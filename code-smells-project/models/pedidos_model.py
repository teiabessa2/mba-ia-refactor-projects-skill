from database import get_db


def criar_pedido(usuario_id, total, itens):
    """Persists an order and its items. itens: [{produto_id, quantidade, preco_unitario}].

    Stock/total validation is the caller's (service's) job — this function
    only writes the rows it's given.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    cursor.executemany(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        [(pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]) for item in itens],
    )
    cursor.executemany(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
        [(item["quantidade"], item["produto_id"]) for item in itens],
    )

    db.commit()
    return pedido_id


def _montar_pedidos_com_itens(rows):
    pedido_ids = [row["id"] for row in rows]
    itens_por_pedido = {pid: [] for pid in pedido_ids}

    if pedido_ids:
        db = get_db()
        cursor = db.cursor()
        placeholders = ",".join("?" for _ in pedido_ids)
        cursor.execute(
            f"""
            SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
                   p.nome AS produto_nome
            FROM itens_pedido ip
            LEFT JOIN produtos p ON p.id = ip.produto_id
            WHERE ip.pedido_id IN ({placeholders})
            """,
            pedido_ids,
        )
        for item in cursor.fetchall():
            itens_por_pedido[item["pedido_id"]].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"] or "Desconhecido",
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })

    return [
        {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": itens_por_pedido[row["id"]],
        }
        for row in rows
    ]


def get_pedidos_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    return _montar_pedidos_com_itens(cursor.fetchall())


def get_todos_pedidos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos")
    return _montar_pedidos_com_itens(cursor.fetchall())


def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()


def estatisticas_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
    faturamento_bruto = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": faturamento_bruto,
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
    }
