from io import BytesIO
from PIL import Image
from fastapi import UploadFile, HTTPException, status


def process_avatar(file: UploadFile) -> bytes:
    """
    1. Validates the format.
    2. Cuts to a square.
    3. Resize to 256x256.
    4. Converts to WebP (light format).
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, or WebP images are allowed",
        )

    try:
        image = Image.open(file.file)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        width, height = image.size
        new_size = min(width, height)
        left = (width - new_size) / 2
        top = (height - new_size) / 2
        right = (width + new_size) / 2
        bottom = (height + new_size) / 2
        image = image.crop((left, top, right, bottom))

        image = image.resize((256, 256), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        image.save(buffer, format="WEBP", quality=85, optimize=True)
        buffer.seek(0)

        return buffer.getvalue()

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file"
        )
