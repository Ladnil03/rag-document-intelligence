"""Top-level uvicorn entry shim.

``uvicorn main:app`` from ``backend/`` (per the Dockerfile and README)
and ``from main import app`` (per the test suite) both resolve to
``app.main:app``.
"""

from app.main import app  # noqa: F401
