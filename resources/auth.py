from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from marshmallow import ValidationError
from app import db
from models.user import User
from schemas import user_schema

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = user_schema.load(request.get_json(), partial=('username',))
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=str(user.id))
            return jsonify({
                "access_token": access_token,
                "user": user_schema.dump(user)
            })
        
        return jsonify({"message": "Invalid credentials"}), 401
    except ValidationError as err:
        return jsonify(err.messages), 400

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = user_schema.load(request.get_json())
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"message": "User already exists!"}), 400

        user = User(
            username=data['username'],
            email=data['email'],
            is_admin=data.get('is_admin', False)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "access_token": access_token,
            "user": user_schema.dump(user)
        }), 201
    except ValidationError as err:
        return jsonify(err.messages), 400