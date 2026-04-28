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



    def _build_create_payload(
        self, *,
        tenant_id,
        service_code,
        description,
        filestore_uploads=[],
        source=None
    ):
        access_token = self.token_service.get_token(tenant_id=tenant_id)
        # user_info = settings.USER_INFO
        user_info = self.token_service.get_user_info(tenant_id=tenant_id)
        timestamp = int(time.time())

        audit_details = {
            # "createdBy": user_info["UUID"],
            "createdBy": user_info["uuid"],
            "createdTime": timestamp,
            # "lastModifiedBy": user_info["UUID"],
            "lastModifiedBy": user_info["uuid"],
            "lastModifiedTime": timestamp
        }

        verfication_documents = []
        for upload in filestore_uploads:
            verfication_documents.append({
                "fileStoreId": upload["fileStoreId"],
                "tenantId": upload["tenantId"],
                "auditDetails": audit_details
            })

        payload = {
            "service": {
                "active": True,
                "tenantId": tenant_id,
                "serviceCode": service_code,
                "description": description,
                "applicationStatus": settings.PGR_CREATE_APPLICATION_STATUS,
                "source": source or "web",
                "user": {
                    # "userName": user_info["USER_NAME"],
                    "userName": user_info["userName"],
                    # "name": user_info["NAME"],
                    "name": user_info["name"],
                    # "type": user_info["TYPE"],
                    "type": user_info["type"],
                    # "mobileNumber": user_info["MOBILE_NUMBER"],
                    "mobileNumber": user_info["mobileNumber"],
                    # "roles": user_info["ROLES"],
                    "roles": user_info["roles"],
                    # "tenantId": user_info["TENANT_ID"],
                    "tenantId": user_info["tenantId"],
                    # "uuid": user_info["UUID"],
                    "uuid": user_info["uuid"],
                    # "active": user_info["ACTIVE"],
                    "active": user_info["active"],
                    # "isDeleted": user_info["IS_DELETED"],
                    "isDeleted": False,
                    # "rowVersion": user_info["ROW_VERSION"],
                    "rowVersion": 1,
                    "auditDetails": audit_details
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
                    # "supervisorName": user_info["NAME"],
                    "supervisorName": user_info["name"],
                    # "supervisorMobileNumber": ""
                    "supervisorMobileNumber": user_info["mobileNumber"]
                },
                "auditDetails": audit_details
            },
            "workflow": {
                # "action": "CREATE",
                "action": "APPLY",
                "assignes": [],
                "hrmsAssignes": [],
                "comments": "",
                "verificationDocuments": verfication_documents
            },
            "RequestInfo": {
                "apiId": "Rainmaker",
                "authToken": access_token
            }
        }

        return payload




    def create_complaint(
        self,
        facility_id,
        workflow,
        service_code,
        description,
        filestore_uploads=[],
        source=None
    ):
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
                description=description,
                source=source,
                filestore_uploads=filestore_uploads
            )

            logger.info(payload)

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
            logger.error(e)
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
