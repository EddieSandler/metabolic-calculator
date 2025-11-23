import stripe
from fastapi import APIRouter, HTTPException
from .config import STRIPE_SECRET_KEY, STRIPE_PRICE_ID, BASE_URL

router = APIRouter()
stripe.api_key = STRIPE_SECRET_KEY


@router.post("/create-checkout-session")
def create_checkout_session():
    """
    Creates a Stripe checkout session.
    Uses BASE_URL from environment (defaults to localhost for dev, set in Render for production).
    No need to change URLs manually - it's automatic!
    """
    if not STRIPE_PRICE_ID:
        raise HTTPException(500, "Stripe price ID not configured.")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        mode="payment",
        success_url=f"{BASE_URL}/paywall/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}/paywall/cancel",
    )

    return {"checkout_url": session.url}