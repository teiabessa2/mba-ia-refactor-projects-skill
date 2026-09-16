from flask import jsonify

from services import relatorios_service


def relatorio_vendas():
    relatorio = relatorios_service.gerar_relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
