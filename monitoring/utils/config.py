# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django.conf import settings  # noqa
from monitoring.config import local_settings

def get_config(name, default):
    value = getattr(settings, name, None)
    if value is not None:
        return value
    return getattr(local_settings, name, default)
