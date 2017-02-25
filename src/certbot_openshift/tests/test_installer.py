import unittest
import mock
import requests_mock


class AuthenticatorTest(unittest.TestCase):
    def setUp(self):
        self.config = mock.MagicMock(
            openshift_api_host='api.example.com',
            openshift_namespace='my-project',
            openshift_token='ABCDEF42',
            noninteractive_mode=True)

        from certbot_openshift.installer import Installer
        self.installer = Installer(self.config, name='openshift')


    def test_get_all_names(self):
        with requests_mock.mock() as m:
            data = {
                'items': [
                    {
                        'spec': {
                            'host': 'foo.example.com'
                        }
                    },
                    {
                        'spec': {
                            'host': 'bar.example.com'
                        }
                    }
                ]
            }
            m.get('https://api.example.com/oapi/v1/namespaces/my-project/routes',
                json=data,
                status_code=200)
            self.installer.prepare()
            self.assertEqual(self.installer.get_all_names(), ['foo.example.com', 'bar.example.com'])
