"""
app/routers/approvals.py
-------------------------
Approval Center endpoints — single source of truth for all approval types
(refund, abandoned_cart, etc.).

Paths (unchanged from original api.py):
  GET  /approvals
  GET  /approvals/all
  POST /approvals/{approval_id}/approve
  POST /approvals/{approval_id}/reject
"""

from fastapi import APIRouter, Depends

from app.deps import require_owner
from database import get_pending_approvals, get_all_approvals, approve_request, reject_request

router = APIRouter()


# ---------------------------------------------------------------------------
# Approval Center — single source of truth for ALL approval types.
# approval_type values in use:
#   "refund"         — created by create_refund_approval() via finance_ai
#   "abandoned_cart" — created by /abandoned-carts/{token}/generate-drafts
# New approval types should use create_approval() from database.py and will
# automatically appear here without any additional endpoint changes.
# ---------------------------------------------------------------------------

@router.get("/approvals")
def list_approvals(_: None = Depends(require_owner)):
    return {"pending_approvals": get_pending_approvals()}


@router.get("/approvals/all")
def list_all_approvals(_: None = Depends(require_owner)):
    return {"approvals": get_all_approvals()}


@router.post("/approvals/{approval_id}/approve")
def approve_approval(approval_id: int, _: None = Depends(require_owner)):
    approve_request(approval_id)
    return {"message": "Approval marked as approved.", "approval_id": approval_id}


@router.post("/approvals/{approval_id}/reject")
def reject_approval(approval_id: int, _: None = Depends(require_owner)):
    reject_request(approval_id)
    return {"message": "Approval marked as rejected.", "approval_id": approval_id}
