from functools import wraps

from flask import request, jsonify, g
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

import config

_serializer = URLSafeTimedSerializer(config.SECRET_KEY, salt="auth-token")


def generate_token(user_id):
    return _serializer.dumps({"user_id": user_id})


def verify_token(token):
    """Returns the user_id encoded in the token, or None if it's missing,
    expired, or has an invalid signature."""
    try:
        data = _serializer.loads(token, max_age=config.TOKEN_EXPIRY_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("user_id")


def _extract_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[len("Bearer "):]
    return None


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        from models.user import User

        token = _extract_token()
        if not token:
            return jsonify({"error": "Autenticação necessária"}), 401

        user_id = verify_token(token)
        if not user_id:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        user = User.query.get(user_id)
        if not user or not user.active:
            return jsonify({"error": "Usuário inválido ou inativo"}), 401

        g.current_user = user
        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not g.current_user.is_admin():
            return jsonify({"error": "Permissão de administrador necessária"}), 403
        return f(*args, **kwargs)

    return wrapper
