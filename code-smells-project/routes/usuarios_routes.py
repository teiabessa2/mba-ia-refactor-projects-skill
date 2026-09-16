from flask import Blueprint

from auth import require_role
from controllers import usuarios_controller

usuarios_bp = Blueprint("usuarios", __name__)

usuarios_bp.add_url_rule(
    "/usuarios", "listar_usuarios",
    require_role("admin")(usuarios_controller.listar_usuarios), methods=["GET"],
)
usuarios_bp.add_url_rule(
    "/usuarios/<int:id>", "buscar_usuario",
    require_role("admin")(usuarios_controller.buscar_usuario), methods=["GET"],
)
usuarios_bp.add_url_rule("/usuarios", "criar_usuario", usuarios_controller.criar_usuario, methods=["POST"])
usuarios_bp.add_url_rule("/login", "login", usuarios_controller.login, methods=["POST"])
