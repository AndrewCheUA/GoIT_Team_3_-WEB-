from pydantic import utils, root_validator

from .core import CoreModel, IDModelMixin, DateTimeModelMixin
from app.services.cloudinary import formatting_image


class ImageBase(CoreModel):
    """
    Leaving salt from base model
    """
    url: str
    description: str
    user_id: int

    @root_validator(pre=True)
    def update_model(cls, values: utils.GetterDict):
        if 'url' not in values.keys():
            values._obj.url = cls.format_url(values._obj.public_id)  # noqa
        return values

    @staticmethod
    def format_url(public_id: str):
        return formatting_image(public_id)['url']


class ImagePublic(DateTimeModelMixin, ImageBase, IDModelMixin):
    class Config:
        orm_mode = True


class ImageCreateResponse(CoreModel):
    image: ImagePublic
    detail: str = "Image successfully uploaded"
