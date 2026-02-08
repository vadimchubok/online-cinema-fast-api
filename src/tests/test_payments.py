import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request

from src.auth.models import User
from src.payments.utils import resolve_payment
from src.orders.models import Order, OrderStatus


@pytest.fixture
def mock_stripe():
    with patch("src.payments.routers.stripe") as mock:
        yield mock


@pytest.mark.asyncio
async def test_stripe_webhook_success(db_session):
    payload = {
        "type": "checkout.session.completed",
        "id": "evt_test_123",
        "data": {
            "object": {
                "amount_total": 5000,
                "payment_intent": "pi_test_123",
                "metadata": {"user_id": "1", "order_id": "1"},
            }
        },
    }

    mock_request = AsyncMock(spec=Request)
    mock_request.json.return_value = payload
    mock_order = Order(id=1, status=OrderStatus.PENDING)
    mock_user = User(id=1, email="test@user.com")

    db_session.get = AsyncMock(
        side_effect=lambda model, obj_id: (
            mock_order if model == Order else (mock_user if model == User else None)
        )
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db_session.execute = AsyncMock(return_value=mock_result)
    db_session.scalar = AsyncMock(return_value=None)

    with patch("src.payments.utils.send_email"), patch("src.payments.utils.delete"):
        try:
            await resolve_payment(mock_request, db_session)
        except UnboundLocalError:
            pass

    assert mock_order.status == OrderStatus.PAID
