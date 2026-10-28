from __future__ import annotations

import json
import os
import sqlite3
import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from datetime import date, timedelta
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from bnpl_cashflow.api.profiles import CardNotFound, PlanCreate, ProfileConflict, ProfileNotFound, ProfileStore, validate_document
from bnpl_cashflow.input import InputValidationError
from bnpl_cashflow.application.services import resolve_upcoming_card_dates, resolve_card_statement_dates
from bnpl_cashflow.application.plan_overview import build_plan_overview
from bnpl_cashflow.application.projection_view import build_projection
from bnpl_cashflow.api.profiles import PlanNotFound
from bnpl_cashflow.api.sessions import DemoSessions

MAX_IMPORT_BYTES = 1024 * 1024


async def read_json(request: Request) -> object:
    if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
        raise HTTPException(415, "Send a JSON document.")
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > MAX_IMPORT_BYTES:
            raise HTTPException(413, "Profile files must be no larger than 1 MiB.")
    try:
        return json.loads(data.decode("utf-8-sig"), object_pairs_hook=_unique_keys, parse_constant=_invalid_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise HTTPException(422, "The file must contain valid JSON with unique keys and finite numbers.") from None


def _unique_keys(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError("Non-standard JSON number")


def create_app(database_path: Path | None = None, today_provider: Callable[[], date] = date.today,
               *, demo: bool | None = None, allowed_origins: list[str] | None = None,
               sessions: DemoSessions | None = None) -> FastAPI:
    demo = os.environ.get("DUEMAP_DEMO", "").lower() == "true" if demo is None else demo
    demo_sessions = sessions or DemoSessions()

    @asynccontextmanager
    async def lifespan(app):
        async def cleanup():
            while True:
                await asyncio.sleep(60)
                demo_sessions.expire()
        task = asyncio.create_task(cleanup()) if demo else None
        try:
            yield
        finally:
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            demo_sessions.close()

    app = FastAPI(title="DueMap API", lifespan=lifespan)
    local_store = ProfileStore(database_path or Path(os.environ.get("BNPL_PROFILE_DB", ".local-data/profiles.sqlite3")))
    origins = allowed_origins if allowed_origins is not None else [
        origin.strip() for origin in os.environ.get("DUEMAP_ALLOWED_ORIGINS", "").split(",") if origin.strip()
    ]
    if demo and not origins:
        raise ValueError("Set DUEMAP_ALLOWED_ORIGINS to the frontend origin for the public demo.")
    app.add_middleware(CORSMiddleware, allow_origins=origins,
                       allow_methods=["GET", "POST", "PATCH", "DELETE"],
                       allow_headers=["Content-Type", "X-DueMap-Session"])

    @app.middleware("http")
    async def private_responses(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def get_store(request: Request):
        if demo:
            with demo_sessions.use(request.headers.get("X-DueMap-Session")) as store:
                yield store
        else:
            yield local_store

    if demo:
        @app.post("/api/session", status_code=201)
        def create_session():
            return {"token": demo_sessions.create(), "expires_after_idle_seconds": demo_sessions.ttl_seconds}

    def card_view(card: dict, as_of_date: date) -> dict:
        next_close, next_due = resolve_upcoming_card_dates(
            card["statement_end_day"], card["payment_due_day"], as_of_date,
        )
        latest_close, latest_due, _, upcoming_due = resolve_card_statement_dates(
            card["statement_end_day"], card["payment_due_day"], as_of_date,
        )
        if card.get("upcoming_statement_close_date"):
            # Keep the original persisted field names compatible with saved cards.
            # User-entered dates describe the latest statement, not a forecast.
            latest_close = date.fromisoformat(card["upcoming_statement_close_date"])
            latest_due = date.fromisoformat(card["upcoming_statement_due_date"])
            _, _, next_close, upcoming_due = resolve_card_statement_dates(
                card["statement_end_day"], card["payment_due_day"],
                latest_close + timedelta(days=1),
            )
        return {**card, "as_of_date": as_of_date.isoformat(),
                "latest_statement_close_date": latest_close.isoformat(),
                "latest_statement_due_date": latest_due.isoformat(),
                "next_statement_due_date": upcoming_due.isoformat(),
                "next_statement_close_date": next_close.isoformat(),
                "next_payment_due_date": next_due.isoformat()}

    @app.exception_handler(ProfileNotFound)
    async def missing_profile_handler(request: Request, exc: ProfileNotFound):
        return JSONResponse(status_code=404, content={"detail": "This profile no longer exists. Return home to choose a saved profile."})

    @app.exception_handler(CardNotFound)
    async def missing_card_handler(request: Request, exc: CardNotFound):
        return JSONResponse(status_code=404, content={"detail": "This card does not exist in the selected profile."})

    @app.exception_handler(ProfileConflict)
    async def conflict_handler(request: Request, exc: ProfileConflict):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(InputValidationError)
    async def input_handler(request: Request, exc: InputValidationError):
        return JSONResponse(status_code=422, content={"detail": "Profile validation failed.",
            "issues": [{"path": issue.path, "message": issue.message} for issue in exc.issues]})

    @app.exception_handler(ValidationError)
    async def schema_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": "The request does not match the expected format.",
            "issues": [{"path": ".".join(map(str, issue["loc"])), "message": issue["msg"]} for issue in exc.errors()]})

    @app.exception_handler(ValueError)
    async def value_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(sqlite3.Error)
    async def storage_handler(request: Request, exc: sqlite3.Error):
        return JSONResponse(status_code=503, content={"detail": "Local profile storage is unavailable. Please try again."})

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.exception_handler(PlanNotFound)
    async def missing_plan_handler(request: Request, exc: PlanNotFound):
        return JSONResponse(status_code=404, content={"detail": "This payment plan is unavailable in this profile."})

    @app.get("/api/profiles")
    def profiles(store: ProfileStore = Depends(get_store)):
        return store.list()

    @app.post("/api/profiles", status_code=201)
    async def create_profile(request: Request, store: ProfileStore = Depends(get_store)):
        body = await read_json(request)
        if not isinstance(body, dict) or set(body) != {"name"} or not isinstance(body["name"], str):
            raise HTTPException(422, "Provide a profile name.")
        return store.create(body["name"])

    @app.post("/api/profiles/import", status_code=201)
    async def import_profile(request: Request, store: ProfileStore = Depends(get_store)):
        document = validate_document(await read_json(request))
        return store.insert(document)

    @app.get("/api/profiles/{profile_id}/cards")
    def list_cards(profile_id: str, store: ProfileStore = Depends(get_store)):
        as_of_date = today_provider()
        return [card_view(card, as_of_date) for card in store.cards(profile_id)]

    @app.post("/api/profiles/{profile_id}/cards", status_code=201)
    async def create_card(profile_id: str, request: Request, store: ProfileStore = Depends(get_store)):
        as_of_date = today_provider()
        return card_view(store.add_card(profile_id, await read_json(request)), as_of_date)

    @app.patch("/api/profiles/{profile_id}/cards/{card_id}")
    async def update_card(profile_id: str, card_id: str, request: Request, store: ProfileStore = Depends(get_store)):
        as_of_date = today_provider()
        return card_view(store.update_card(profile_id, card_id, await read_json(request)), as_of_date)

    @app.get("/api/profiles/{profile_id}/plans")
    def list_plans(profile_id: str, store: ProfileStore = Depends(get_store)):
        return store.plans(profile_id)

    @app.get("/api/profiles/{profile_id}/plans/overview")
    def plan_overview(profile_id: str, store: ProfileStore = Depends(get_store)):
        return build_plan_overview(store.export(profile_id))

    @app.get("/api/profiles/{profile_id}/projection")
    def projection(profile_id: str, start: date | None = None,
                   months: int = Query(default=6, ge=1, le=24),
                   card_id: str | None = None, currency: str | None = None,
                   store: ProfileStore = Depends(get_store)):
        return build_projection(store.export(profile_id), today_provider(), start, months, card_id, currency)

    @app.patch("/api/profiles/{profile_id}/plans/{plan_id}")
    async def update_plan(profile_id: str, plan_id: str, request: Request, store: ProfileStore = Depends(get_store)):
        return store.update_plan(profile_id, plan_id, PlanCreate.model_validate(await read_json(request)).model_dump(exclude_unset=True))

    @app.delete("/api/profiles/{profile_id}/plans/{plan_id}")
    def delete_plan(profile_id: str, plan_id: str, store: ProfileStore = Depends(get_store)):
        store.delete_plan(profile_id, plan_id)
        return {"deleted": True}

    @app.post("/api/profiles/{profile_id}/plans", status_code=201, openapi_extra={
        "requestBody": {"required": True, "content": {"application/json": {"schema": PlanCreate.model_json_schema()}}}})
    async def create_plan(profile_id: str, request: Request, store: ProfileStore = Depends(get_store)):
        return store.add_plan(profile_id, PlanCreate.model_validate(await read_json(request)).model_dump())

    @app.get("/api/profiles/{profile_id}/export")
    def export_profile(profile_id: str, store: ProfileStore = Depends(get_store)):
        return JSONResponse(store.export(profile_id), headers={"Content-Disposition": 'attachment; filename="duemap-profile.json"'})

    return app


app = create_app()
