import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from src.notifications.email import send_email
import src.notifications.email as email_module
from src.notifications.services.sendgrid_webhook import SendGridWebhookService
from src.auth.models import User
from src.core.config import settings


def test_send_email_mocked(monkeypatch):
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "fake_key")
    mock_sg_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_sg_client.client.mail.send.post.return_value = mock_response
    monkeypatch.setattr(email_module, "sg", mock_sg_client)

    send_email(
        to_email="test@user.com",
        template_id="d-test-123",
        data={"user": "Yan"},
        email_type="welcome",
    )
    assert mock_sg_client.client.mail.send.post.called


def test_send_email_error(monkeypatch):
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "fake_key")
    mock_sg_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.body = "Invalid API Key"
    mock_sg_client.client.mail.send.post.return_value = mock_response
    monkeypatch.setattr(email_module, "sg", mock_sg_client)

    with pytest.raises(RuntimeError) as excinfo:
        send_email(
            to_email="test@user.com",
            template_id="d-test-123",
            data={},
            email_type="verification",
        )
    assert "SendGrid error 400" in str(excinfo.value)


@pytest.mark.asyncio
async def test_process_bounce_event():
    mock_session = AsyncMock(spec=AsyncSession)
    test_user = User(id=1, email="bad@email.com", is_active=False)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session.execute.return_value = mock_result
    event = {
        "event": "bounce",
        "email": "bad@email.com",
        "email_type": "email_activation",
    }
    service = SendGridWebhookService()
    with patch(
        "src.notifications.services.sendgrid_webhook.send_telegram_message",
        new_callable=AsyncMock,
    ) as mock_send:
        await service.process_event(event, mock_session)

        mock_session.delete.assert_called_once_with(test_user)
        mock_session.commit.assert_called_once()
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_process_non_fatal_event():
    mock_session = AsyncMock()
    event = {"event": "delivered", "email": "ok@email.com"}
    service = SendGridWebhookService()
    await service.process_event(event, mock_session)
    assert not mock_session.execute.called
