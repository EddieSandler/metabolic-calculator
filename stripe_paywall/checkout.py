import stripe
from fastapi import APIRouter, HTTPException
from stripe_paywall.config import STRIPE_SECRET_KEY, STRIPE_PRICE_ID

router = APIRouter()
stripe.api_key = STRIPE_SECRET_KEY


@router.post("/create-checkout-session")
def create_checkout_session():
    if not STRIPE_PRICE_ID:
        raise HTTPException(500, "Stripe price ID not configured.")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        mode="payment",
        success_url="http://127.0.0.1:8000/paywall/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://127.0.0.1:8000/paywall/cancel",
    )

    return {"checkout_url": session.url}