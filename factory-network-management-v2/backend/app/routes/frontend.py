from pathlib import Path
from flask import Blueprint, send_from_directory

frontend = Blueprint("frontend", __name__)
BUILD = Path(__file__).resolve().parents[3] / "frontend" / "dist"


@frontend.get("/")
@frontend.get("/passport/<uid>")
def app_page(uid=None):
    if not (BUILD / "index.html").exists():
        return "Frontend build unavailable. Build the frontend or use the Vite development server.", 503
    return send_from_directory(BUILD, "index.html", max_age=0)


@frontend.get("/assets/<path:filename>")
def app_asset(filename):
    return send_from_directory(BUILD / "assets", filename)
