from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app import db
from models.cart import CartItem
from models.order import Order, OrderItem
from models.product import Product
from schemas import cart_item_schema, cart_items_schema, order_schema

bp = Blueprint('cart', __name__, url_prefix='/cart')

@bp.route('', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    return jsonify(cart_items_schema.dump(cart_items))

@bp.route('', methods=['POST'])
@jwt_required()
def add_to_cart():
    try:
        user_id = get_jwt_identity()
        data = cart_item_schema.load(request.get_json())
        
        cart_item = CartItem(
            user_id=user_id,
            product_id=data['product_id'],
            quantity=data['quantity']
        )
        
        db.session.add(cart_item)
        db.session.commit()
        
        return jsonify(cart_item_schema.dump(cart_item)), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

@bp.route('/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(item_id):
    try:
        user_id = get_jwt_identity()
        cart_item = CartItem.query.filter_by(id=item_id, user_id=user_id).first_or_404()
        
        data = cart_item_schema.load(request.get_json(), partial=True)
        
        if 'quantity' in data:
            cart_item.quantity = data['quantity']
            
        db.session.commit()
        return jsonify(cart_item_schema.dump(cart_item))
    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500

@bp.route('/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    try:
        user_id = get_jwt_identity()
        cart_item = CartItem.query.filter_by(id=item_id, user_id=user_id).first_or_404()
        
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({"message": "Item removed from cart"}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred"}), 500

@bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    try:
        user_id = get_jwt_identity()
        
        # Get all cart items for the user
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        
        if not cart_items:
            return jsonify({"message": "Cart is empty"}), 400
            
        # Calculate total amount
        total_amount = 0
        order_items_data = []
        
        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_id)
            if not product:
                return jsonify({"message": f"Product {cart_item.product_id} not found"}), 400
                
            if product.stock < cart_item.quantity:
                return jsonify({"message": f"Not enough stock for {product.name}"}), 400
                
            item_total = product.price * cart_item.quantity
            total_amount += item_total
            
            order_items_data.append({
                "product_id": product.id,
                "quantity": cart_item.quantity,
                "price": product.price
            })
            
            # Update product stock
            product.stock -= cart_item.quantity
        
        # Create order
        order = Order(
            user_id=user_id,
            status='pending',
            total_amount=total_amount
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                price=item_data["price"]
            )
            db.session.add(order_item)
        
        # Clear the cart
        for cart_item in cart_items:
            db.session.delete(cart_item)
            
        db.session.commit()
        
        return jsonify({
            "message": "Order created successfully",
            "order": order_schema.dump(order)
        }), 201
        
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"message": "An error occurred during checkout"}), 500
