from models import pedidos_model, produtos_model
from services import notificacoes_service


class PedidoError(Exception):
    """Raised for business-rule violations while placing an order."""


def criar_pedido(usuario_id, itens_solicitados):
    produto_ids = [item["produto_id"] for item in itens_solicitados]
    produtos = produtos_model.get_produtos_por_ids(produto_ids)

    total = 0
    itens = []
    for item in itens_solicitados:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise PedidoError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise PedidoError(f"Estoque insuficiente para {produto['nome']}")
        total += produto["preco"] * item["quantidade"]
        itens.append({
            "produto_id": item["produto_id"],
            "quantidade": item["quantidade"],
            "preco_unitario": produto["preco"],
        })

    pedido_id = pedidos_model.criar_pedido(usuario_id, total, itens)
    notificacoes_service.notificar_novo_pedido(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_pedidos_usuario(usuario_id):
    return pedidos_model.get_pedidos_usuario(usuario_id)


def listar_todos_pedidos():
    return pedidos_model.get_todos_pedidos()


def atualizar_status_pedido(pedido_id, novo_status):
    pedidos_model.atualizar_status_pedido(pedido_id, novo_status)
    notificacoes_service.notificar_mudanca_status(pedido_id, novo_status)
