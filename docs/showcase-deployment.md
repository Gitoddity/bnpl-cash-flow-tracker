# Free showcase: GitHub Pages and Render

The React frontend can be published on GitHub Pages. The Python API runs as a
free Render web service, using the root `render.yaml` Blueprint. No permanent
database or paid disk is required. The Windows BAT launcher remains for local use.

## Visitor data

Hosted mode (`DUEMAP_DEMO=true`) creates isolated, random-token sessions. Profile
inputs live only in a bounded in-memory SQLite database per session. They never
use the local application's `.local-data/profiles.sqlite3` file. Sessions expire
after 30 minutes without activity; a background task releases expired memory at
least every minute. Restarts and Render sleeping discard all sessions sooner.
There is a limit of 32 simultaneous sessions and approximately 4 MiB per session.

The browser keeps only its random session token in sessionStorage, not profile
data. Profile requests send that token in a header, including downloads; it is
never placed in links or query strings. The API marks responses `no-store`.
Visitors must use Export Profile before leaving, and import their downloaded
version 1 JSON to resume. An expired session returns a clear message and resets
the frontend to profile selection. Downloaded JSON is not encrypted.

Local mode stays persistent and does not require sessions. Set the demo flag only
on Render and in hosted frontend builds, not in the local BAT environment.

## 1. Deploy the API

1. Sign into Render, select **New > Blueprint**, and connect this source repository.
2. Select the branch containing these deployment changes and its `render.yaml`.
3. Confirm the service uses the **Free** compute plan and has no attached disk or
   paid database. The Blueprint installs only API dependencies, not Streamlit.
4. Keep `DUEMAP_DEMO=true`, one Uvicorn worker, and `TZ=America/Toronto`.
5. Set `DUEMAP_ALLOWED_ORIGINS` to the frontend origin, for example
   `https://gitoddity.github.io` (no repository path or trailing slash).
6. Deploy, then copy the actual Render origin shown in the dashboard. Service
   names can receive a suffix; do not assume the URL from the configured name.
7. Confirm `https://YOUR-SERVICE.onrender.com/api/health` returns `{"status":"ok"}`.

Free Render services sleep after 15 minutes without inbound traffic; the first
request after sleep can take about a minute. Frontend errors explain this and
allow retrying. No automated requests keep the API artificially awake.

## 2. Publish the frontend

The source repository is private. Free GitHub Pages normally requires a public
repository. Keep the source private unless you explicitly choose otherwise:

- If your GitHub plan supports Pages from private repositories, use the included
  `.github/workflows/pages.yml` in this source repository.
- Otherwise create a separate public repository, such as `duemap-demo`, containing
  only the built frontend, provider attribution files and `.nojekyll`. Publish
  its `main` branch root using Pages. Do not copy `.local-data`, Python source,
  profile downloads, environment files, or credentials into that repository.

For the included Actions workflow, enable **Settings > Pages > GitHub Actions**,
set the repository Actions variable `DUEMAP_API_URL` to the actual HTTPS Render
origin, and run **Deploy DueMap showcase**. Workflow dispatch also accepts the
origin directly. Push deployment runs on `main` after the origin is configured.
For a deployment from another branch, run the workflow manually on that branch.

For a separate public frontend repository, build from `frontend`:

```powershell
$env:VITE_DEMO_MODE = 'true'
$env:VITE_API_BASE_URL = 'https://YOUR-SERVICE.onrender.com'
npm.cmd ci
npm.cmd test
npm.cmd run build
```

Publish the contents of `frontend/dist`, not the dist folder itself. Add an empty
`.nojekyll` at the publishing root. Vite uses relative asset paths, provider logos
respect `BASE_URL`, and hash navigation works under `/duemap-demo/` without SPA
rewrite rules. The frontend API URL is public configuration, not a secret.

## Verification

- Open the public frontend; confirm all fonts and provider logos load.
- Import `examples/profile-v1.json`, add/edit inputs, and open Projection.
- Export Profile; verify the downloaded JSON imports into a fresh session.
- In an incognito browser, confirm the first browser's profiles are not visible.
- Refresh to confirm the active tab resumes its unexpired session.
- Restart the demo API; confirm the frontend explains the ended session and can
  start a fresh one. Import the previously downloaded profile to resume.

References: [Render free limits](https://render.com/docs/free),
[Blueprints](https://render.com/docs/infrastructure-as-code),
[GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).
