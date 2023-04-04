import asyncio

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connect import get_db
from app.database.models import User
from app.repository import images as repository_images
from app.schemas.image import (
    ImageCreateResponse,
    ImagePublic,
)
from app.services import cloudinary
from app.services.auth import auth_service


router = APIRouter(prefix="/images", tags=["images"])


@router.post(
    "/", response_model=ImageCreateResponse, response_model_by_alias=False, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def upload_image(file: UploadFile = File(), description: str = Form(min_length=10, max_length=1200),
                       db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user)):
    """
    The upload_image function is used to upload an image to the cloudinary server.
    The function takes in a file, description and database session as parameters.
    It then uses the cloudinary library to upload the image and returns a response with
    the uploaded image's id.

    :param file: UploadFile: Get the file from the request body
    :param description: str: Get the description of the image from the request body
    :param db: AsyncSession: Get the database session
    :param current_user: User: Get the user id of the current logged in user
    :return: A dict with the following keys:
    """
    loop = asyncio.get_event_loop()
    image = await loop.run_in_executor(None, cloudinary.upload_image, file.file)

    if image is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid image file")

    image = await repository_images.create_image(current_user.id, description.strip(), image['public_id'], db)

    return {"image": image, "detail": "Image successfully uploaded"}


@router.get("/{image_id}", response_model=ImagePublic, dependencies=[Depends(RateLimiter(times=10, seconds=10))])
async def get_image(image_id: int, current_user: User = Depends(auth_service.get_current_user),
                    db: AsyncSession = Depends(get_db)):
    """
    The get_image function returns an image by its id.

    :param image_id: int: Get the image id from the url
    :param current_user: User: Get the current user from the database
    :param db: AsyncSession: Pass the database session to the function
    :return: The image object
    """
    image = await repository_images.get_image_by_id(current_user.id, image_id, db)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found image")

    return image
