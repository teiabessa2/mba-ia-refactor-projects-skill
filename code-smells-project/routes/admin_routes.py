from flask import Blueprint

from auth import require_role
from controllers import admin_controller

admin_bp = Blueprint("admin", __name__)

# /admin/query (arbitrary SQL execution, catalog C5) was removed rather than
# gated — see refactoring-playbook.md #5. Reporting needs go through the
# purpose-built /relatorios/vendas endpoint instead.
admin_bp.add_url_rule(
    "/admin/reset-db", "reset_database",
    require_role("admin")(admin_controller.reset_database), methods=["POST"],
)
