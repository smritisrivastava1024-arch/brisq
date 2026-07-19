"""
app/routers/abandoned_carts.py
-------------------------------
Abandoned-cart management endpoints.

Paths (unchanged from original api.py):
  POST /abandoned-carts/create
  GET  /abandoned-carts
  POST /abandoned-carts/{cart_token}/generate-drafts
"""

from fastapi import APIRouter, Depends, HTTPException

from app.config import MODEL
from app.deps import groq_client, require_owner
from app.schemas import AbandonedCartRequest

from database import (
    create_abandoned_cart,
    get_pending_abandoned_carts,
    get_abandoned_cart_by_token,
    update_abandoned_cart_ai_messages,
    create_approval,
)

router = APIRouter()


@router.post("/abandoned-carts/create")
def create_abandoned_cart_endpoint(
    request: AbandonedCartRequest,
    _: None = Depends(require_owner),
):
    create_abandoned_cart(
        request.cart_token,
        request.customer_name,
        request.email,
        request.phone,
        request.items,
        request.cart_value,
        request.checkout_url,
    )
    return {"message": "Abandoned cart saved successfully.", "cart_token": request.cart_token}


@router.get("/abandoned-carts")
def list_abandoned_carts(_: None = Depends(require_owner)):
    return {"pending_abandoned_carts": get_pending_abandoned_carts()}


@router.post("/abandoned-carts/{cart_token}/generate-drafts")
def generate_abandoned_cart_drafts(
    cart_token: str,
    _: None = Depends(require_owner),
):
    cart = get_abandoned_cart_by_token(cart_token)

    if not cart:
        raise HTTPException(status_code=404, detail="Abandoned cart not found")

    prompt = f"""
You are Brisq Marketing AI.

Create abandoned cart recovery drafts for this customer.

Customer:
{cart["customer_name"]}

Email:
{cart["email"]}

Phone:
{cart["phone"]}

Items:
{cart["items"]}

Cart value:
\u20b9{cart["cart_value"]}

Checkout URL:
{cart["checkout_url"]}

Return exactly this format:

EMAIL:
<email subject + email body>

WHATSAPP:
<short WhatsApp message>

COUPON:
<suggested coupon or incentive>
"""

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    ai_text = response.choices[0].message.content

    email_part = ai_text
    whatsapp_part = ai_text
    coupon_part = "No coupon suggested"

    if "EMAIL:" in ai_text and "WHATSAPP:" in ai_text:
        email_part = ai_text.split("WHATSAPP:")[0].replace("EMAIL:", "").strip()
        rest = ai_text.split("WHATSAPP:")[1]

        if "COUPON:" in rest:
            whatsapp_part = rest.split("COUPON:")[0].strip()
            coupon_part = rest.split("COUPON:")[1].strip()
        else:
            whatsapp_part = rest.strip()

    update_abandoned_cart_ai_messages(cart_token, email_part, whatsapp_part, coupon_part)

    create_approval(
        approval_type="abandoned_cart",
        reference_id=cart_token,
        title=f"Abandoned cart recovery for {cart['customer_name']}",
        description=f"Recovery message for cart worth \u20b9{cart['cart_value']}",
        payload={
            "cart_token": cart_token,
            "customer_name": cart["customer_name"],
            "email": cart["email"],
            "phone": cart["phone"],
            "items": cart["items"],
            "cart_value": cart["cart_value"],
            "checkout_url": cart["checkout_url"],
            "email_draft": email_part,
            "whatsapp_draft": whatsapp_part,
            "suggested_coupon": coupon_part,
            "action": "abandoned_cart_recovery_requires_owner_approval",
        },
    )

    return {
        "message": "AI recovery drafts generated, saved, and sent to Approval Center.",
        "cart_token": cart_token,
        "email_draft": email_part,
        "whatsapp_draft": whatsapp_part,
        "suggested_coupon": coupon_part,
    }
