# API Application

The FastAPI application exposes the synchronous, non-persistent English Rhymes analyzer at
`POST /v1/rhymes/analyze`. HTTP schemas are separate Pydantic models; analytical behavior remains in
`packages/analysis`.

From Python 3.12:

```bash
cd apps/api
python3 -m pip install -r requirements.txt
uvicorn secondear_api.main:app --reload --port 8000
```

The request accepts `lyrics`, `language_profile`, `primary_tag`, pronunciation overrides, and an
optional provenance-only `source_reference`. It does not fetch that reference. Lyrics are not
written to storage or application logs.

Set `SECONDEAR_WEB_ORIGINS` to a comma-separated origin list when the web app is not served from the
default local origins.
