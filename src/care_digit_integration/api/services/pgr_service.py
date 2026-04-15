from urllib.parse import urljoin
import logging
import time

import requests

from care.utils.shortcuts import get_object_or_404
from care.facility.models import Facility


from care_digit_integration.api.services.token_service import TokenService
from care_digit_integration.models.digit_complaint_types import DigitComplaintTypes
from care_digit_integration.settings import plugin_settings as settings


logger = logging.getLogger(__name__)


class PGRService:
    def __init__(self):
        self.token_service = TokenService()


    def _get_tenant_id(self, facility_id, workflow):
        facility = get_object_or_404(Facility, external_id=facility_id)

        digit_complaint_type = get_object_or_404(
            DigitComplaintTypes,
            facility=facility,
            workflow=workflow
        )

        return digit_complaint_type.tenant_id



    def _build_create_payload(self, *, tenant_id, service_code, description):
        access_token = self.token_service.get_token(tenant_id=tenant_id)
        user_info = settings.USER_INFO
        timestamp = int(time.time())

        payload = {
            "service": {
                "active": True,
                "tenantId": tenant_id,
                "serviceCode": service_code,
                "description": description,
                "applicationStatus": "CREATED",
                "source": "web",
                "user": {
                    "userName": user_info["USER_NAME"],
                    "name": user_info["NAME"],
                    "type": user_info["TYPE"],
                    "mobileNumber": user_info["MOBILE_NUMBER"],
                    "roles": user_info["ROLES"],
                    "tenantId": user_info["TENANT_ID"],
                    "uuid": user_info["UUID"],
                    "active": user_info["ACTIVE"],
                    "isDeleted": user_info["IS_DELETED"],
                    "rowVersion": user_info["ROW_VERSION"],
                    "auditDetails": {
                        "createdBy": user_info["UUID"],
                        "createdTime": timestamp,
                        "lastModifiedBy": user_info["UUID"],
                        "lastModifiedTime": timestamp
                    }
                },
                "isDeleted": False,
                "rowVersion": 1,
                "address": {
                    "landmark": "",
                    "buildingName": "",
                    "street": "",
                    "pincode": "",
                    "locality": {
                        "code": settings.LOCALITY_CODE
                    },
                    "geoLocation": {}
                },
                "additionalDetail": {
                    "supervisorName": user_info["NAME"],
                    "supervisorMobileNumber": ""
                },
                "auditDetails": {
                    "createdBy": user_info["UUID"],
                    "createdTime": timestamp,
                    "lastModifiedBy": user_info["UUID"],
                    "lastModifiedTime": timestamp
                }
            },
            "workflow": {
                "action": "CREATE",
                "assignes": [],
                "hrmsAssignes": [],
                "comments": ""
            },
            "RequestInfo": {
                "apiId": "Rainmaker",
                "authToken": access_token
            }
        }

        return payload




    def create_complaint(self, facility_id, workflow, service_code, description):
        try:
            tenant_id = self._get_tenant_id(facility_id, workflow)

            url = urljoin(settings.HOST, settings.PGR_CREATE_ENDPOINT)

            params = { "tenantId": tenant_id }

            headers = {
                'accept': 'application/json, text/plain, */*',
                'content-type': 'application/json;charset=UTF-8'
            }

            payload = self._build_create_payload(
                tenant_id=tenant_id,
                service_code=service_code,
                description=description
            )

            response = requests.post(
                url=url,
                params=params,
                headers=headers,
                json=payload,
                timeout=settings.REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise




    def fetch_complaint(self, *, pgr_ticket_id, facility_id, workflow):
        try:
            tenant_id = self._get_tenant_id(facility_id, workflow)

            url = urljoin(settings.HOST, settings.PGR_FETCH_ENDPOINT)

            params = {
                "tenantId": tenant_id,
                "serviceRequestId": pgr_ticket_id
            }

            headers = {
                'accept': 'application/json, text/plain, */*',
                'content-type': 'application/json;charset=UTF-8'
            }

            access_token = self.token_service.get_token(tenant_id=tenant_id)

            payload = {
                "RequestInfo": {
                    "apiId": "Rainmaker",
                    "authToken": access_token
                }
            }

            response = requests.post(
                url=url,
                params=params,
                headers=headers,
                json=payload,
                timeout=settings.REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise
