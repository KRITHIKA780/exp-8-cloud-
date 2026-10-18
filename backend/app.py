from pathlib import Path
from flask import Flask, jsonify, redirect, send_from_directory
try:
    from .db import init_db
    from .routes.auth import auth_bp
    from .routes.items import items_bp
    from .routes.claims import claims_bp
    from .routes.admin import admin_bp
except ImportError:
    from db import init_db
    from routes.auth import auth_bp
    from routes.items import items_bp
    from routes.claims import claims_bp
    from routes.admin import admin_bp

FRONTEND_FOLDER = Path(__file__).resolve().parent.parent / "frontend"
PROJECT_FOLDER = FRONTEND_FOLDER.parent
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = Path(__file__).with_name("uploads")
app.config["UPLOAD_FOLDER"].mkdir(exist_ok=True)

init_db()
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(items_bp, url_prefix="/api/items")
app.register_blueprint(claims_bp, url_prefix="/api/claims")
app.register_blueprint(admin_bp, url_prefix="/api/admin")


@app.get("/")
def frontend_home():
    return redirect("/frontend/index.html")


@app.get("/frontend/<path:filename>")
def frontend_file(filename):
    return send_from_directory(FRONTEND_FOLDER, filename)


@app.get("/css/<path:filename>")
def css_file(filename):
    return send_from_directory(PROJECT_FOLDER / "css", filename)


@app.get("/js/<path:filename>")
def javascript_file(filename):
    return send_from_directory(PROJECT_FOLDER / "js", filename)


@app.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Id"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
    return response


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "lost-found-system"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
