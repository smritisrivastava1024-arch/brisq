"""
app/schemas.py
--------------
Pydantic request/response models shared across routers.
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    history: list = []


class AbandonedCartRequest(BaseModel):
    cart_token: str
    customer_name: str
    email: str
    phone: str
    items: str
    cart_value: float
    checkout_url: str
