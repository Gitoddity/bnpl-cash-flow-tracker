from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from datetime import date
from typing import Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from bnpl_cashflow.api.profiles import CardNotFound, ProfileConflict, ProfileNotFound, ProfileStore, validate_document
from bnpl_cashflow.input import InputValidationError
from bnpl_cashflow.application.services import resolve_upcoming_card_dates

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


def create_app(database_path: Path | None = None, today_provider: Callable[[], date] = date.today) -> FastAPI:
    app = FastAPI(title="BNPL Cash Flow Tracker local API")
    store = ProfileStore(database_path or Path(os.environ.get("BNPL_PROFILE_DB", ".local-data/profiles.sqlite3")))

    def card_view(card: dict, as_of_date: date) -> dict:
        next_close, next_due = resolve_upcoming_card_dates(
            card["statement_end_day"], card["payment_due_day"], as_of_date,
        )
        return {**card, "as_of_date": as_of_date.isoformat(),
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
        return JSONResponse(status_code=422, content={"detail": "The profile document does not match the version 1 format.",
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

    @app.get("/api/profiles")
    def profiles():
        return store.list()

    @app.post("/api/profiles", status_code=201)
    async def create_profile(request: Request):
        body = await read_json(request)
        if not isinstance(body, dict) or set(body) != {"name"} or not isinstance(body["name"], str):
            raise HTTPException(422, "Provide a profile name.")
        return store.create(body["name"])

    @app.post("/api/profiles/import", status_code=201)
    async def import_profile(request: Request):
        document = validate_document(await read_json(request))
        return store.insert(document)

    @app.get("/api/profiles/{profile_id}/cards")
    def list_cards(profile_id: str):
        as_of_date = today_provider()
        return [card_view(card, as_of_date) for card in store.cards(profile_id)]

    @app.post("/api/profiles/{profile_id}/cards", status_code=201)
    async def create_card(profile_id: str, request: Request):
        as_of_date = today_provider()
        return card_view(store.add_card(profile_id, await read_json(request)), as_of_date)

    @app.patch("/api/profiles/{profile_id}/cards/{card_id}")
    async def update_card(profile_id: str, card_id: str, request: Request):
        as_of_date = today_provider()
        return card_view(store.update_card(profile_id, card_id, await read_json(request)), as_of_date)

    return app


app = create_app()
