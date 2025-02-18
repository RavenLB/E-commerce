from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app import db
from models.cart import CartItem
from models.order import Order, OrderItem
from models.product import Product
from schemas import cart_item_schema, cart_items_schema, order_schema
from sqlalchemy.exc import IntegrityError
from resources.stripe import create_payment_intent

bp = Blueprint('cart', __name__, url_prefix='/cart')

@bp.route('', methods=['GET'])
@jwt_required()
def get_cart():
    try:
        user_id = get_jwt_identity()
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        
        if not cart_items:
            return jsonify({
                "message": "Your cart is empty",
                "cart_items": []
            })
            
        return jsonify(cart_items_schema.dump(cart_items))
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred while fetching your cart"}), 500

@bp.route('', methods=['POST'])
@jwt_required()
def add_to_cart():
    try:
        user_id = get_jwt_identity()
        data = cart_item_schema.load(request.get_json())
        
        # Check if product exists
        product = Product.query.get(data['product_id'])
        if not product:
            return jsonify({
                "message": f"Product with ID {data['product_id']} does not exist"
            }), 404
            
        # Validate quantity
        if data['quantity'] <= 0:
            return jsonify({
                "message": "Quantity must be greater than 0"
            }), 400
            
        # Check stock availability
        if product.stock < data['quantity']:
            return jsonify({
                "message": f"Not enough stock available. Only {product.stock} items left"
            }), 400
        
        # Check if item already exists in cart
        existing_item = CartItem.query.filter_by(
            user_id=user_id,
            product_id=data['product_id']
        ).first()
        
        if existing_item:
            # Update quantity of existing item
            new_quantity = existing_item.quantity + data['quantity']
            if new_quantity > product.stock:
                return jsonify({
                    "message": f"Cannot add {data['quantity']} more items. Only {product.stock - existing_item.quantity} more available"
                }), 400
                
            existing_item.quantity = new_quantity
            cart_item = existing_item
        else:
            # Create new cart item
            cart_item = CartItem(
                user_id=user_id,
                product_id=data['product_id'],
                quantity=data['quantity']
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        return jsonify({
            "message": "Item added to cart successfully",
            "cart_item": cart_item_schema.dump(cart_item)
        }), 201
        
    except ValidationError as err:
        return jsonify({"message": "Validation error", "errors": err.messages}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Database integrity error. Please try again"}), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"message": "An error occurred while adding item to cart"}), 500

@bp.route('/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(item_id):
    try:
        user_id = get_jwt_identity()
        
        # Check if cart item exists and belongs to user
        cart_item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
        if not cart_item:
            return jsonify({
                "message": f"Cart item with ID {item_id} not found in your cart"
            }), 404
        
        data = cart_item_schema.load(request.get_json(), partial=True)
        
        if 'quantity' in data:
            # Validate quantity
            if data['quantity'] <= 0:
                return jsonify({
                    "message": "Quantity must be greater than 0"
                }), 400
                
            # Check stock availability
            product = Product.query.get(cart_item.product_id)
            if not product:
                return jsonify({
                    "message": "Product no longer exists"
                }), 400
                
            if data['quantity'] > product.stock:
                return jsonify({
                    "message": f"Not enough stock available. Only {product.stock} items available"
                }), 400
                
            cart_item.quantity = data['quantity']
            
        db.session.commit()
        return jsonify({
            "message": "Cart item updated successfully",
            "cart_item": cart_item_schema.dump(cart_item)
        })
        
    except ValidationError as err:
        return jsonify({"message": "Validation error", "errors": err.messages}), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"message": "An error occurred while updating cart item"}), 500

@bp.route('/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    try:
        user_id = get_jwt_identity()
        
        # Check if cart item exists and belongs to user
        cart_item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
        if not cart_item:
            return jsonify({
                "message": f"Cart item with ID {item_id} not found in your cart"
            }), 404
        
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({
            "message": "Item removed from cart successfully"
        }), 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"message": "An error occurred while removing item from cart"}), 500

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
        
        # Create payment intent
        payment_intent = create_payment_intent(int(total_amount * 100))
        if not payment_intent:
            return jsonify({"message": "Payment processing failed"}), 500
        
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
        
        # After creating the payment intent
        order.status = 'paid'  # Simulate successful payment
        db.session.commit()
        
        return jsonify({
            "message": "Order created successfully",
            "order": order_schema.dump(order),
            "payment_intent": payment_intent
        }), 201
        
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"message": "An error occurred during checkout"}), 500
