from flask import jsonify, request

from services import usuarios_service


def listar_usuarios():
    usuarios = usuarios_service.listar_usuarios()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(id):
    usuario = usuarios_service.buscar_usuario(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    id = usuarios_service.criar_usuario(nome, email, senha)
    return jsonify({"dados": {"id": id}, "sucesso": True}), 201


def login():
    dados = request.get_json(silent=True) or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    resultado = usuarios_service.login(email, senha)
    if not resultado:
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Login OK"}), 200
