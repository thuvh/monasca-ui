# Copyright 2018 OP5 AB
# (c) Copyright 2017-2018 SUSE LLC

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

from django.test.utils import override_settings
from mock import Mock
from mock import patch

from monitoring.test import helpers
from monitoring.api.client import _get_auth_params_from_request
from monitoring.api.client import _get_to_verify


def _mock_url_for(request, service_name):
    return getattr(request, service_name)


class ClientTests(helpers.TestCase):

    def test_ssl_verify_with_cert(self):
        to_verify = _get_to_verify()
        self.assertEqual(to_verify, '/etc/ssl/certs/some.crt')

    @override_settings(OPENSTACK_SSL_NO_VERIFY=True)
    def test_no_ssl_verify(self):
        to_verify = _get_to_verify()
        self.assertFalse(to_verify)

    def test_get_auth_params_from_request(self):
        request = Mock()
        request.user.user_domain_id = 923
        request.user.token.id = '22'
        request.user.tenant_id = 789
        request.user.token.project = {'domain_id': 55}
        request.monitoring = 'monitoring_url'
        request.identity = 'identity_url'
        with patch('openstack_dashboard.api.base.url_for',
                   side_effect=_mock_url_for):
            auth_params = _get_auth_params_from_request(request)

        self.assertEqual(
            auth_params,
            (923, '22', 789, 55, 'monitoring_url', 'identity_url'))
