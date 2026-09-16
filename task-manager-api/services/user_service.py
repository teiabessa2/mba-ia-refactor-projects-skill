import logging

from sqlalchemy import func

from database import db
from models.user import User
from models.task import Task
from utils.helpers import validate_email, sanitize_string, MIN_PASSWORD_LENGTH, VALID_ROLES
from utils.auth import generate_token
from errors import ValidationError, NotFoundError, ConflictError, AuthError, ForbiddenError

logger = logging.getLogger(__name__)


def list_users():
    users = User.query.all()
    task_counts = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .group_by(Task.user_id)
        .all()
    )
    result = []
    for u in users:
        data = u.to_dict()
        data['task_count'] = task_counts.get(u.id, 0)
        result.append(data)
    return result


def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    data = user.to_dict()
    tasks = Task.query.filter_by(user_id=user_id).all()
    data['tasks'] = [t.to_dict() for t in tasks]
    return data


def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    tasks = Task.query.filter_by(user_id=user_id).all()
    return [t.to_dict() for t in tasks]


def create_user(data):
    if not data:
        raise ValidationError('Dados inválidos')

    name = sanitize_string(data.get('name'))
    email = sanitize_string(data.get('email'))
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not validate_email(email):
        raise ValidationError('Email inválido')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')

    if User.query.filter_by(email=email).first():
        raise ConflictError('Email já cadastrado')

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao criar usuário")
        raise

    logger.info("Usuário criado: %s - %s", user.id, user.name)
    return user.to_dict()


def update_user(user_id, data):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    if not data:
        raise ValidationError('Dados inválidos')

    if 'name' in data:
        user.name = sanitize_string(data['name'])

    if 'email' in data:
        email = sanitize_string(data['email'])
        if not validate_email(email):
            raise ValidationError('Email inválido')
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')
        user.email = email

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            raise ValidationError('Role inválido')
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao atualizar usuário %s", user_id)
        raise

    return user.to_dict()


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    tasks = Task.query.filter_by(user_id=user_id).all()
    for t in tasks:
        db.session.delete(t)

    try:
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao deletar usuário %s", user_id)
        raise

    logger.info("Usuário deletado: %s", user_id)


def authenticate(email, password):
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise AuthError('Credenciais inválidas')

    if not user.active:
        raise ForbiddenError('Usuário inativo')

    token = generate_token(user.id)
    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token,
    }
