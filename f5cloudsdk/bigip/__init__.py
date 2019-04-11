"""Module for BIG-IP configuration

    Examples
    --------
    Example: Basic
    --------------
    from f5cloudsdk.bigip import ManagementClient

    device = ManagementClient('192.0.2.10', user='admin', password='admin')
    # get BIG-IP info (version, etc.)
    device.get_info()

    Example: Token Authentication
    -----------------------------
    device = ManagementClient('192.0.2.10', token='my_token')
"""

import json
import requests
from requests.auth import HTTPBasicAuth

import f5cloudsdk.constants as constants
from .decorators import check_auth

class ManagementClient(object):
    """A class used as a management client for BIG-IP

    Attributes
    ----------
    host : str
        the hostname of the device
    user : str, optional
        the username of the device
    password : str, optional
        the password of the device
    private_key : str, optional
        the private key of the device
    token : str, optional
        the token of the device

    Methods
    -------
    get_info()
        Refer to method documentation
    make_request()
        Refer to method documentation
    make_request_ssh()
        Refer to method documentation
    """

    def __init__(self, host, **kwargs):
        """Class initialization

        Parameters
        ----------
        host : str
            the hostname of the device
        **kwargs:
            optional keyword arguments

        Keyword Arguments
        -----------------
        user : str
            the username to assign to the user attribute
        password : str
            the password to assign to the password attribute
        private_key : str
            the private_key to assign to the private_key attribute
        token : str
            the token to assign to the token attribute

        Returns
        -------
        None
        """
        self.host = host
        self.user = kwargs.pop('user', '')
        self.password = kwargs.pop('password', '')
        self.private_key = kwargs.pop('private_key', '')
        self.token = kwargs.pop('token', None)

        if self.user and self.password:
            # run _login_using_credentials() to get token
            self._login_using_credentials()
        elif self.private_key:
            # create temporary user and run _login_using_credentials() to get token
            self._login_using_key()
        elif self.token:
            # token provided directly - TODO: how to refresh?
            pass
        else:
            raise Exception('user/password credentials, private key or token required')

    def _get_token(self):
        """Gets authentication token

        Parameters
        ----------
        None

        Returns
        -------
        str
            a valid authentication token
        """

        url = 'https://%s/mgmt/shared/authn/login' % (self.host)
        body = {
            'username': self.user,
            'password': self.password,
            'loginProviderName': 'tmos' # need to support other providers
        }
        response = requests.post(
            url,
            json=body,
            auth=HTTPBasicAuth(self.user, self.password),
            verify=False
        ).json()
        return response['token']['token']

    def _login_using_credentials(self):
        """Logs in to device using user/password

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.token = self._get_token()

    def _login_using_key(self):
        """Logs in to device using private key

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

    def get_info(self):
        """Gets device info

        Parameters
        ----------
        None

        Returns
        -------
        dict
            a dictionary containg version: {'version': 'x.x.x'}
        """
        uri = '/mgmt/tm/sys/version'
        response = self.make_request(uri)

        v_0 = 'https://localhost/mgmt/tm/sys/version/0'
        version = response['entries'][v_0]['nestedStats']['entries']['Version']['description']
        return {'version': version}

    @check_auth
    def make_request(self, uri, **kwargs):
        """Makes request to device (HTTP/S)

        Parameters
        ----------
        uri : str
            the URI where the request should be made
        **kwargs:
            optional keyword arguments

        Keyword Arguments
        -----------------
        method : str
            the HTTP method to use
        headers : str
            the HTTP headers to use
        body : str
            the HTTP body to use
        body_content_type : str
            the HTTP body content type to use

        Returns
        -------
        dict
            a dictionary containg the JSON response
        """

        host = self.host
        uri = uri
        method = kwargs.pop('method', 'GET').lower()
        headers = {'X-F5-Auth-Token': self.token, 'User-Agent': constants.USER_AGENT}
        # add any user-supplied headers, allow the user to override default headers
        headers.update(kwargs.pop('headers', {}))
        # check for body, normalize
        body = kwargs.pop('body', None)
        body_content_type = kwargs.pop('body_content_type', 'json') # json (default), raw
        if body and body_content_type == 'json':
            headers.update({'Content-Type': 'application/json'})
            body = json.dumps(body)

        # construct url
        url = 'https://%s%s' % (host, uri)
        # make request
        response = requests.request(
            method,
            url,
            headers=headers,
            data=body,
            verify=False
        )
        # check response code
        response.raise_for_status()

        return response.json()

    @check_auth
    def make_request_ssh(self):
        """Makes request to device (SSH)

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
