from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.product import Product
from models.user import User
from schemas import product_schema, products_schema
from marshmallow import ValidationError

bp = Blueprint('product', __name__, url_prefix='/products')

def is_admin():
    """Helper function to check if current user is admin"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.is_admin

@bp.route('', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify(products_schema.dump(products))

@bp.route('/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify(product_schema.dump(product))

@bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    try:
        if not is_admin():
            return jsonify({"message": "Admin access required"}), 403
            
        data = product_schema.load(request.get_json())
        product = Product(**data)
        db.session.add(product)
        db.session.commit()
        return jsonify(product_schema.dump(product)), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_product(id):
    try:
        if not is_admin():
            return jsonify({"message": "Admin access required"}), 403
            
        product = Product.query.get_or_404(id)
        data = product_schema.load(request.get_json(), partial=True)
        
        for key, value in data.items():
            setattr(product, key, value)
            
        db.session.commit()
        return jsonify(product_schema.dump(product))
    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):
    try:
        if not is_admin():
            return jsonify({"message": "Admin access required"}), 403
            
        product = Product.query.get_or_404(id)
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({"message": "Product deleted successfully"}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500

@bp.route('/debug', methods=['GET'])
def debug_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price
    } for p in products])
