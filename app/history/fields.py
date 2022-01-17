import io

from PIL.Image import Image
from tortoise import fields

from app.configuration import MEDIA_URL


class ImageField(fields.TextField):
    pass
