"""Vercel serverless entrypoint (@vercel/python). Exposes the Flask app as
`app` - the runtime auto-detects and serves it as a WSGI callable."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

app = create_app()
