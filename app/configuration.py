import os
from pathlib import Path
import dotenv

dotenv.load_dotenv()

DATABASE_URL = 'DATABASE_URL'
TORTOISE_ORM = {
    'connections': {
        'default': os.environ.get(DATABASE_URL)
    },
    'apps': {
        'app': {
            'models': ['app.schedule.models', 'app.history.models', 'aerich.models'],
            'default_connection': 'default',
        }
    },
}
BASE_DIR = Path(__file__).parent.parent

STATIC_URL = BASE_DIR / 'static'
MEDIA_URL = STATIC_URL / 'media'
