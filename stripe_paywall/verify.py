# stripe_paywall/verify.py

import stripe
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from .config import STRIPE_SECRET_KEY, STRIPE_PRICE_ID

router = APIRouter()

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY


@router.get("/paywall/success")
async def stripe_success(request: Request, session_id: str = Query(...)):
    """
    Called by Stripe after a successful checkout.
    Verifies the session, sets an access cookie, and processes pending calculation if exists.
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid session ID: {e}")

    # Basic sanity checks
    if session.get("payment_status") != "paid":
        raise HTTPException(status_code=403, detail="Payment not completed")

    if session.get("mode") != "payment":
        raise HTTPException(status_code=400, detail="Unexpected session mode")

    # Optional: ensure our price was used (defensive)
    # This assumes you only have one line item and it's our PRICE_ID.
    try:
        line_items = stripe.checkout.Session.list_line_items(session.id, limit=1)
        price_id = line_items.data[0].price.id if line_items.data else None
    except Exception:
        price_id = None

    if STRIPE_PRICE_ID and price_id and price_id != STRIPE_PRICE_ID:
        raise HTTPException(status_code=400, detail="Unexpected product/price in session")

    # At this point, payment is good.
    # Grant access by setting a cookie
    # Check if there's a pending calculation to process
    pending_calculation = request.session.get("pending_calculation")
    
    if pending_calculation:
        # Redirect to process the calculation
        response = RedirectResponse(url="/process-pending-calculation", status_code=303)
    else:
        # No pending calculation, just go to home
        response = RedirectResponse(url="/", status_code=303)
    
    # Set access cookie
    response.set_cookie(
        key="calculator_access",
        value="granted",
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 365,  # 1 year
    )
    return response


@router.get("/paywall/cancel")
async def stripe_cancel(request: Request):
    """
    Called when user cancels on Stripe Checkout.
    Clear any pending calculation and redirect back to calculator.
    """
    # Clear pending calculation if user cancels
    request.session.pop("pending_calculation", None)
    # Redirect back to calculator
    return RedirectResponse(url="/")