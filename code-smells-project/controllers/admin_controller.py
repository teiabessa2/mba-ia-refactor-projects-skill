from flask import jsonify

from services import admin_service


def reset_database():
    admin_service.resetar_banco()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
