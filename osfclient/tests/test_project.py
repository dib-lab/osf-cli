from mock import patch
import pytest

from osfclient.models import OSFCore
from osfclient.models import Project
from osfclient.models import Storage

from osfclient.tests import fake_responses
from osfclient.tests.mocks import FakeResponse


@patch.object(OSFCore, '_get')
def test_invalid_storage(OSFCore_get):
    project = Project({})
    project._storages_url = 'https://api.osf.io/v2/nodes/f3szh/files/'

    response = FakeResponse(200, fake_responses.storage_node('f3szh'))
    OSFCore_get.return_value = response

    with pytest.raises(RuntimeError):
        project.storage('does-not-exist')

    OSFCore_get.assert_called_once_with(
        'https://api.osf.io/v2/nodes/f3szh/files/')


@patch.object(OSFCore, '_get')
def test_valid_storage(OSFCore_get):
    project = Project({})
    project._storages_url = 'https://api.osf.io/v2/nodes/f3szh/files/'

    response = FakeResponse(200, fake_responses.storage_node('f3szh'))
    OSFCore_get.return_value = response

    storage = project.storage('osfstorage')

    OSFCore_get.assert_called_once_with(
        'https://api.osf.io/v2/nodes/f3szh/files/')
    assert isinstance(storage, Storage)


@patch.object(OSFCore, '_get')
def test_iterate_storages(OSFCore_get):
    project = Project({})
    project._storages_url = 'https://api.osf.io/v2/nodes/f3szh/files/'

    store_json = fake_responses.storage_node('f3szh',
                                             ['osfstorage', 'github'])
    response = FakeResponse(200, store_json)
    OSFCore_get.return_value = response

    stores = list(project.storages)

    assert len(stores) == 2
    for store in stores:
        assert isinstance(store, Storage)

    OSFCore_get.assert_called_once_with(
        'https://api.osf.io/v2/nodes/f3szh/files/')


@patch.object(OSFCore, '_get')
def test_pass_down_session_to_storage(OSFCore_get):
    # check that `self.session` is passed to newly created OSFCore instances
    project = Project({})
    project._storages_url = 'https://api.osf.io/v2/nodes/f3szh/files/'

    store_json = fake_responses.storage_node('f3szh')
    response = FakeResponse(200, store_json)
    OSFCore_get.return_value = response

    store = project.storage()

    assert store.session == project.session

def test_jsonld_init_project():
    project = Project(fake_responses.jsonld_attributes)

    assert project.metadata(jsonld=True) == fake_responses.jsonld_attributes


@patch.object(OSFCore, '_get')
def test_pass_down_session_to_storages(OSFCore_get):
    # as previous test but for multiple storages
    project = Project({})
    project._storages_url = 'https://api.osf.io/v2/nodes/f3szh/files/'

    store_json = fake_responses.storage_node('f3szh')
    response = FakeResponse(200, store_json)
    OSFCore_get.return_value = response

    for store in project.storages:
        assert store.session == project.session
