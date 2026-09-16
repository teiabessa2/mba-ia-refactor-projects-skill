from flask import Blueprint, request, jsonify

from services import category_service
from utils.auth import login_required

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(category_service.list_categories()), 200


@category_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    data = request.get_json(silent=True)
    result = category_service.create_category(data)
    return jsonify(result), 201


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@login_required
def update_category(cat_id):
    data = request.get_json(silent=True)
    result = category_service.update_category(cat_id, data)
    return jsonify(result), 200


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@login_required
def delete_category(cat_id):
    category_service.delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
