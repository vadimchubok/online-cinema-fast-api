import re

import email_validator


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lower letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[@$!%*?&#]", password):
        raise ValueError(
            "Password must contain at least one special character: @, $, !, %, *, ?, #, &."
        )
    return password


def validate_passwords_different(
        new_password: str, old_password: str, hashed_old_password: str = None
) -> None:
    """
    Validate that new password is different from old password.

    Args:
        new_password: The new password
        old_password: The old password in plain text (for comparison)
        hashed_old_password: Optional hashed old password (will verify against it)
    """
    if old_password and new_password == old_password:
        raise ValueError("New password must be different from the current password.")

    if hashed_old_password:
        from src.auth.security import verify_password
        if verify_password(new_password, hashed_old_password):
            raise ValueError("New password must be different from the current password.")


def validate_email(user_email: str) -> str:
    try:
        email_info = email_validator.validate_email(
            user_email, check_deliverability=False
        )
        email = email_info.normalized
    except email_validator.EmailNotValidError as error:
        raise ValueError(str(error))
    else:
        return email
