from models import pedidos_model


def gerar_relatorio_vendas():
    stats = pedidos_model.estatisticas_vendas()
    faturamento = stats["faturamento_bruto"]
    total_pedidos = stats["total_pedidos"]

    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": stats["pedidos_pendentes"],
        "pedidos_aprovados": stats["pedidos_aprovados"],
        "pedidos_cancelados": stats["pedidos_cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
