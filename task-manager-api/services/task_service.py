import logging

from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import process_task_data, paginate_args, DEFAULT_PRIORITY
from errors import ValidationError, NotFoundError

logger = logging.getLogger(__name__)


def _serialize(task):
    data = task.to_dict()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def list_tasks(args):
    page, per_page = paginate_args(args)
    pagination = (
        Task.query
        .options(joinedload(Task.user), joinedload(Task.category))
        .order_by(Task.id)
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return {
        'items': [_serialize(t) for t in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
    }


def get_task(task_id):
    task = Task.query.options(joinedload(Task.user), joinedload(Task.category)).get(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return _serialize(task)


def _validate_references(user_id, category_id):
    if user_id and not User.query.get(user_id):
        raise NotFoundError('Usuário não encontrado')
    if category_id and not Category.query.get(category_id):
        raise NotFoundError('Categoria não encontrada')


def create_task(data):
    if not data:
        raise ValidationError('Dados inválidos')
    if not data.get('title'):
        raise ValidationError('Título é obrigatório')

    fields, error = process_task_data(data)
    if error:
        raise ValidationError(error)

    user_id = data.get('user_id')
    category_id = data.get('category_id')
    _validate_references(user_id, category_id)

    task = Task()
    task.title = fields['title']
    task.description = fields.get('description', '')
    task.status = fields.get('status', 'pending')
    task.priority = fields.get('priority', DEFAULT_PRIORITY)
    task.user_id = user_id
    task.category_id = category_id
    task.due_date = fields.get('due_date')
    task.tags = fields.get('tags')

    try:
        db.session.add(task)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao criar task")
        raise

    logger.info("Task criada: %s - %s", task.id, task.title)
    return task.to_dict()


def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    if not data:
        raise ValidationError('Dados inválidos')

    fields, error = process_task_data(data)
    if error:
        raise ValidationError(error)

    if 'user_id' in data:
        _validate_references(data['user_id'], None)
        task.user_id = data['user_id']

    if 'category_id' in data:
        _validate_references(None, data['category_id'])
        task.category_id = data['category_id']

    for field in ('title', 'description', 'status', 'priority', 'due_date', 'tags'):
        if field in fields:
            setattr(task, field, fields[field])

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao atualizar task %s", task_id)
        raise

    logger.info("Task atualizada: %s", task.id)
    return task.to_dict()


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')

    try:
        db.session.delete(task)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Erro ao deletar task %s", task_id)
        raise

    logger.info("Task deletada: %s", task_id)


def search_tasks(args):
    query = args.get('q', '')
    status = args.get('status', '')
    priority = args.get('priority', '')
    user_id = args.get('user_id', '')
    page, per_page = paginate_args(args)

    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category))

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    if priority:
        try:
            tasks = tasks.filter(Task.priority == int(priority))
        except ValueError:
            raise ValidationError('Prioridade inválida')

    if user_id:
        try:
            tasks = tasks.filter(Task.user_id == int(user_id))
        except ValueError:
            raise ValidationError('user_id inválido')

    pagination = tasks.order_by(Task.id).paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [_serialize(t) for t in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
    }


def get_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    overdue_count = sum(1 for t in Task.query.filter(Task.due_date.isnot(None)) if t.is_overdue())

    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
