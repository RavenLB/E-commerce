from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.product import Product
from models.user import User
from schemas import product_schema, products_schema
from marshmallow import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

bp = Blueprint('product', __name__, url_prefix='/products')

def is_admin():
    """Helper function to check if current user is admin"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.is_admin

@bp.route('', methods=['GET'])
def get_products():
    try:
        # Get query parameters
        search = request.args.get('search', '')
        category = request.args.get('category')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        sort_by = request.args.get('sort', 'name')
        order = request.args.get('order', 'asc')
        
        # Validate price range
        if min_price is not None and min_price < 0:
            return jsonify({"message": "Minimum price cannot be negative"}), 400
        if max_price is not None and max_price < 0:
            return jsonify({"message": "Maximum price cannot be negative"}), 400
        if min_price is not None and max_price is not None and min_price > max_price:
            return jsonify({"message": "Minimum price cannot be greater than maximum price"}), 400
            
        # Validate sorting parameters
        valid_sort_fields = ['name', 'price', 'created_at']
        if sort_by not in valid_sort_fields:
            return jsonify({
                "message": f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}"
            }), 400
            
        if order not in ['asc', 'desc']:
            return jsonify({"message": "Order must be 'asc' or 'desc'"}), 400
        
        # Build query
        query = Product.query
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        if category:
            query = query.filter(Product.category == category)
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        # Apply sorting
        if sort_by == 'price':
            sort_column = Product.price
        elif sort_by == 'created_at':
            sort_column = Product.created_at
        else:
            sort_column = Product.name
            
        if order == 'desc':
            sort_column = sort_column.desc()
            
        query = query.order_by(sort_column)
        
        # Get categories for filtering
        categories = db.session.query(Product.category).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        # Execute query
        products = query.all()
        
        if not products:
            return jsonify({
                "message": "No products found matching your criteria",
                "total": 0,
                "products": []
            })
        
        return jsonify({
            "total": len(products),
            "categories": categories,
            "products": products_schema.dump(products)
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred while fetching products"}), 500

@bp.route('/<int:id>', methods=['GET'])
def get_product(id):
    try:
        product = Product.query.get(id)
        if not product:
            return jsonify({
                "message": f"Product with ID {id} not found"
            }), 404
            
        return jsonify(product_schema.dump(product))
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "An error occurred while fetching the product"}), 500

@bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    try:
        if not is_admin():
            return jsonify({"message": "Admin access required"}), 403
            
        data = product_schema.load(request.get_json())
        
        # Additional validations
        if data.get('price', 0) <= 0:
            return jsonify({"message": "Price must be greater than 0"}), 400
            
        if data.get('stock', 0) < 0:
            return jsonify({"message": "Stock cannot be negative"}), 400
            
        product = Product(**data)
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            "message": "Product created successfully",
            "product": product_schema.dump(product)
        }), 201
        
    except ValidationError as err:
        return jsonify({"message": "Validation error", "errors": err.messages}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "A product with this name already exists"}), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"message": "An error occurred while creating the product"}), 500

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_product(id):
    try:
        if not is_admin():
            return jsonify({"message": "Admin access required"}), 403
            
        product = Product.query.get(id)
        if not product:
            return jsonify({
                "message": f"Product with ID {id} not found"
            }), 404
            
        data = product_schema.load(request.get_json(), partial=True)
        
        # Validate price and stock if provided
        if 'price' in data and data['price'] <= 0:
            return jsonify({"message": "Price must be greater than 0"}), 400
            
        if 'stock' in data and data['stock'] < 0:
            return jsonify({"message": "Stock cannot be negative"}), 400
        
        for key, value in data.items():
            setattr(product, key, value)
            
        db.session.commit()
        
        return jsonify({
            "message": "Product updated successfully",
            "product": product_schema.dump(product)
        })
        
    except ValidationError as err:
        return jsonify({"message": "Validation error", "errors": err.messages}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "A product with this name already exists"}), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"message": "An error occurred while updating the product"}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):
    try:
        if not is_admin():
            return jsonify({"message": "Admin access required"}), 403
            
        product = Product.query.get(id)
        if not product:
            return jsonify({
                "message": f"Product with ID {id} not found"
            }), 404
            
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            "message": "Product deleted successfully"
        }), 200
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Cannot delete product as it is referenced in orders or cart"
        }), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"message": "An error occurred while deleting the product"}), 500

@bp.route('/debug', methods=['GET'])
def debug_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price
    } for p in products])
