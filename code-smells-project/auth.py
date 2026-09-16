from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import jsonify, request

import config

ALGORITHM = "HS256"


def gerar_token(usuario_id, tipo):
    payload = {
        "usuario_id": usuario_id,
        "tipo": tipo,
        "exp": datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXP_HOURS),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=ALGORITHM)


def _extrair_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header[len("Bearer "):]


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = _extrair_token()
        if not token:
            return jsonify({"erro": "Token de autenticação ausente"}), 401
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido"}), 401
        request.usuario_atual = {"id": payload["usuario_id"], "tipo": payload["tipo"]}
        return f(*args, **kwargs)

    return wrapper


def require_role(role):
    def decorator(f):
        @wraps(f)
        def role_checked(*args, **kwargs):
            if request.usuario_atual["tipo"] != role:
                return jsonify({"erro": "Permissão negada"}), 403
            return f(*args, **kwargs)

        return require_auth(role_checked)

    return decorator
