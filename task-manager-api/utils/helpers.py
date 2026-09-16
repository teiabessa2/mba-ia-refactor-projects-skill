from datetime import datetime, timezone
import logging
import re

logger = logging.getLogger(__name__)


def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    if re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email):
        return True
    return False


def sanitize_string(s):
    if s:
        return s.strip()
    return s


def generate_id():
    import uuid
    return str(uuid.uuid4())


def log_action(action, details=None):
    if details:
        logger.info("ACTION: %s DETAILS: %s", action, details)
    else:
        logger.info("ACTION: %s", action)


def parse_date(date_string):
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_string, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def is_valid_color(color):
    if color and len(color) == 7 and color[0] == '#':
        return True
    return False


def paginate_args(args):
    try:
        page = max(1, int(args.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(args.get('per_page', DEFAULT_PAGE_SIZE))
    except (TypeError, ValueError):
        per_page = DEFAULT_PAGE_SIZE
    per_page = max(1, min(per_page, MAX_PAGE_SIZE))
    return page, per_page


def process_task_data(data, existing_task=None):
    from models.task import Task

    result = {}

    if 'title' in data:
        title = sanitize_string(data['title'])
        if title:
            if len(title) >= 3 and len(title) <= 200:
                result['title'] = title
            else:
                return None, 'Título deve ter entre 3 e 200 caracteres'
        else:
            return None, 'Título não pode ser vazio'

    if 'description' in data:
        result['description'] = data['description']

    if 'status' in data:
        if Task.validate_status(data['status']):
            result['status'] = data['status']
        else:
            return None, 'Status inválido'

    if 'priority' in data:
        try:
            p = int(data['priority'])
        except (TypeError, ValueError):
            return None, 'Prioridade inválida'
        if Task.validate_priority(p):
            result['priority'] = p
        else:
            return None, 'Prioridade deve ser entre 1 e 5'

    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if parsed:
                result['due_date'] = parsed
            else:
                return None, 'Data inválida'
        else:
            result['due_date'] = None

    if 'tags' in data:
        tags = data['tags']
        if type(tags) == list:
            result['tags'] = ','.join(tags)
        else:
            result['tags'] = tags

    return result, None


VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
