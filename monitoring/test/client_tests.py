# Copyright 2018 OP5 AB
# (c) Copyright 2017-2018 SUSE LLC
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from django.conf import settings as d_settings
from django.test.utils import override_settings
from mock import Mock
from mock import patch

from monascaclient import client as mon_client

from monitoring.test import helpers
from monitoring.api.client import _get_auth_params_from_request
from monitoring.api.client import _get_to_verify


def _mock_url_for(request, service_name):
    return getattr(request, service_name)


def _mock_get_auth_params(request):
    return (923, '22', 789, 55, 'monitoring_url', 'identity_url')


def _mock_request():
    request = Mock()
    request.user.user_domain_id = 923
    request.user.token.id = '22'
    request.user.tenant_id = 789
    request.user.token.project = {'domain_id': 55}
    request.monitoring = 'monitoring_url'
    request.identity = 'identity_url'
    return request


def _mock_client_args(verify):
    return ('2_0', '22', 789, 55, 923, verify, 'auth_url', 'mon_url')


def _expected_session_args(verify):
    return {
        'auth_url': 'auth_url', 'user_domain_id': 55, 'project_id': 789,
        'token': '22', 'endpoint': 'mon_url', 'verify': verify,
        'project_domain_id': 923
    }


class ClientTests(helpers.TestCase):

    @override_settings(OPENSTACK_SSL_NO_VERIFY=False)
    @override_settings(OPENSTACK_SSL_CACERT='/etc/ssl/certs/some.crt')
    def test_ssl_verify_with_cert(self):
        insecure = getattr(d_settings, 'OPENSTACK_SSL_NO_VERIFY', False)
        cert = getattr(d_settings, 'OPENSTACK_SSL_CACERT', None)
        to_verify = _get_to_verify(insecure, cert)

        self.assertEqual(to_verify, '/etc/ssl/certs/some.crt')

    @override_settings(OPENSTACK_SSL_NO_VERIFY=True)
    def test_no_ssl_verify(self):
        insecure = getattr(d_settings, 'OPENSTACK_SSL_NO_VERIFY', False)
        cert = getattr(d_settings, 'OPENSTACK_SSL_CACERT', None)
        to_verify = _get_to_verify(insecure, cert)

        self.assertFalse(to_verify)

    def test_get_auth_params_from_request(self):
        mock_request = _mock_request()
        with patch('openstack_dashboard.api.base.url_for',
                   side_effect=_mock_url_for):
            auth_params = _get_auth_params_from_request(mock_request)

        self.assertEqual(
            auth_params,
            (923, '22', 789, 55, 'monitoring_url', 'identity_url'))

    @patch('monascaclient.client._session')
    def test_client_no_verify(self, mock_session):
        (
            version,
            token,
            project_id,
            user_domain_id,
            project_domain_id,
            verify,
            auth_url,
            endpoint
        ) = _mock_client_args(False)

        the_client = mon_client.Client(
            api_version=version,
            token=token,
            project_id=project_id,
            user_domain_id=user_domain_id,
            project_domain_id=project_domain_id,
            verify=verify,
            auth_url=auth_url,
            endpoint=endpoint
        )

        self.assertIsNotNone(the_client)
        mock_session.assert_called_with(_expected_session_args(False))

    @patch('monascaclient.client._session')
    def test_client_verify(self, mock_session):
        cert = '/etc/ssl/certs/some.crt'
        (
            version,
            token,
            project_id,
            user_domain_id,
            project_domain_id,
            verify,
            auth_url,
            endpoint
        ) = _mock_client_args(cert)

        the_client = mon_client.Client(
            api_version=version,
            token=token,
            project_id=project_id,
            user_domain_id=user_domain_id,
            project_domain_id=project_domain_id,
            verify=verify,
            auth_url=auth_url,
            endpoint=endpoint
        )

        self.assertIsNotNone(the_client)
        mock_session.assert_called_with(_expected_session_args(cert))
