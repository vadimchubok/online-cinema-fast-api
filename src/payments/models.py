from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, DECIMAL

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class PaymentStatus(str, Enum):
    SUCCESSFUL = "SUCCESSFUL"
    CANCELED = "CANCELED"
    REFUNDED = "REFUNDED"


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    external_payment_id: Mapped[Optional[str]]


class PaymentItem(Base):
    __tablename__ = "payment_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price_at_payment: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
