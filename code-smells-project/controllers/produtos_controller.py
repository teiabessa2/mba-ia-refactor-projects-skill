from flask import jsonify, request

from services import produtos_service
from validators.produto_validator import validar_produto


def listar_produtos():
    pagina = int(request.args.get("pagina", 1))
    tamanho = int(request.args.get("tamanho", 20))
    resultado = produtos_service.listar_produtos(pagina, tamanho)
    return jsonify({
        "dados": resultado["itens"],
        "pagina": resultado["pagina"],
        "tamanho": resultado["tamanho"],
        "total": resultado["total"],
        "sucesso": True,
    }), 200


def buscar_produto(id):
    produto = produtos_service.buscar_produto(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min = request.args.get("preco_min")
    preco_max = request.args.get("preco_max")
    preco_min = float(preco_min) if preco_min else None
    preco_max = float(preco_max) if preco_max else None

    resultados = produtos_service.buscar_produtos(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar_produto():
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    erros = validar_produto(dados)
    if erros:
        return jsonify({"erro": "; ".join(erros)}), 400

    id = produtos_service.criar_produto(
        dados["nome"], dados.get("descricao", ""), dados["preco"],
        dados["estoque"], dados.get("categoria", "geral"),
    )
    return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    erros = validar_produto(dados)
    if erros:
        return jsonify({"erro": "; ".join(erros)}), 400

    atualizado = produtos_service.atualizar_produto(
        id, dados["nome"], dados.get("descricao", ""), dados["preco"],
        dados["estoque"], dados.get("categoria", "geral"),
    )
    if not atualizado:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    if not produtos_service.deletar_produto(id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
