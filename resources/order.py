from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app import db
from models.order import Order, OrderItem
from schemas import order_schema, orders_schema, OrderItemSchema

bp = Blueprint('order', __name__, url_prefix='/orders')

@bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    try:
        user_id = get_jwt_identity()
        data = order_schema.load(request.get_json())
        
        order = Order(
            user_id=user_id,
            status='pending',
            total_amount=sum(item['price'] * item['quantity'] for item in data['items'])
        )
        
        db.session.add(order)
        db.session.commit()
        
        for item_data in data['items']:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            db.session.add(order_item)
        
        db.session.commit()
        return jsonify(order_schema.dump(order)), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

@bp.route('', methods=['GET'])
@jwt_required()
def get_orders():
    try:
        user_id = get_jwt_identity()
        # Get all orders for the current user, ordered by creation date (newest first)
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        return jsonify(orders_schema.dump(orders))
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_order(id):
    try:
        user_id = get_jwt_identity()
        # Get specific order, ensuring it belongs to the current user
        order = Order.query.filter_by(id=id, user_id=user_id).first_or_404()
        return jsonify(order_schema.dump(order))
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500

@bp.route('/<int:id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(id):
    try:
        user_id = get_jwt_identity()
        order = Order.query.filter_by(id=id, user_id=user_id).first_or_404()
        
        if order.status != 'pending':
            return jsonify({"message": "Only pending orders can be cancelled"}), 400
            
        # Return items to stock
        for item in order.items:
            product = item.product
            if product:
                product.stock += item.quantity
        
        order.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            "message": "Order cancelled successfully",
            "order": order_schema.dump(order)
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500
