""" Test BIG-IQ licensing assignment """

from f5cloudsdk.bigiq.licensing import AssignmentClient

from ....global_test_imports import pytest
from ....shared import constants
from ... import utils

REQ = constants.MOCK['requests']


class TestAssignmentClient(object):
    """Test"""

    @pytest.mark.usefixtures("mgmt_client")
    def test_crud_operations(self, mgmt_client, mocker):
        """Test: CRUD operation functions

        Assertions
        ----------
        - response should match mocked return value
        """

        client = AssignmentClient(mgmt_client)

        utils.validate_crud_operations(
            client,
            mocker=mocker,
            methods=['list']
        )

    @pytest.mark.usefixtures("mgmt_client")
    def test_invalid_crud_operations(self, mgmt_client, mocker):
        """Test: Invalid CRUD operation functions

        Assertions
        ----------
        - Exception should be raised for each invalid CRUD operation
        """

        client = AssignmentClient(mgmt_client)

        utils.invalidate_crud_operations(
            client,
            mocker=mocker,
            methods=['create', 'show', 'update', 'delete']
        )
