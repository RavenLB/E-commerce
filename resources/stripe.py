import stripe
import os
import dotenv

# Load environment variables from .env
dotenv.load_dotenv()

# Set API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

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