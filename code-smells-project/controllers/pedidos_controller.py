from flask import jsonify, request

from services import pedidos_service
from services.pedidos_service import PedidoError


def criar_pedido():
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    itens = dados.get("itens", [])
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    # The order always belongs to whoever authenticated the request — the
    # caller can no longer place an order "as" an arbitrary usuario_id.
    usuario_id = request.usuario_atual["id"]

    try:
        resultado = pedidos_service.criar_pedido(usuario_id, itens)
    except PedidoError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 400

    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }), 201


def listar_pedidos_usuario(usuario_id):
    usuario_atual = request.usuario_atual
    if usuario_atual["tipo"] != "admin" and usuario_atual["id"] != usuario_id:
        return jsonify({"erro": "Permissão negada"}), 403
    pedidos = pedidos_service.listar_pedidos_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    pedidos = pedidos_service.listar_todos_pedidos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status", "")
    if novo_status not in ["pendente", "aprovado", "enviado", "entregue", "cancelado"]:
        return jsonify({"erro": "Status inválido"}), 400

    pedidos_service.atualizar_status_pedido(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
