from database import get_db

COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


def get_produtos_paginado(pagina=1, tamanho=20):
    tamanho = min(max(tamanho, 1), 100)
    pagina = max(pagina, 1)
    offset = (pagina - 1) * tamanho

    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT {COLUNAS} FROM produtos LIMIT ? OFFSET ?", (tamanho, offset))
    itens = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM produtos")
    total = cursor.fetchone()[0]

    return {"itens": itens, "pagina": pagina, "tamanho": tamanho, "total": total}


def get_produto_por_id(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT {COLUNAS} FROM produtos WHERE id = ?", (produto_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_produtos_por_ids(produto_ids):
    if not produto_ids:
        return {}
    db = get_db()
    cursor = db.cursor()
    placeholders = ",".join("?" for _ in produto_ids)
    cursor.execute(f"SELECT {COLUNAS} FROM produtos WHERE id IN ({placeholders})", produto_ids)
    return {row["id"]: dict(row) for row in cursor.fetchall()}


def criar_produto(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar_produto(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def deletar_produto(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    query = f"SELECT {COLUNAS} FROM produtos WHERE 1=1"
    params = []

    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]
