from mock import patch, MagicMock, call

import os
import pytest
import six

from requests.exceptions import ConnectionError

from osfclient.models import OSFCore
from osfclient.models import Storage
from osfclient.models import File
from osfclient.models import Folder

from osfclient.tests import fake_responses
from osfclient.tests.mocks import FakeResponse, MockFile


@patch.object(OSFCore, '_get')
def test_iterate_files(OSFCore_get):
    store = Storage({})
    store._files_url = 'https://api.osf.io/v2/nodes/f3szh/files/osfstorage'

    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     ['hello.txt', 'bye.txt'])
    response = FakeResponse(200, json)
    OSFCore_get.return_value = response

    files = list(store.files)

    assert len(files) == 2
    for file_ in files:
        assert isinstance(file_, File)
        assert file_.session == store.session

    OSFCore_get.assert_called_once_with(
        'https://api.osf.io/v2/nodes/f3szh/files/osfstorage')


@patch.object(OSFCore, '_get')
def test_iterate_folders(OSFCore_get):
    store = Storage({})
    store._files_url = 'https://api.osf.io/v2/nodes/f3szh/files/osfstorage'

    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     folder_names=['foo', 'bar'])
    response = FakeResponse(200, json)
    OSFCore_get.return_value = response

    folders = list(store.folders)

    assert len(folders) == 2
    for folder in folders:
        assert isinstance(folder, Folder)
        assert folder.session == store.session
        assert folder.name in ('foo', 'bar')

    OSFCore_get.assert_called_once_with(
        'https://api.osf.io/v2/nodes/f3szh/files/osfstorage')


def test_iterate_files_and_folders():
    # check we attempt to recurse into the folders
    store = Storage({})
    store._files_url = 'https://api.osf.io/v2/nodes/f3szh/files/osfstorage'

    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     file_names=['hello.txt', 'bye.txt'],
                                     folder_names=['foo'])
    top_level_response = FakeResponse(200, json)

    second_level_url = ('https://api.osf.io/v2/nodes/9zpcy/files/' +
                        'osfstorage/foo123/')
    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     file_names=['foo/hello2.txt',
                                                 'foo/bye2.txt'])
    second_level_response = FakeResponse(200, json)

    def simple_OSFCore_get(url):
        if url == store._files_url:
            return top_level_response
        elif url == second_level_url:
            return second_level_response

    with patch.object(OSFCore, '_get',
                      side_effect=simple_OSFCore_get) as mock_osf_get:
        files = list(store.files)

    assert len(files) == 4
    for file_ in files:
        assert isinstance(file_, File)
        assert file_.session == store.session

    # check right URLs are called in the right order
    expected = [((store._files_url,),), ((second_level_url,),)]
    assert mock_osf_get.call_args_list == expected


def test_create_existing_file():
    # try to create file with a name that is already taken
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url
    store._put = MagicMock(return_value=FakeResponse(409, None))

    try:
        exception = FileExistsError
    except NameError:
        exception = OSError

    fake_fp = MagicMock()
    fake_fp.mode = 'rb'
    with pytest.raises(exception):
        store.create_file('foo.txt', fake_fp)

    store._put.assert_called_once_with(new_file_url,
                                       data=fake_fp,
                                       params={'name': 'foo.txt'})

    assert fake_fp.call_count == 0


def test_force_existing_file():
    # test that adding `force=True` lets you overwrite existing remote files
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url

    def simple_OSFCore_put(url, params=None, data=None):
        if url == new_file_url:
            return FakeResponse(409, None)
        elif url.endswith("osfstorage/foo.txt"):
            return FakeResponse(200, None)

    store._files_url = 'https://api.osf.io/v2/nodes/f3szh/files/osfstorage'
    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     file_names=['hello.txt', 'foo.txt'])
    top_level_response = FakeResponse(200, json)

    def simple_OSFCore_get(url):
        if url == store._files_url:
            return top_level_response

    fake_fp = MagicMock()
    fake_fp.mode = 'rb'
    with patch.object(OSFCore, '_put',
                      side_effect=simple_OSFCore_put) as fake_put:
        with patch.object(OSFCore, '_get',
                          side_effect=simple_OSFCore_get) as fake_get:
            store.create_file('foo.txt', fake_fp, force=True)

    assert fake_fp.call_count == 0
    assert call.read(1) in fake_fp.mock_calls
    # should have made two PUT requests, first attempt at uploading then
    # to update the file
    assert fake_put.call_count == 2
    # should have made one GET request to list files
    assert fake_get.call_count == 1


def test_update_existing_file_files_differ():
    # test that adding `update=True` lets you overwrite an existing remote file
    # if it differs from the local file
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url

    def simple_OSFCore_put(url, params=None, data=None):
        if url == new_file_url:
            return FakeResponse(409, None)
        elif url.endswith("osfstorage/foo.txt"):
            return FakeResponse(200, None)

    store._files_url = 'https://api.osf.io/v2/nodes/f3szh/files/osfstorage'
    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     file_names=['hello.txt', 'foo.txt'])
    for i_file in range(2):
        json['data'][i_file]['attributes']['extra']['hashes']['md5'] = '1' * 32
    top_level_response = FakeResponse(200, json)

    def simple_OSFCore_get(url):
        if url == store._files_url:
            return top_level_response

    def simple_checksum(file_path):
        return '0' * 32

    fake_fp = MagicMock()
    fake_fp.mode = 'rb'
    with patch.object(OSFCore, '_put',
                      side_effect=simple_OSFCore_put) as fake_put:
        with patch.object(OSFCore, '_get',
                          side_effect=simple_OSFCore_get) as fake_get:
            with patch('osfclient.models.storage.checksum',
                       side_effect=simple_checksum):
                store.create_file('foo.txt', fake_fp, update=True)

    assert fake_fp.call_count == 0
    assert call.read(1) in fake_fp.mock_calls
    # should have made two PUT requests, first attempt at uploading then
    # to update the file
    assert fake_put.call_count == 2
    # should have made one GET request to list files
    assert fake_get.call_count == 1


def test_update_existing_file_files_match():
    # test that `update=True` will not overwrite a remote file if it matches the
    # local file
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url

    def simple_OSFCore_put(url, params=None, data=None):
        if url == new_file_url:
            return FakeResponse(409, None)
        elif url.endswith("osfstorage/foo.txt"):
            return FakeResponse(200, None)

    store._files_url = 'https://api.osf.io/v2/nodes/f3szh/files/osfstorage'
    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     file_names=['hello.txt', 'foo.txt'])
    for i_file in range(2):
        json['data'][i_file]['attributes']['extra']['hashes']['md5'] = '0' * 32
    top_level_response = FakeResponse(200, json)

    def simple_OSFCore_get(url):
        if url == store._files_url:
            return top_level_response

    def simple_checksum(file_path):
        return '0' * 32
    
    fake_fp = MagicMock()
    fake_fp.mode = 'rb'
    with patch.object(OSFCore, '_put',
                      side_effect=simple_OSFCore_put) as fake_put:
        with patch.object(OSFCore, '_get',
                          side_effect=simple_OSFCore_get) as fake_get:
            with patch('osfclient.models.storage.checksum',
                       side_effect=simple_checksum):
                store.create_file('foo.txt', fake_fp, update=True)

    assert fake_fp.call_count == 0
    assert call.peek(1) not in fake_fp.mock_calls
    # should have made one PUT requests, first attempt at uploading, and no
    # attempt to update the file since they match
    assert fake_put.call_count == 1
    # should have made one GET request to list files
    assert fake_get.call_count == 1


def test_update_existing_file_files_match_force_overrides_update():
    # test that adding `force=True` and `update=True` forces overwriting of the
    # remote file, since `force=True` overrides `update=True`
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url

    def simple_OSFCore_put(url, params=None, data=None):
        if url == new_file_url:
            return FakeResponse(409, None)
        elif url.endswith("osfstorage/foo.txt"):
            return FakeResponse(200, None)

    store._files_url = 'https://api.osf.io/v2/nodes/f3szh/files/osfstorage'
    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     file_names=['hello.txt', 'foo.txt'])
    for i_file in range(2):
        json['data'][i_file]['attributes']['extra']['hashes']['md5'] = '0' * 32
    top_level_response = FakeResponse(200, json)

    def simple_OSFCore_get(url):
        if url == store._files_url:
            return top_level_response

    def simple_checksum(file_path):
        return '0' * 32
    
    fake_fp = MagicMock()
    fake_fp.mode = 'rb'
    with patch.object(OSFCore, '_put',
                      side_effect=simple_OSFCore_put) as fake_put:
        with patch.object(OSFCore, '_get',
                          side_effect=simple_OSFCore_get) as fake_get:
            with patch('osfclient.models.storage.checksum',
                       side_effect=simple_checksum):
                store.create_file('foo.txt', fake_fp, force=True, update=True)

    assert fake_fp.call_count == 0
    assert call.read(1) in fake_fp.mock_calls
    # should have made two PUT requests, first attempt at uploading then
    # to update the file, even though they match, since force=True overrides
    # update=True
    assert fake_put.call_count == 2
    # should have made one GET request to list files
    assert fake_get.call_count == 1


def test_update_existing_file_fails():
    # test we raise an error when we fail to update a file that we think
    # exists
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url

    def simple_OSFCore_put(url, params=None, data=None):
        if url == new_file_url:
            return FakeResponse(409, None)
        elif url.endswith("osfstorage/foo.txt"):
            return FakeResponse(200, None)

    store._files_url = 'https://api.osf.io/v2/nodes/f3szh/files/osfstorage'
    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     # this is the key, none of the files are
                                     # named after the file we are trying to
                                     # update
                                     file_names=['hello.txt', 'bar.txt'])
    top_level_response = FakeResponse(200, json)

    def simple_OSFCore_get(url):
        if url == store._files_url:
            return top_level_response

    fake_fp = MagicMock()
    fake_fp.mode = 'rb'
    with patch.object(OSFCore, '_put',
                      side_effect=simple_OSFCore_put):
        with patch.object(OSFCore, '_get',
                          side_effect=simple_OSFCore_get):
            with pytest.raises(RuntimeError):
                store.create_file('foo.txt', fake_fp, update=True)


def test_create_new_file():
    # create a new file at the top level
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url
    store._put = MagicMock(return_value=FakeResponse(201, None))

    fake_fp = MagicMock()
    fake_fp.mode = 'rb'

    store.create_file('foo.txt', fake_fp)

    store._put.assert_called_once_with(new_file_url,
                                       data=fake_fp,
                                       params={'name': 'foo.txt'})

    assert fake_fp.call_count == 0


def test_create_new_file_subdirectory():
    # test a new file in a new subdirectory
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/bar12/')
    new_folder_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                      'osfstorage/?kind=folder')
    store = Storage({})
    store._new_file_url = new_file_url
    store._new_folder_url = new_folder_url

    def simple_put(url, params={}, data=None):
        if url == new_folder_url:
            # this is a full fledged Folder response but also works as a
            # fake for _WaterButlerFolder
            return FakeResponse(
                201, {'data': fake_responses._folder('bar12', 'bar')}
                )
        elif url == new_file_url:
            # we don't do anything with the response, so just make it None
            return FakeResponse(201, None)
        else:
            print(url)
            assert False, 'Whoops!'

    fake_fp = MagicMock()
    fake_fp.mode = 'rb'

    with patch.object(Storage, '_put', side_effect=simple_put) as mock_put:
        store.create_file('bar/foo.txt', fake_fp)

    expected = [call(new_folder_url, params={'name': 'bar'}),
                call(new_file_url, params={'name': 'foo.txt'}, data=fake_fp)]
    assert mock_put.call_args_list == expected
    assert fake_fp.call_count == 0


def test_create_new_zero_length_file():
    # check zero length files are special cased
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url
    store._put = MagicMock(return_value=FakeResponse(201, None))

    fake_fp = MagicMock()
    fake_fp.mode = 'rb'
    fake_fp.read = lambda: ''

    store.create_file('foo.txt', fake_fp)

    store._put.assert_called_once_with(new_file_url,
                                       # this is the important check in
                                       # this test
                                       data=b'',
                                       params={'name': 'foo.txt'})

    assert fake_fp.call_count == 0


def test_create_small_file_connection_error():
    # turn a requests.ConnectionError into a RuntimeError with a more helpful
    # message that the file might exist
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url
    store._put = MagicMock(side_effect=ConnectionError)

    try:
        exception = RuntimeError
    except NameError:
        exception = OSError

    fake_fp = MagicMock()
    fake_fp.mode = 'rb'
    # set file size of 1 MB minus 1 byte ("small" file)
    with patch('osfclient.models.storage.get_local_file_size',
               return_value=2**20-1):
        with pytest.raises(exception):
            store.create_file('foo.txt', fake_fp)

    store._put.assert_called_once_with(new_file_url,
                                       data=fake_fp,
                                       params={'name': 'foo.txt'})

    assert fake_fp.call_count == 0


def test_create_big_file_connection_error(monkeypatch):
    # with a "big" file, we're more confident that a connection error means the
    # file alredy exists, so raise FileExistsError without hedging
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url
    store._put = MagicMock(side_effect=ConnectionError)

    try:
        exception = FileExistsError
    except NameError:
        exception = OSError

    fake_fp = MagicMock()
    fake_fp.mode = 'rb'
    # set file size of 1 MB ("big" file)
    with patch('osfclient.models.storage.get_local_file_size',
               return_value=2**20):
        with pytest.raises(exception):
            store.create_file('foo.txt', fake_fp)

    store._put.assert_called_once_with(new_file_url,
                                       data=fake_fp,
                                       params={'name': 'foo.txt'})

    assert fake_fp.call_count == 0


def test_update_existing_file_overrides_connection_error():
    # successful upload even on connection error if update=True
    new_file_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                    'osfstorage/foo123/')
    store = Storage({})
    store._new_file_url = new_file_url

    def simple_OSFCore_put(url, params=None, data=None):
        if url == new_file_url:
            raise ConnectionError
        elif url.endswith("osfstorage/foo.txt"):
            return FakeResponse(200, None)

    def simple_checksum(file_path):
        return '0' * 32
    
    store._files_url = 'https://api.osf.io/v2/nodes/f3szh/files/osfstorage'
    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     file_names=['hello.txt', 'foo.txt'])
    top_level_response = FakeResponse(200, json)

    def simple_OSFCore_get(url):
        if url == store._files_url:
            return top_level_response

    fake_fp = MagicMock()
    fake_fp.mode = 'rb'
    with patch.object(OSFCore, '_put',
                      side_effect=simple_OSFCore_put) as fake_put:
        with patch.object(OSFCore, '_get',
                          side_effect=simple_OSFCore_get) as fake_get:
            with patch('osfclient.models.storage.checksum',
                       side_effect=simple_checksum):
                store.create_file('foo.txt', fake_fp, update=True)

    assert fake_fp.call_count == 0
    assert call.read(1) in fake_fp.mock_calls
    # should have made two PUT requests, first attempt at uploading then
    # to update the file
    assert fake_put.call_count == 2
    # should have made one GET request to list files
    assert fake_get.call_count == 1
