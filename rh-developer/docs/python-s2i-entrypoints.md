---
title: Python S2I Entry Point Requirements
category: containers
sources:
  - title: UBI Python S2I Builder
    url: https://github.com/sclorg/s2i-python-container
    sections: Run script logic, APP_MODULE configuration
    date_accessed: 2026-02-08
  - title: Red Hat Python S2I Documentation
    url: https://catalog.redhat.com/software/containers/ubi9/python-311
    sections: Environment variables, Startup behavior
    date_accessed: 2026-02-08
---

# Python S2I Entry Point Requirements

The UBI Python S2I builder has specific startup logic that must be understood to avoid deployment failures.

## How the S2I Python Run Script Works

The S2I Python builder uses this startup logic (in order):

1. If `app.sh` exists → Execute it directly
2. If `gunicorn` is installed AND `APP_MODULE` is set → Start with gunicorn
3. If `app.py` exists → Run with Python directly
4. Otherwise → **ERROR: No start command found**

## Entry Point Configuration Matrix

| Entry Point File | gunicorn in requirements | Configuration Needed | Result |
|------------------|--------------------------|----------------------|--------|
| `app.py` | No | None | Works (Python direct) |
| `app.py` | Yes | None (optional APP_MODULE) | Works |
| `main.py` | **No** | - | **FAILS** |
| `main.py` | Yes | `APP_MODULE=main:app` | Works |
| `wsgi.py` | Yes | `APP_MODULE=wsgi` or `APP_MODULE=wsgi:application` | Works |
| Custom file | Yes | `APP_MODULE=[module]:[variable]` | Works |

## APP_MODULE Format

- **Format:** `[python_module]:[flask_app_variable]`
- **Example:** `main:app` → imports `app` from `main.py`
- **Requires:** `gunicorn` in `requirements.txt`

### Common Patterns

| File | Typical APP_MODULE |
|------|-------------------|
| `main.py` with `app = Flask(__name__)` | `main:app` |
| `main.py` with `application = Flask(__name__)` | `main:application` |
| `wsgi.py` with `application` | `wsgi:application` or just `wsgi` |
| `src/app.py` with `app` | `src.app:app` |

## Alternative: APP_FILE

- Set `APP_FILE=main.py` to run with Python directly (development mode)
- **Not recommended for production** (no WSGI server, no worker management)
- Use only if gunicorn is not an option

## Critical Warning

**If the entry point is NOT `app.py` and `gunicorn` is NOT installed:**
- The S2I build will succeed (dependencies install)
- The container will **fail to start** with "No start command found"
- This is a **runtime failure**, not a build failure

**Always verify:**
1. Entry point file name
2. `gunicorn` in requirements.txt
3. `APP_MODULE` environment variable in BuildConfig
