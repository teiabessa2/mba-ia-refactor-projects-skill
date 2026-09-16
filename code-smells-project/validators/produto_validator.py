CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]


def validar_produto(dados):
    """Shared field-shape validation for create and update — previously
    duplicated (and drifted) between the two independently."""
    erros = []

    if "nome" not in dados:
        erros.append("Nome é obrigatório")
    else:
        nome = dados["nome"]
        if len(nome) < 2:
            erros.append("Nome muito curto")
        if len(nome) > 200:
            erros.append("Nome muito longo")

    if "preco" not in dados:
        erros.append("Preço é obrigatório")
    elif dados["preco"] < 0:
        erros.append("Preço não pode ser negativo")

    if "estoque" not in dados:
        erros.append("Estoque é obrigatório")
    elif dados["estoque"] < 0:
        erros.append("Estoque não pode ser negativo")

    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        erros.append("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return erros
