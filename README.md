# After Defects - An After Effects Project File (.pjf) & Animation Preset (.ffx) Downgrader

A web tool to downgrade After Effects project files (`.aep`) and effect presets (`.ffx`) from newer versions to older ones.

## How it works

After Effects files use the **RIFX binary format**. The version of AE that created the file is stored as a 16-bit integer inside a `tdsn` chunk. This tool:

1. Parses the RIFX structure to find and read that version integer
2. Maps it to an AE release name (e.g. `3520` → *After Effects 2024*)
3. Lets you pick a lower target version
4. Patches the version bytes in place and returns the modified file

> ⚠️ **Limitation**: This is a version-byte patch, not a full re-encode. Projects that use effects, expressions, or features not available in the target version will still fail to open. Always test the downgraded file before using it in production.

---

## Quick start (Docker)

```bash
git clone <repo>
cd ae-downgrader
docker compose up --build
```

Open **http://localhost:3000** in your browser.

---

## Development (without Docker)

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` → `http://localhost:8000`, so both servers work together out of the box.

---

## Supported versions

| Version int | After Effects release |
|---|---|
| 3584 | After Effects 2025 |
| 3520 | After Effects 2024 (24.x) |
| 3456 | After Effects 2023 (23.x) |
| 3392 | After Effects 2022 (22.x) |
| 3328 | After Effects 2021 (18.x) |
| 3264 | After Effects 2020 (17.x) |
| 3200 | After Effects CC 2019 (16.x) |
| 3136 | After Effects CC 2018 (15.x) |
| 3072 | After Effects CC 2017 (14.x) |
| 3008 | After Effects CC 2015.3 |
| 2944 | After Effects CC 2015 |
| 2880 | After Effects CC 2014 |
| 2816 | After Effects CC (12.x) |
| 2752 | After Effects CS6 |
| 2688 | After Effects CS5.5 |
| 2624 | After Effects CS5 |

---

## API

### `POST /analyze`
- **Body**: `multipart/form-data` with `file` field (`.aep` or `.ffx`)
- **Returns**: JSON with `source` version info and `targets` array

### `POST /downgrade`
- **Body**: `multipart/form-data` with `file` and `target_version_int` fields
- **Returns**: patched binary file as download

### `GET /health`
- Returns `{"status": "ok"}` — used by Docker healthcheck

---

## Project structure

```
ae-downgrader/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py        ← FastAPI app + endpoints
│   ├── parser.py      ← RIFX binary parser
│   ├── patcher.py     ← Version byte patcher
│   └── versions.py    ← AE version registry
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── App.css
        └── index.css
```
