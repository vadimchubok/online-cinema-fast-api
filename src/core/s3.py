import aioboto3
from fastapi import HTTPException, status
from src.core.config import settings

"""
GUIDE FOR INTEGRATING S3 CLIENT FOR USER AVATARS

1. Import the client:
   from src.core.s3 import s3_client

2. Usage in a FastAPI Router:
   @router.post("/profile/avatar")
   async def update_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
       # Define a unique path, e.g., 'avatars/user_1.png'
       file_path = f"avatars/user_{current_user.id}.{file.filename.split('.')[-1]}"

       # Upload to MinIO/S3
       # result will be: "avatars/user_1.png" (the relative path in the bucket)
       path_in_bucket = await s3_client.upload_file(file.file, file_path)

       if path_in_bucket:
           # Save path_in_bucket to UserProfileModel.avatar in your DB
           current_user.profile.avatar = path_in_bucket
           ...

3. Deleting an old avatar:
   if current_user.profile.avatar:
       await s3_client.delete_file(current_user.profile.avatar)

Note: The database stores ONLY the relative path. 
Front-end should prepend the MinIO endpoint (e.g., http://localhost:9000/avatars/...) to display the image.
"""


class S3Service:
    def __init__(self):
        self.session = aioboto3.Session()
        self.config = {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "region_name": settings.AWS_REGION,
        }
        self.bucket_name = settings.S3_BUCKET_NAME

    async def upload_file(
        self, file_data: bytes, object_name: str, content_type: str
    ) -> str:
        try:
            async with self.session.client("s3", **self.config) as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=file_data,
                    ContentType=content_type,
                )
            return object_name
        except Exception as e:
            print(f"S3 Upload Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error uploading file to storage",
            )

    async def delete_file(self, object_name: str):
        try:
            async with self.session.client("s3", **self.config) as client:
                await client.delete_object(Bucket=self.bucket_name, Key=object_name)
        except Exception as e:
            print(f"S3 Delete Error: {e}")

    async def generate_presigned_url(
        self, object_name: str, expiration: int = 3600
    ) -> str:
        try:
            async with self.session.client("s3", **self.config) as client:
                response = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": object_name},
                    ExpiresIn=expiration,
                )
            return response
        except Exception as e:
            print(f"S3 Presign Error: {e}")
            return ""


s3_client = S3Service()
