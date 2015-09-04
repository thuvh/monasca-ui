# coding=utf-8
from django.core import urlresolvers
from django.test import RequestFactory
from mock import patch, call  # noqa

from monitoring.test import helpers
from monitoring.overview import constants
from monitoring.overview import views


INDEX_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'index')


class OverviewTest(helpers.TestCase):
    def test_index_get(self):
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'monitoring/overview/index.html')
        self.assertTemplateUsed(res, 'monitoring/overview/monitor.html')


class KibanaProxyViewTest(helpers.TestCase):

    def setUp(self):
        super(KibanaProxyViewTest, self).setUp()
        self.view = views.KibanaProxyView()
        self.request_factory = RequestFactory()

    def test_get_relative_url_with_unicode(self):
        """Tests if it properly converts multibyte characters"""
        self.view.request = self.request_factory.get(
            '/', data={'a': 1, 'b': 2}
        )
        expected = ('/elasticsearch/.kibana/search'
                    '/New-Saved-Search%E3%81%82')

        actual = self.view.get_relative_url(
            u'/elasticsearch/.kibana/search/New-Saved-Searchあ'
        )
        # order of query params may change
        # and we don't care about it - throw it away
        actual = actual.split('?')[0]

        self.assertEqual(actual, expected)
