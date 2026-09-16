from models import produtos_model


def listar_produtos(pagina=1, tamanho=20):
    return produtos_model.get_produtos_paginado(pagina, tamanho)


def buscar_produto(produto_id):
    return produtos_model.get_produto_por_id(produto_id)


def criar_produto(nome, descricao, preco, estoque, categoria):
    return produtos_model.criar_produto(nome, descricao, preco, estoque, categoria)


def atualizar_produto(produto_id, nome, descricao, preco, estoque, categoria):
    if not produtos_model.get_produto_por_id(produto_id):
        return False
    produtos_model.atualizar_produto(produto_id, nome, descricao, preco, estoque, categoria)
    return True


def deletar_produto(produto_id):
    if not produtos_model.get_produto_por_id(produto_id):
        return False
    produtos_model.deletar_produto(produto_id)
    return True


def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    return produtos_model.buscar_produtos(termo, categoria, preco_min, preco_max)
