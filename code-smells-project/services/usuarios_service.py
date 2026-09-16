from werkzeug.security import check_password_hash, generate_password_hash

import auth
from models import usuarios_model


def listar_usuarios():
    return usuarios_model.get_todos_usuarios()


def buscar_usuario(usuario_id):
    return usuarios_model.get_usuario_por_id(usuario_id)


def criar_usuario(nome, email, senha):
    senha_hash = generate_password_hash(senha)
    return usuarios_model.criar_usuario(nome, email, senha_hash)


def login(email, senha):
    usuario = usuarios_model.get_usuario_por_email(email)
    if not usuario or not check_password_hash(usuario["senha"], senha):
        return None

    token = auth.gerar_token(usuario["id"], usuario["tipo"])
    return {
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "tipo": usuario["tipo"],
        },
    }
