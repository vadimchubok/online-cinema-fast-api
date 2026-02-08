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

    with patch("src.payments.utils.send_email"):
        await resolve_payment(mock_request, db_session)

    assert mock_order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_stripe_webhook_refund_created(db_session):
    payload = {
        "type": "refund.created",
        "id": "re_123",
        "data": {"object": {"payment_intent": "pi_test_123"}},
    }

    mock_request = AsyncMock(spec=Request)
    mock_request.json.return_value = payload

    mock_payment = Payment(
        id=1, order_id=10, payment_intent="pi_test_123", status=PaymentStatus.SUCCESSFUL
    )
    mock_order = Order(id=10, status=OrderStatus.PAID)

    db_session.scalar = AsyncMock(return_value=mock_payment)
    db_session.get = AsyncMock(return_value=mock_order)

    await resolve_payment(mock_request, db_session)
    assert mock_payment.status == PaymentStatus.REFUNDED
    assert mock_order.status == OrderStatus.CANCELED


@pytest.mark.asyncio
async def test_refund_payment_router_success(mock_stripe, db_session):
    from src.payments.routers import refund_payment

    mock_stripe.Refund.create.return_value = MagicMock(id="re_test_999")
    test_payment = Payment(
        id=1, payment_intent="pi_123", status=PaymentStatus.SUCCESSFUL
    )

    with patch("src.payments.routers.get_payment_by_id", return_value=test_payment):
        response = await refund_payment(payment_id=1, db=db_session)

    assert response["status"] == "refund_initiated"
    assert response["refund_id"] == "re_test_999"
