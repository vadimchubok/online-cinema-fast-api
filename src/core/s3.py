import aioboto3
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


class S3Client:
    def __init__(self):
        self.session = aioboto3.Session()
        self.config = {
            "endpoint_url": settings.MINIO_ENDPOINT,
            "aws_access_key_id": settings.MINIO_ROOT_USER,
            "aws_secret_access_key": settings.MINIO_ROOT_PASSWORD,
            "region_name": settings.AWS_REGION,
        }
        self.bucket = settings.MINIO_BUCKET_NAME

    async def upload_file(self, file_obj, object_name: str):
        """
        Asynchronous file upload to MinIO/S3
        file_obj: can be a file-like object (from FastAPI UploadFile)
        object_name: the name of the file in the storage ('avatars/user_1.png')
        """
        async with self.session.client("s3", **self.config) as s3:
            try:
                await s3.upload_fileobj(file_obj, self.bucket, object_name)

                # Generate a public link.
                # IMPORTANT: If the project is in production, this will be the domain.
                # For local development, Dev 1 can replace 'minio' with 'localhost' in the MINIO_ENDPOINT.
                return f"{self.bucket}/{object_name}"
            except Exception as e:
                print(f"S3 Upload Error: {e}")
                return None

    async def delete_file(self, object_name: str):
        """Deleting a file from storage"""
        async with self.session.client("s3", **self.config) as s3:
            try:
                await s3.delete_object(Bucket=self.bucket, Key=object_name)
                return True
            except Exception as e:
                print(f"S3 Delete Error: {e}")
                return False


s3_client = S3Client()
