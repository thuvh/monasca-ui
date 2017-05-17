# Copyright 2017 Fujitsu LIMITED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib

from django.conf import settings
from django.contrib.messages import api as msg_api
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon.utils import memoized

from openstack_dashboard.api import base
from oslo_log import log as logging

from monascaclient import client as mon_client
from monascaclient import exc
from monitoring.config import local_settings as settings

LOG = logging.getLogger(__name__)

INSECURE = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
CACERT = getattr(settings, 'OPENSTACK_SSL_CACERT', None)

KEYSTONE_SERVICE = 'identity'
MONITORING_SERVICE = getattr(settings, 'MONITORING_SERVICE_TYPE', 'monitoring')

VERSIONS = base.APIVersionManager(MONITORING_SERVICE, preferred_version=2.0)
VERSIONS.load_supported_version(2.0, {'client': mon_client, 'version': '2_0'})


def _handle_message(request, message):
    def horizon_message_already_queued(_message):
        _message = force_text(_message)
        if request.is_ajax():
            for tag, msg, extra in request.horizon['async_messages']:
                if _message == msg:
                    return True
        else:
            for msg in msg_api.get_messages(request):
                if msg.message == _message:
                    return True
        return False

    if horizon_message_already_queued(message):
        exceptions.handle(request, ignore=True)
    else:
        exceptions.handle(request, message=message)


@contextlib.contextmanager
def handled_exceptions(request):
    """Handles all monasca-api specific exceptions."""
    try:
        yield
    except exc.ConnectionError:
        msg = _('Unable to communicate to monasca-api server.')
        LOG.exception(msg)
        _handle_message(request, msg)
    except exc.Unauthorized:
        msg = _('Check Keystone configuration of monasca-api server.')
        LOG.exception(msg)
        _handle_message(request, msg)
    except exc.Forbidden:
        msg = _('Operation is forbidden by monasca-api server.')
        LOG.exception(msg)
        _handle_message(request, msg)
    except exc.NotFound:
        msg = _('Requested object is not found on monasca server.')
        LOG.exception(msg)
        _handle_message(request, msg)
    except exc.Conflict:
        msg = _('Requested operation conflicts with an existing object.')
        LOG.exception(msg)
        _handle_message(request, msg)
    except exc.BadRequest as e:
        msg = _('The request data is not acceptable by the server')
        LOG.exception(msg)
        reason = getattr(e, 'details', '')
        if not reason:
            reason = msg
        _handle_message(request, reason)
    except exc.InternalServerError as e:
        msg = _("There was an error communicating with server")
        LOG.exception(msg)
        reason = getattr(e, 'details', '')
        if not reason:
            reason = msg
        _handle_message(request, reason)


def _get_endpoint(request):
    try:
        endpoint = base.url_for(request,
                                service_type=settings.MONITORING_SERVICE_TYPE,
                                endpoint_type=settings.MONITORING_ENDPOINT_TYPE)
    except exceptions.ServiceCatalogException:
        endpoint = 'http://127.0.0.1:8070/v2.0'
        LOG.warning('Monasca API location could not be found in Service '
                    'Catalog, using default: {0}'.format(endpoint))
    return endpoint


def get_auth_params_from_request(request):
    """Extracts the properties from the request object needed by the monascaclient
    call below. These will be used to memoize the calls to monascaclient
    """
    LOG.debug('Extracting intel from request')
    return (
        request.user.username,
        request.user.user_domain_id,
        request.user.user_domain_name,
        request.user.token.id,
        request.user.tenant_id,
        request.user.token.project.get('domain_id'),
        base.url_for(request, MONITORING_SERVICE),
        base.url_for(request, KEYSTONE_SERVICE)
    )


@memoized.memoized_with_request(get_auth_params_from_request)
def monascaclient(request_auth_params, version=None):
    (
        username,
        user_domain_id,
        user_domain_name,
        token_id,
        project_id,
        project_domain_id,
        monasca_url,
        auth_url
    ) = request_auth_params

    if not version:
        version = VERSIONS.get_active_version()['version']

    LOG.debug('Monasca::Client <Url: {0}>'.format(monasca_url))

    c = mon_client.Client(api_version=version,
                          username=username,
                          user_domain_id=user_domain_id,
                          user_domain_name=user_domain_name,
                          token=token_id,
                          project_id=project_id,
                          project_domain_id=project_domain_id,
                          insecure=INSECURE,
                          cert=CACERT,
                          auth_url=auth_url,
                          endpoint=monasca_url)
    return c
