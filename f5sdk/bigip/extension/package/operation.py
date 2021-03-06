"""Module for BIG-IP extension component package configuration"""

import os
import re
import time

from f5sdk import constants
from f5sdk.utils import http_utils, misc_utils

PKG_MGMT_URI = '/mgmt/shared/iapp/package-management-tasks'


class OperationClient(object):
    """A class used as a extension package operation client for BIG-IP

    Attributes
    ----------
    component : str
        the extension component
    version : str
        the extension component version

    Methods
    -------
    is_installed()
        Refer to method documentation
    install()
        Refer to method documentation
    uninstall()
        Refer to method documentation
    """

    def __init__(self, client, component, version, metadata_client, **kwargs):
        """Class initialization

        Parameters
        ----------
        client : instance
            the management client instance
        component : str
            the extension component
        version : str
            the extension component version
        metadata_client : instance
            the extension metadata client instance
        **kwargs :
            optional keyword arguments

        Keyword Arguments
        -----------------
        logger : instance
            the logger instance to use

        Returns
        -------
        None
        """

        self.logger = kwargs.pop('logger', None)

        self._client = client
        self._metadata_client = metadata_client
        self.component = component
        self.version = version

    def _upload_rpm(self, file_name, **kwargs):
        """Uploads a local RPM file to a remote device

        Parameters
        ----------
        file_name : str
            the name of the local file to upload
        **kwargs :
            optional keyword arguments

        Keyword Arguments
        -----------------
        delete_file : bool
            flag to delete local file when upload is complete

        Returns
        -------
        None
        """

        delete_file = kwargs.pop('delete_file', True)
        uri = '/mgmt/shared/file-transfer/uploads/%s' % (file_name.split('/')[-1])

        file_object = open(file_name, 'rb')
        max_chunk = 1024 * 1024
        file_size = len(file_object.read())
        file_object.seek(0)  # move to start
        start_index = 0
        while True:
            file_slice = file_object.read(max_chunk)
            if not file_slice:
                break

            slice_size = len(file_slice)
            if slice_size < max_chunk:
                end = file_size
            else:
                end = start_index + slice_size

            headers = {
                'Content-Range': '%s-%s/%s' % (start_index, end - 1, file_size),
                'Content-Length': str(end),
                'Content-Type': 'application/octet-stream'
            }
            # send chunk
            self._client.make_request(
                uri,
                method='POST',
                headers=headers,
                body=file_slice,
                body_content_type='raw'
            )
            start_index += slice_size

        if delete_file:
            os.remove(file_name)

    def _check_rpm_task_status(self, task_id):
        """Checks RPM task status on a remote device

        Parameters
        ----------
        task_id : str
            the task id to query

        Returns
        -------
        dict
            a dictionary containing the JSON response
        """

        status_link_uri = '%s/%s' % (PKG_MGMT_URI, task_id)
        sleep_secs = 1
        count = 0
        max_count = 120  # max_count + sleep_secs = 2 mins
        while True:
            response = self._client.make_request(status_link_uri)
            if response['status'] == 'FINISHED':
                break
            elif response['status'] == 'FAILED':
                raise Exception(response['errorMessage'])
            elif count > max_count:
                raise Exception('Max count exceeded')
            time.sleep(sleep_secs)
            count += 1
        return response

    def _install_rpm(self, package_path):
        """Installs RPM on a remote device

        Parameters
        ----------
        package_path : str
            the path to the package on the remote device to install

        Returns
        -------
        None
        """

        uri = PKG_MGMT_URI
        body = {
            'operation': 'INSTALL',
            'packageFilePath': package_path
        }
        response = self._client.make_request(uri, method='POST', body=body)

        # now check for task status completion
        self._check_rpm_task_status(response['id'])

    def install(self):
        """Installs extension package component on a remote device

        Parameters
        ----------
        None

        Returns
        -------
        dict
            a dictionary containing component and version:
            {
              'component': 'as3',
              'version': 'x.x.x'
            }
        """

        # download package (rpm) locally, upload to BIG-IP, install on BIG-IP
        download_url = self._metadata_client.get_download_url()
        download_pkg = download_url.split('/')[-1]
        tmp_file = '%s/%s' % (constants.TMP_DIR, download_pkg)
        # download
        http_utils.download_to_file(download_url, tmp_file)
        # upload
        self._upload_rpm(tmp_file)
        # install
        tmp_file_bigip_path = '/var/config/rest/downloads/%s' % (download_pkg)
        self._install_rpm(tmp_file_bigip_path)
        return {'component': self.component, 'version': self.version}

    def _uninstall_rpm(self, package_name):
        """Uninstalls RPM (LX extension) on a remote device

        Parameters
        ----------
        package_name : str
            the name of the installed package

        Returns
        -------
        None
        """

        uri = PKG_MGMT_URI
        body = {
            'operation': 'UNINSTALL',
            'packageName': package_name
        }
        response = self._client.make_request(uri, method='POST', body=body)
        # now check for task status completion
        self._check_rpm_task_status(response['id'])

    def _check_for_dependency(self):
        """Check for (existing) dependencies

        Notes
        -----

        Log a warning message for any dependencies

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        # check for component dependencies, if they exist validate dependency
        # exists for the current component version
        component_dependencies = self._metadata_client.get_component_dependencies()
        for name, dependency in component_dependencies.items():
            versions = dependency['versions']
            matches = [i for i in versions if misc_utils.compare_versions(
                self.version,
                i['version'],
                i['operation']
            )]
            # log warning if matching dependency is found
            if len(matches) == len(versions):
                msg = ('A component package dependency has not been removed: {}'
                       ' See documentation for more details: {}'
                       ).format(name, dependency['uninstallDocumentation'])
                self.logger.warning(msg)

    def uninstall(self):
        """Uninstalls extension package component on a remote device

        Parameters
        ----------
        None

        Returns
        -------
        dict
            a dictionary containing component and version:
            {
              'component': 'as3',
              'version': 'x.x.x'
            }
        """

        # uninstall from BIG-IP
        package_name = self._metadata_client.get_package_name()
        self._uninstall_rpm(package_name)

        # check for any component dependencies, log warning as needed
        self._check_for_dependency()

        return {'component': self.component, 'version': self.version}

    def _check_rpm_exists(self, component_package_name):
        """Checks RPM (LX extension) exists on a remote device

        Parameters
        ----------
        component_package_name : str
            the name of the installed package

        Returns
        -------
        str
            RPM version, or empty string if it does not exist
        """

        uri = PKG_MGMT_URI
        body = {
            'operation': 'QUERY'
        }
        response = self._client.make_request(uri, method='POST', body=body)

        # now check for task status completion
        response = self._check_rpm_task_status(response['id'])
        # check queryResponse for matching package_name
        query_response = response['queryResponse']
        matching_packages = [i for i in query_response
                             if component_package_name in i['packageName']]
        return self._get_version_number_from_package_name(matching_packages[0]['packageName']) \
            if len(matching_packages) == 1 else ''

    @staticmethod
    def _get_version_number_from_package_name(package_name):
        version_number_pattern = '[0-9]+.[0-9]+.[0-9]+'
        compiled_pattern = re.compile(version_number_pattern)
        version_index = compiled_pattern.search(package_name)
        return package_name[version_index.start():version_index.end()]

    def is_installed(self):
        """Checks if the extension component package is installed on a remote device

        Parameters
        ----------
        None

        Returns
        -------
        dict
            a dictionary containing version info
            {
              'installed': 'true',
              'installed_version': 'x.x.x',
              'latest_version': 'y.y.y'
            }
        """

        # list installed packages, check if this version's package name is installed
        component_package_name = self._metadata_client.get_component_package_name()
        retrieve_rpm_version = self._check_rpm_exists(component_package_name)
        version_data = {
            'installed': retrieve_rpm_version != '',
            'installed_version': retrieve_rpm_version,
            'latest_version': self._metadata_client.get_latest_version()
        }
        return version_data
