import pytest
from unittest.mock import MagicMock, AsyncMock
from src.notifications.email import send_email
import src.notifications.email as email_module
from src.notifications.services.sendgrid_webhook import SendGridWebhookService
from src.auth.models import User, EmailStatusEnum
from src.core.config import settings


def test_send_email_mocked(monkeypatch):
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "fake_key")
    mock_sg_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_sg_client.client.mail.send.post.return_value = mock_response

    monkeypatch.setattr(email_module, "sg", mock_sg_client)

    send_email(to_email="test@user.com", template_id="d-test-123", data={"user": "Yan"})

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
        send_email(to_email="test@user.com", template_id="d-test-123", data={})

    assert "SendGrid error 400" in str(excinfo.value)


@pytest.mark.asyncio
async def test_process_bounce_event():
    mock_session = AsyncMock()

    test_user = User(id=1, email="bad@email.com", is_active=True)
    mock_session.get.return_value = test_user

    event = {
        "event": "bounce",
        "email": "bad@email.com",
        "custom_args": {"user_id": "1"},
    }

    await SendGridWebhookService.process_event(event, mock_session)
    assert test_user.email_status == EmailStatusEnum.BOUNCED
    assert test_user.is_active is False


@pytest.mark.asyncio
async def test_process_non_fatal_event():
    mock_session = AsyncMock()
    event = {"event": "delivered", "email": "ok@email.com"}
    await SendGridWebhookService.process_event(event, mock_session)
    assert not mock_session.get.called
