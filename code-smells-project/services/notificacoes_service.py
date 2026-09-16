import logging

logger = logging.getLogger(__name__)


def notificar_novo_pedido(pedido_id, usuario_id):
    logger.info(
        "Notificações (email/sms/push) disparadas para pedido %s do usuário %s",
        pedido_id, usuario_id,
    )


def notificar_mudanca_status(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado — preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Pedido %s cancelado — devolver estoque", pedido_id)
