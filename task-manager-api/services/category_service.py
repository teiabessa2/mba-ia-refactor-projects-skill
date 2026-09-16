import logging

from sqlalchemy import func

from database import db
from models.category import Category
from models.task import Task
from utils.helpers import sanitize_string, DEFAULT_COLOR, is_valid_color
from errors import ValidationError, NotFoundError

logger = logging.getLogger(__name__)


def list_categories():
    categories = Category.query.all()
    task_counts = dict(
        db.session.query(Task.category_id, func.count(Task.id))
        .group_by(Task.category_id)
        .all()
    )
    result = []
    for c in categories:
        data = c.to_dict()
        data['task_count'] = task_counts.get(c.id, 0)
        result.append(data)
    return result


def create_category(data):
    if not data:
        raise ValidationError('Dados inválidos')

    name = sanitize_string(data.get('name'))
    if not name:
        raise ValidationError('Nome é obrigatório')

    color = data.get('color', DEFAULT_COLOR)
    if not is_valid_color(color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = color

    try:
        db.session.add(category)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao criar categoria")
        raise

    return category.to_dict()


def update_category(cat_id, data):
    category = Category.query.get(cat_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    if not data:
        raise ValidationError('Dados inválidos')

    if 'name' in data:
        category.name = sanitize_string(data['name'])
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        if not is_valid_color(data['color']):
            raise ValidationError('Cor inválida. Use o formato #RRGGBB')
        category.color = data['color']

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao atualizar categoria %s", cat_id)
        raise

    return category.to_dict()


def delete_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')

    try:
        db.session.delete(category)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao deletar categoria %s", cat_id)
        raise
