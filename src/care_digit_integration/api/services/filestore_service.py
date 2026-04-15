from urllib.parse import urljoin
import logging

import requests

from care_digit_integration.api.services.token_service import TokenService
from care_digit_integration.settings import plugin_settings as settings

logger = logging.getLogger(__name__)


class FileStoreService:
    def __init__(self):
        self.token_service = TokenService()


    def upload_files(self, *, files, tenant_id):
        try:
            url = urljoin(settings.HOST, settings.FILESTORE_UPLOAD_ENDPOINT)

            headers = {
                'accept': 'application/json, text/plain, */*',
                'auth-token': self.token_service.get_token(tenant_id=tenant_id),
            }

            multipart_files = []

            for key in files:
                for f in files.getlist(key):
                    multipart_files.append(
                        ("file", (f.name, f, f.content_type))
                    )

            payload = {
                "tenantId": tenant_id,
                "module": settings.MODULE_NAME
            }

            response = requests.post(
                url=url,
                headers=headers,
                data=payload,
                files=multipart_files,
                timeout=settings.REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise
