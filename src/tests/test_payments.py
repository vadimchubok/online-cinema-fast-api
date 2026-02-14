import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request, HTTPException

from src.auth.models import User, UserGroupEnum
from src.payments.utils import resolve_payment, create_checkout_session
from src.payments.models import Payment
from src.orders.models import Order, OrderStatus
from src.payments.routers import get_my_payments, list_all_payments, refund_payment


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
async def test_get_my_payments(db_session):
    current_user = User(id=1, email="u@t.com")

    with patch("src.payments.routers.get_payments", return_value=[]) as mock_crud:
        res = await get_my_payments(db=db_session, current_user=current_user)
        assert res == []
        mock_crud.assert_called_once()


@pytest.mark.asyncio
async def test_list_all_payments_admin(db_session):
    with patch("src.payments.routers.get_payments", return_value=[]) as mock_crud:
        res = await list_all_payments(db=db_session)
        assert res == []
        args, kwargs = mock_crud.call_args
        assert kwargs["user_group"] == UserGroupEnum.ADMIN


@pytest.mark.asyncio
async def test_refund_payment_no_intent(db_session, mock_stripe):
    test_payment = Payment(id=1, payment_intent=None)

    with patch("src.payments.routers.get_payment_by_id", return_value=test_payment):
        with pytest.raises(HTTPException) as exc:
            await refund_payment(payment_id=1, db=db_session)
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_checkout_session():
    with patch("src.payments.utils.settings") as mock_settings:
        mock_settings.STRIPE_API_KEY = "sk_test_fake_key"

        with patch("src.payments.utils.stripe") as mock_stripe:
            mock_stripe.checkout.Session.create.return_value = MagicMock(
                url="http://stripe.com/pay"
            )

            url = await create_checkout_session(
                user_id=1,
                order_id=1,
                amount=100.0
            )

            assert url == "http://stripe.com/pay"


def test_send_email_task_success():
    from src.tasks.email import send_email_task

    with patch("src.tasks.email.sync_send_email") as mock_sync:
        res = send_email_task(
            to_email="t@t.com", template_id="123", data={}, email_type="test"
        )
        assert "successfully sent" in res
        mock_sync.assert_called_once()
