# Copyright 2018 OP5 AB
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from mock import Mock
from mock import patch

from monitoring.test import helpers
from monitoring.api.client import _get_auth_params_from_request


def _mock_url_for(request, service_name):
    return getattr(request, service_name)


class ApiTest(helpers.TestCase):
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
