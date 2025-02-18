from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Load the app configuration
    app.config.from_object('app.config.Config')

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Import models to ensure they're known to Flask-Migrate
    from models import User, Product, CartItem, Order, OrderItem

    # Register blueprints
    from resources.auth import bp as auth_bp
    from resources.product import bp as product_bp
    from resources.cart import bp as cart_bp
    from resources.order import bp as order_bp
    from resources.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)

    return app
