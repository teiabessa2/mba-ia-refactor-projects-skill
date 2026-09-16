from flask import Blueprint

from auth import require_role
from controllers import relatorios_controller

relatorios_bp = Blueprint("relatorios", __name__)

relatorios_bp.add_url_rule(
    "/relatorios/vendas", "relatorio_vendas",
    require_role("admin")(relatorios_controller.relatorio_vendas), methods=["GET"],
)
