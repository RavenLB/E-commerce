from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app import db
from models.user import User
from models.product import Product
from models.order import Order
from schemas import product_schema, order_schema, orders_schema

bp = Blueprint('admin', __name__, url_prefix='/admin')

def is_admin():
    """Helper function to check if current user is admin"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.is_admin

@bp.route('/orders', methods=['GET'])
@jwt_required()
def get_all_orders():
    try:
        if not is_admin():
            return jsonify({"message": "Admin access required"}), 403
            
        # Optional query parameters for filtering
        status = request.args.get('status')
        user_id = request.args.get('user_id')
        
        # Start with base query
        query = Order.query
        
        # Apply filters if provided
        if status:
            query = query.filter_by(status=status)
        if user_id:
            query = query.filter_by(user_id=user_id)
            
        # Order by creation date (newest first)
        orders = query.order_by(Order.created_at.desc()).all()
        
        return jsonify({
            "total": len(orders),
            "orders": orders_schema.dump(orders)
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500

@bp.route('/orders/<int:id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(id):
    try:
        if not is_admin():
            return jsonify({"message": "Admin access required"}), 403
            
        order = Order.query.get_or_404(id)
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({"message": "Status is required"}), 400
            
        valid_statuses = ['pending', 'paid', 'shipped', 'delivered', 'cancelled']
        if data['status'] not in valid_statuses:
            return jsonify({"message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
            
        # If cancelling order, return items to stock
        if data['status'] == 'cancelled' and order.status != 'cancelled':
            for item in order.items:
                if item.product:
                    item.product.stock += item.quantity
        
        order.status = data['status']
        db.session.commit()
        
        return jsonify({
            "message": "Order status updated successfully",
            "order": order_schema.dump(order)
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500

@bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"message": "Unauthorized"}), 403
            
        data = product_schema.load(request.get_json())
        product = Product(**data)
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify(product_schema.dump(product)), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

@bp.route('/products/<int:id>', methods=['PUT'])
@jwt_required()
def update_product(id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"message": "Unauthorized"}), 403
            
        product = Product.query.get_or_404(id)
        data = product_schema.load(request.get_json(), partial=True)
        
        for key, value in data.items():
            setattr(product, key, value)
            
        db.session.commit()
        return jsonify(product_schema.dump(product))
    except ValidationError as err:
        return jsonify(err.messages), 400

@bp.route('/products/<int:id>/stock', methods=['PUT'])
@jwt_required()
def update_product_stock(id):
    try:
        if not is_admin():
            return jsonify({"message": "Admin access required"}), 403
            
        product = Product.query.get_or_404(id)
        data = request.get_json()
        
        if 'stock' not in data:
            return jsonify({"message": "Stock quantity is required"}), 400
            
        if not isinstance(data['stock'], int) or data['stock'] < 0:
            return jsonify({"message": "Stock must be a positive integer"}), 400
            
        product.stock = data['stock']
        db.session.commit()
        
        return jsonify({
            "message": "Stock updated successfully",
            "product": product_schema.dump(product)
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500
