from flask import Blueprint, jsonify, request
try:
    from ..db import get_db
except ImportError:
    from db import get_db

admin_bp = Blueprint("admin", __name__)


def require_admin(connection):
    user = connection.execute("SELECT role FROM users WHERE id = ?", (request.headers.get("X-User-Id"),)).fetchone()
    return user and user["role"] == "admin"


@admin_bp.get("/stats")
def stats():
    connection = get_db()
    if not require_admin(connection):
        connection.close()
        return jsonify({"error": "Admin access required"}), 403
    result = {
        "users": connection.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "lost_items": connection.execute("SELECT COUNT(*) FROM items WHERE report_type = 'lost'").fetchone()[0],
        "found_items": connection.execute("SELECT COUNT(*) FROM items WHERE report_type = 'found' OR status = 'found'").fetchone()[0],
        "still_missing": connection.execute("SELECT COUNT(*) FROM items WHERE report_type = 'lost' AND status = 'open'").fetchone()[0],
        "unread_alerts": connection.execute(
            "SELECT (SELECT COUNT(*) FROM notifications WHERE is_read = 0 AND recipient_id IS NULL) + "
            "(SELECT COUNT(*) FROM login_events WHERE is_read = 0)"
        ).fetchone()[0],
    }
    connection.close()
    return jsonify(result)


@admin_bp.get("/notifications")
def notifications():
    connection = get_db()
    if not require_admin(connection):
        connection.close()
        return jsonify({"error": "Admin access required"}), 403
    rows = connection.execute(
        """
        SELECT notifications.*, items.title, items.location, items.image, items.status, items.report_type
        FROM notifications
        JOIN items ON items.id = notifications.item_id
        WHERE notifications.recipient_id IS NULL
        ORDER BY notifications.created_at DESC
        LIMIT 40
        """
    ).fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])


@admin_bp.patch("/notifications/read")
def mark_notifications_read():
    connection = get_db()
    if not require_admin(connection):
        connection.close()
        return jsonify({"error": "Admin access required"}), 403
    connection.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0 AND recipient_id IS NULL")
    connection.execute("UPDATE login_events SET is_read = 1 WHERE is_read = 0")
    connection.commit()
    connection.close()
    return jsonify({"message": "Notifications marked as read"})


@admin_bp.get("/login-alerts")
def login_alerts():
    connection = get_db()
    if not require_admin(connection):
        connection.close()
        return jsonify({"error": "Admin access required"}), 403
    rows = connection.execute(
        """
        SELECT login_events.*, users.name, users.email
        FROM login_events JOIN users ON users.id = login_events.user_id
        ORDER BY login_events.created_at DESC LIMIT 20
        """
    ).fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])


@admin_bp.get("/claims")
def claims():
    connection = get_db()
    if not require_admin(connection):
        connection.close()
        return jsonify({"error": "Admin access required"}), 403
    rows = connection.execute(
        """
        SELECT claims.*, items.title, users.name AS claimant_name, users.email AS claimant_email
        FROM claims
        JOIN items ON items.id = claims.item_id
        JOIN users ON users.id = claims.claimant_id
        ORDER BY claims.created_at DESC
        """
    ).fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])


@admin_bp.patch("/claims/<int:claim_id>")
def update_claim(claim_id):
    status = (request.get_json() or {}).get("status")
    if status not in {"approved", "rejected"}:
        return jsonify({"error": "Claim status must be approved or rejected"}), 400
    connection = get_db()
    if not require_admin(connection):
        connection.close()
        return jsonify({"error": "Admin access required"}), 403
    claim = connection.execute("SELECT item_id FROM claims WHERE id = ?", (claim_id,)).fetchone()
    if not claim:
        connection.close()
        return jsonify({"error": "Claim not found"}), 404
    connection.execute("UPDATE claims SET status = ? WHERE id = ?", (status, claim_id))
    if status == "approved":
        connection.execute("UPDATE items SET status = 'resolved' WHERE id = ?", (claim["item_id"],))
    connection.commit()
    connection.close()
    return jsonify({"message": f"Claim {status}"})
