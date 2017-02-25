from certbot import interfaces, errors
from certbot.plugins import common
from certbot.display import util as display_util
import requests
import zope.interface
import logging
import copy

logger = logging.getLogger(__name__)


def _validate_not_blank(value):
    if len(value) <= 0:
        raise errors.PluginError("Option can not be blank")
    return value


@zope.interface.implementer(interfaces.IInstaller)
@zope.interface.provider(interfaces.IPluginFactory)
class Installer(common.Plugin):
    """
    Openshift Installer

    This plugin allows the automatically installing SSL Certs into an Openshift 3 Route.
    """
    description = 'Openshift 3 Installer'


    @classmethod
    def add_parser_arguments(cls, add):
        add("api-host", help="Hostname of the Openshift API")
        add("namespace", help="Route Namespace")
        add("token", help="Openshift Bearer Token")


    def __init__(self, *args, **kwargs):
        super(Installer, self).__init__(*args, **kwargs)
        self._api_host = self._get_api_host()
        self._namespace = self._get_namespace()
        self._token = self._get_token()
        self._enhance_func = {
            "redirect": self._enable_redirect,
        }
        self._changes = {}


    def prepare(self):
        """Verify that provided configuration is valid"""
        self._routes = self._list_routes()


    def more_info(self):
        return ("")


    def get_all_names(self):
        return [r['spec']['host'] for r in self._routes['items']]


    def deploy_cert(self, domain, cert_path, key_path, chain_path, fullchain_path):
        route = {}
        route['spec'] = {}
        route['spec']['tls'] = {
            'termination': 'edge',
            'certificate': open(cert_path).read() if cert_path else None,
            'key': open(key_path).read() if key_path else None,
            'caCertificate': open(chain_path).read() if chain_path else None,
        }
        self._checkin_route(domain, route)


    def enhance(self, domain, enhancement, options=None):
        try:
            return self._enhance_func[enhancement](domain, options)
        except (KeyError, ValueError):
            raise errors.PluginError("Unsupported enhancement: {0}".format(enhancement))
        except errors.PluginError:
            logger.warning("Failed %s for %s", enhancement, domain)
            raise


    def supported_enhancements(self):
        return ['redirect']


    def save(self, title=None, temporary=False):
        for domain, change in self._changes.items():
            names = [r['metadata']['name'] for r in self._routes['items'] if r['spec']['host'] == domain]
            if len(names) <= 0:
                raise errors.PluginError("Couldn't find route for domain: {0}".format(domain))
            for name in names:
                self._save_route(name, change)
                logger.info('Saved route {} for {}'.format(name, domain))
        self._changes = {}


    def rollback_checkpoints(self, rollback=1):
        pass


    def recovery_routine(self):
        pass


    def view_config_changes(self):
        pass


    def config_test(self):
        pass


    def restart(self):
        pass


    def _enable_redirect(self, domain, *args, **kwargs):
        route = {}
        route['spec'] = {}
        route['spec']['tls'] = {
            'insecureEdgeTerminationPolicy': 'Redirect',
        }
        self._checkin_route(domain, route)


    def _checkin_route(self, domain, route):
        self._changes[domain] = copy.deepcopy(route)


    def _get_route_detail_url(self, route_name):
        return 'https://{}/oapi/v1/namespaces/{}/routes/{}'.format(self._api_host, self._namespace, route_name)


    def _get_route_list_url(self):
        return 'https://{}/oapi/v1/namespaces/{}/routes'.format(self._api_host, self._namespace)


    def _list_routes(self):
        resp = requests.get(self._get_route_list_url(), headers=self._get_headers())
        try:
            resp.raise_for_status()
        except requests.RequestException as e:
            raise errors.PluginError('Encountered error while trying to fetch route details: {}'.format(e))
        return resp.json()


    def _save_route(self, route_name, route):
        data = copy.deepcopy(route)
        data['kind'] = 'Route'
        data['apiVersion'] = 'v1'

        headers = self._get_headers()
        headers['Content-Type'] = 'application/merge-patch+json'

        resp = requests.patch(self._get_route_detail_url(route_name), headers=headers, json=data)
        try:
            resp.raise_for_status()
        except requests.RequestException as e:
            raise errors.PluginError('Encountered error while trying to save route: {}'.format(e))
        return resp.json()


    def _get_headers(self):
        return {
            'Authorization': 'Bearer {}'.format(self._token)
        }


    def _get_api_host(self):
        return self._get_config('api-host', 'Openshift API host', _validate_not_blank)


    def _get_namespace(self):
        return self._get_config('namespace', 'route namespace', _validate_not_blank)


    def _get_token(self):
        return self._get_config('token', 'Openshift API bearer token', _validate_not_blank)


    def _get_config(self, option, name, validation_fn):
        value = self.conf(option)
        if not value:
            value = self._prompt_for_config("Input the {}".format(name), validation_fn)
        if not value:
            cli_flag = '--{0}'.format(self.option_name(option))
            raise errors.PluginError('Must provide {} with flag {}'.format(name, cli_flag))
        return validation_fn(value)


    def _prompt_for_config(self, prompt, validation_fn=lambda value: value):
        display = zope.component.getUtility(interfaces.IDisplay)
        while True:
            code, value = display.directory_select(prompt, force_interactive=True)
            if code == display_util.HELP:
                return None
            elif code == display_util.CANCEL:
                return None
            else:
                try:
                    return validation_fn(value)
                except errors.PluginError as error:
                    display.notification(str(error), pause=False)
