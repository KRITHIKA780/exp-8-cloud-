from flask import Blueprint, jsonify, request
try:
    from ..db import get_db
except ImportError:
    from db import get_db

claims_bp = Blueprint("claims", __name__)


@claims_bp.get("/<int:user_id>")
def user_claims(user_id):
    connection = get_db()
    rows = connection.execute(
        "SELECT claims.*, items.title FROM claims JOIN items ON items.id = claims.item_id WHERE claims.claimant_id = ? ORDER BY claims.created_at DESC",
        (user_id,),
    ).fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])


@claims_bp.post("")
def create_claim():
    data = request.get_json() or {}
    if not all(data.get(field) for field in ["item_id", "claimant_id", "message"]):
        return jsonify({"error": "Item, claimant and message are required"}), 400
    connection = get_db()
    cursor = connection.execute(
        "INSERT INTO claims (item_id, claimant_id, message) VALUES (?, ?, ?)",
        (data["item_id"], data["claimant_id"], data["message"]),
    )
    connection.commit()
    connection.close()
    return jsonify({"id": cursor.lastrowid, "message": "Claim submitted"}), 201
