class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ecommerce.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key_here'
    JWT_SECRET_KEY = 'your_jwt_secret_key_here'
    STRIPE_SECRET_KEY = 'sk_test_51QtsSkP8emwpFUP7nCrZx4GrWFwx0ZRetVakqgYazUHGv0aR7dW6q3QYPU2Ot1YTgYStFIUcscZoBo4hctRI7V8x00w0LeQzsb'
    JWT_ACCESS_TOKEN_EXPIRES = False  # Add this for testing (tokens won't expire)

