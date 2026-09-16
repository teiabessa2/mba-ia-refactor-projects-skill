from flask import Blueprint

from auth import require_role
from controllers import produtos_controller

produtos_bp = Blueprint("produtos", __name__)

produtos_bp.add_url_rule("/produtos", "listar_produtos", produtos_controller.listar_produtos, methods=["GET"])
produtos_bp.add_url_rule("/produtos/busca", "buscar_produtos", produtos_controller.buscar_produtos, methods=["GET"])
produtos_bp.add_url_rule("/produtos/<int:id>", "buscar_produto", produtos_controller.buscar_produto, methods=["GET"])

produtos_bp.add_url_rule(
    "/produtos", "criar_produto",
    require_role("admin")(produtos_controller.criar_produto), methods=["POST"],
)
produtos_bp.add_url_rule(
    "/produtos/<int:id>", "atualizar_produto",
    require_role("admin")(produtos_controller.atualizar_produto), methods=["PUT"],
)
produtos_bp.add_url_rule(
    "/produtos/<int:id>", "deletar_produto",
    require_role("admin")(produtos_controller.deletar_produto), methods=["DELETE"],
)
