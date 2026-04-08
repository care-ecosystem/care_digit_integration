from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

PLUGIN_NAME = "care_digit_integration"


class CareDigitIntegrationConfig(AppConfig):
    name = PLUGIN_NAME
    verbose_name = _("Care digit integration")

    def ready(self):
        import care_digit_integration.signals  # noqa F401
