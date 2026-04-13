from django.core.cache import cache

import logging
import requests
import time
from urllib.parse import urlencode, urljoin

from care_digit_integration.settings import plugin_settings as settings

logger = logging.getLogger(__name__)


class TokenService:

    def _get_cache_key(self, tenant_id):
        return f"access_token:{tenant_id}"



    def _fetch_token(self, tenant_id):
        url = urljoin(settings.HOST, settings.DIGIT_TOKEN_ENDPOINT)

        headers = {
            'accept': 'application/json, text/plain, */*',
            'authorization': 'Basic ZWdvdi11c2VyLWNsaWVudDo=',
            'content-type': 'application/x-www-form-urlencoded'
        }

        payload = urlencode({
            "username": settings.USERNAME,
            "password": settings.PASSWORD,
            "grant_type": settings.GRANT_TYPE,
            "scope": "read",
            "tenantId": tenant_id,
            "userType": settings.USER_TYPE,
        })

        response = requests.post(url=url, headers=headers, data=payload, timeout=10)

        if response.status_code != 200:
            raise Exception(f"Token API failed: {response.text}")

        return response.json().get("access_token")



    def get_token(self, tenant_id):
        cache_key = self._get_cache_key(tenant_id)

        token = cache.get(cache_key)
        if token:
            return token

        lock_key = f"lock:{cache_key}"

        if cache.add(lock_key, "1", timeout=10):
            try:
                token = self._fetch_token(tenant_id)

                cache.set(
                    cache_key,
                    token,
                    timeout=settings.TOKEN_EXPIRY - 60
                )

                return token

            finally:
                cache.delete(lock_key)


        for _ in range(5):
            token = cache.get(cache_key)
            if token:
                return token
            time.sleep(0.2)

        token = self._fetch_token(tenant_id)

        cache.set(
            cache_key,
            token,
            timeout=settings.TOKEN_EXPIRY - 60
        )

        return token
