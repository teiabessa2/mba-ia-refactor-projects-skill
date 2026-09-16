from flask import Blueprint

from auth import require_auth, require_role
from controllers import pedidos_controller

pedidos_bp = Blueprint("pedidos", __name__)

pedidos_bp.add_url_rule(
    "/pedidos", "criar_pedido",
    require_auth(pedidos_controller.criar_pedido), methods=["POST"],
)
pedidos_bp.add_url_rule(
    "/pedidos", "listar_todos_pedidos",
    require_role("admin")(pedidos_controller.listar_todos_pedidos), methods=["GET"],
)
pedidos_bp.add_url_rule(
    "/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
    require_auth(pedidos_controller.listar_pedidos_usuario), methods=["GET"],
)
pedidos_bp.add_url_rule(
    "/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
    require_role("admin")(pedidos_controller.atualizar_status_pedido), methods=["PUT"],
)
