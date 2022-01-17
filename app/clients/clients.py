import io
import os
import re
import typing

import httpx
from httpx import codes
from PIL import Image

from app import consts


class BaseClient:
    URL_ROOT: str
    TOKEN_NAME: str

    def __init__(self, token: str = None):
        self.token = token or os.environ.get(self.TOKEN_NAME)

    def get_full_path(self, path: str):
        return '{}{}'.format(self.URL_ROOT, path)

    @staticmethod
    async def make_get(path: str, params: [str], **client_settings) -> httpx.Response:
        async with httpx.AsyncClient(**client_settings) as client:
            response = await client.get(path, params)
        return response

    async def make_post(self, path: str,
                        params: list[str] = None,
                        data: dict = None,
                        files: list[tuple[str, Image]] = None,
                        **client_settings):
        async with httpx.AsyncClient(**client_settings) as client:
            response = await client.post(path, data=data, files=files, params=params)
        return response


class PlantNetClient(BaseClient):
    URL_ROOT: typing.Final = 'https://my-api.plantnet.org/v2/'
    TOKEN_NAME = consts.PLANT_NET_API_KEY

    async def send_recognize_request(self, image: Image):
        path = self.get_full_path('identify/all')
        params = self.get_request_params()
        data = {'organs': ['leaf']}
        files = [('images', image)]
        response: httpx.Response = await self.make_post(path, params, data, files)
        response.raise_for_status()
        return response.json()

    def get_request_params(self, params: dict = None):
        params = params or dict()
        params.update({
            'api-key': self.token,
            'lang': 'ru',
            'include-related-images': True}
        )
        return list(params.items())

    @staticmethod
    async def parse_response(json: dict, buffer: io.BytesIO, offset: int = 0):
        data = json.get('results')
        text = PlantNetClient.get_species(data, offset)
        image = await PlantNetClient.get_image(data, buffer, offset)
        return image, text

    @staticmethod
    def get_species(data: dict, offset: int) -> str:
        species = data[offset]['species']
        name_key = 'scientificNameWithoutAuthor'
        result = f'Название: {species[name_key]}.'
        common_name = ', '.join(species['commonNames'])
        if common_name:
            result = f'{result}\nБолее известен как {common_name}'
        return result

    @staticmethod
    async def get_image(data, buffer: io.BytesIO, offset: int):
        url = data[offset]['images'][0]['url']['m']
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        pos = buffer.tell()
        buffer.write(response.content)
        buffer.seek(pos)
        return buffer

    @staticmethod
    def validate_images(*img_urls):
        pattern = r'^\S*.(jpg|png)$'
        for img_url in img_urls:
            if not re.match(img_url, pattern):
                raise ValueError
        return True
