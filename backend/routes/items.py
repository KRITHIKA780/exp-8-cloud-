from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename
try:
    from ..db import get_db
except ImportError:
    from db import get_db

items_bp = Blueprint("items", __name__)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}


@items_bp.get("")
def list_items():
    query = (request.args.get("q") or "").strip()
    report_type = (request.args.get("type") or "").strip()
    status = (request.args.get("status") or "").strip()
    sql = """
        SELECT items.*, users.name AS reporter
        FROM items
        JOIN users ON users.id = items.user_id
        WHERE 1 = 1
    """
    params = []
    if query:
        sql += " AND (items.title LIKE ? OR items.location LIKE ? OR items.description LIKE ? OR items.category LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like, like])
    if report_type in {"lost", "found"}:
        sql += " AND items.report_type = ?"
        params.append(report_type)
    if status in {"open", "found", "resolved"}:
        sql += " AND items.status = ?"
        params.append(status)
    sql += " ORDER BY items.created_at DESC"
    connection = get_db()
    rows = connection.execute(sql, params).fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])


@items_bp.post("")
def create_item():
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    required = ["title", "description", "category", "location", "report_type", "user_id"]
    if any(not data.get(field) for field in required):
        return jsonify({"error": "All item fields are required"}), 400
    if data["report_type"] not in {"lost", "found"}:
        return jsonify({"error": "Report type must be lost or found"}), 400
    image_url = data.get("image")
    image = request.files.get("image")
    if image and image.filename:
        extension = Path(image.filename).suffix.lower().lstrip(".")
        if extension not in ALLOWED_EXTENSIONS:
            return jsonify({"error": "Only JPG, PNG, GIF or WEBP images are allowed"}), 400
        filename = f"{uuid4().hex}.{extension}"
        image.save(current_app.config["UPLOAD_FOLDER"] / secure_filename(filename))
        image_url = f"/uploads/{filename}"
    connection = get_db()
    cursor = connection.execute(
        "INSERT INTO items (title, description, category, location, report_type, image, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data["title"], data["description"], data["category"], data["location"], data["report_type"], image_url, data["user_id"]),
    )
    if data["report_type"] == "lost":
        connection.execute(
            "INSERT INTO notifications (item_id, message) VALUES (?, ?)",
            (
                cursor.lastrowid,
                f"New lost item: {data['title']} (missed at {data['location']})",
            ),
        )
        connection.execute(
            """
            INSERT INTO notifications (item_id, recipient_id, message)
            SELECT ?, users.id, ?
            FROM users
            WHERE users.role = 'student' AND users.id != ?
            """,
            (
                cursor.lastrowid,
                f"A new lost item was reported: {data['title']} at {data['location']}",
                data["user_id"],
            ),
        )
    connection.commit()
    connection.close()
    return jsonify({"id": cursor.lastrowid, "message": "Report created. Admin has been notified." if data["report_type"] == "lost" else "Report created"}), 201


@items_bp.patch("/<int:item_id>")
def update_item(item_id):
    data = request.get_json() or {}
    status = data.get("status")
    if status not in {"open", "found", "resolved"}:
        return jsonify({"error": "Status must be open, found or resolved"}), 400
    connection = get_db()
    item = connection.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        connection.close()
        return jsonify({"error": "Item not found"}), 404
    connection.execute("UPDATE items SET status = ? WHERE id = ?", (status, item_id))
    if status == "found":
        found_by_name = (data.get("found_by_name") or "a student").strip()
        connection.execute(
            "INSERT INTO notifications (item_id, message) VALUES (?, ?)",
            (item_id, f"Your item was found by {found_by_name}: {item['title']}"),
        )
        connection.execute(
            """
            INSERT INTO notifications (item_id, recipient_id, message)
            SELECT ?, users.id, ?
            FROM users
            WHERE users.role = 'student' AND users.id != ?
            """,
            (
                item_id,
                f"Found update: {item['title']} was found by {found_by_name} at {item['location']}",
                item["user_id"],
            ),
        )
    connection.commit()
    connection.close()
    return jsonify({"message": f"Item marked as found by {found_by_name}" if status == "found" else "Item updated"})
