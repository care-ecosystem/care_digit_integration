from django.core.cache import cache

import requests
import time
from urllib.parse import urlencode, urljoin

from care_digit_integration.settings import plugin_settings as settings

import logging
logger = logging.getLogger(__name__)


class TokenService:

    def _get_cache_key(self, tenant_id):
        return f"digit:access_token:{tenant_id}"



    def _cache_data(self, cache_key, token_response):
        token = token_response.get("access_token")
        user_info = token_response.get("UserRequest")

        if not token:
            raise Exception("Access token missing in response")

        data = {
            "access_token": token,
            "user_info": user_info
        }

        cache.set(
            cache_key,
            data,
            timeout=max(settings.TOKEN_EXPIRY - 60, 1)
        )



    def _fetch_token(self, tenant_id):
        try:
            url = urljoin(settings.HOST, settings.DIGIT_TOKEN_ENDPOINT)

            headers = {
                'accept': 'application/json, text/plain, */*',
                'authorization': f'Basic {settings.DIGIT_HEADER_AUTH_TOKEN}',
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

            response = requests.post(
                url=url,
                headers=headers,
                data=payload,
                timeout=settings.REQUEST_TIMEOUT
            )

            return response.json()

        except Exception as e:
            logger.error(e)
            logger.error(response.status)
            logger.error(response.text)

            raise e


    def get_token(self, tenant_id):
        logger.info("Inside get_token()")
        cache_key = self._get_cache_key(tenant_id)

        data = cache.get(cache_key)
        if data:
            logger.info("Data exists")
            logger.info(data)
            return data.get("access_token")

        lock_key = f"lock:{cache_key}"

        if cache.add(lock_key, "1", timeout=settings.REQUEST_TIMEOUT):
            try:
                logger.info("Inside lock")
                response = self._fetch_token(tenant_id)
                logger.info(response)

                self._cache_data(
                    cache_key=cache_key,
                    token_response=response
                )


                return response.get("access_token")
            except Exception as e:
                logger.error(e)
            finally:
                cache.delete(lock_key)


        logger.info("Outside lock")
        for _ in range(5):
            data = cache.get(cache_key)
            if data:
                return data.get("access_token")
            time.sleep(0.2)

        response = self._fetch_token(tenant_id)
        logger.info(response)

        self._cache_data(
            cache_key=cache_key,
            token_response=response
        )

        return response.get("access_token")



    def get_user_info(self, tenant_id):
        cache_key = self._get_cache_key(tenant_id)
        data = cache.get(cache_key)

        if data:
            return data.get("user_info")

        raise Exception("DIGIT user information not found")
