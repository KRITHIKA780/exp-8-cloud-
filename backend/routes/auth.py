from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
try:
    from ..db import get_db
except ImportError:
    from db import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not all([name, email, password]):
        return jsonify({"error": "Name, email and password are required"}), 400
    role = data.get("role", "student")
    if role not in {"student", "admin"}:
        return jsonify({"error": "Choose a valid account type"}), 400
    connection = get_db()
    try:
        cursor = connection.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name.strip(), email.lower().strip(), generate_password_hash(password), role),
        )
        if role == "student":
            connection.execute(
                "INSERT INTO login_events (user_id, role, event_type) VALUES (?, ?, 'registration')",
                (cursor.lastrowid, role),
            )
        connection.commit()
        return jsonify({"id": cursor.lastrowid, "name": name.strip(), "email": email.lower().strip(), "role": role}), 201
    except Exception:
        return jsonify({"error": "Email is already registered"}), 409
    finally:
        connection.close()


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    connection = get_db()
    user = connection.execute("SELECT * FROM users WHERE email = ?", (data.get("email", "").lower(),)).fetchone()
    connection.close()
    if not user or not check_password_hash(user["password"], data.get("password", "")):
        return jsonify({"error": "Invalid email or password"}), 401
    requested_role = data.get("role", "student")
    actual_role = "student" if user["role"] == "user" else user["role"]
    if requested_role not in {"student", "admin"} or actual_role != requested_role:
        return jsonify({"error": "Choose the correct account type for this login"}), 403
    connection = get_db()
    connection.execute(
        "INSERT INTO login_events (user_id, role, event_type) VALUES (?, ?, 'login')",
        (user["id"], actual_role),
    )
    connection.commit()
    connection.close()
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"], "role": actual_role})


@auth_bp.get("/notifications/<int:user_id>")
def user_notifications(user_id):
    connection = get_db()
    rows = connection.execute(
        """
        SELECT notifications.*, items.title, items.location, items.status AS item_status
        FROM notifications
        JOIN items ON items.id = notifications.item_id
        WHERE items.user_id = ? OR notifications.recipient_id = ?
        ORDER BY notifications.created_at DESC
        LIMIT 20
        """,
        (user_id, user_id),
    ).fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])
