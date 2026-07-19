import os
import sqlite3
import pytest
import database

# Use an in-memory database for testing
TEST_DB_NAME = ":memory:"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """
    Patches database.DB_NAME to use an in-memory database for all tests,
    ensuring isolation and no side effects on brisq.db.
    """
    monkeypatch.setattr(database, "DB_NAME", TEST_DB_NAME)
    database.initialize_database()

def test_create_and_get_abandoned_cart():
    database.create_abandoned_cart(
        cart_token="cart_123",
        customer_name="Test User",
        email="test@example.com",
        phone="555-1234",
        items="Test Item",
        cart_value=100.0,
        checkout_url="http://example.com/checkout"
    )
    
    pending = database.get_pending_abandoned_carts()
    assert len(pending) == 1
    assert pending[0]["cart_token"] == "cart_123"
    assert pending[0]["customer_name"] == "Test User"

def test_create_and_approve_request():
    database.create_approval(
        approval_type="refund",
        reference_id="order_123",
        title="Refund Request",
        description="Customer requested refund",
        payload={"amount": 100}
    )
    
    pending = database.get_pending_approvals()
    assert len(pending) == 1
    
    approval_id = pending[0]["id"]
    database.approve_request(approval_id)
    
    pending_after = database.get_pending_approvals()
    assert len(pending_after) == 0
    
    all_approvals = database.get_all_approvals()
    assert len(all_approvals) == 1
    assert all_approvals[0]["status"] == "approved"

def test_reject_request():
    database.create_approval(
        approval_type="discount",
        reference_id="order_456",
        title="Discount Request",
        description="Give discount",
        payload={}
    )
    
    pending = database.get_pending_approvals()
    approval_id = pending[0]["id"]
    
    database.reject_request(approval_id)
    
    all_approvals = database.get_all_approvals()
    assert all_approvals[0]["status"] == "rejected"
