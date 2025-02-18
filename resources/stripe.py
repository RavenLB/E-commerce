import stripe
from flask import current_app

# Initialize Stripe with your secret key
stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

def create_payment_intent(amount, currency='eur'):
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            payment_method_types=["card"],
        )
        return payment_intent
    except Exception as e:
        print(f"Stripe error: {str(e)}")
        return None 