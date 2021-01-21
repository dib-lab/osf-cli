import io
from mock import call
from mock import patch
from mock import MagicMock
from mock import PropertyMock

import pytest

from osfclient.models import OSFCore
from osfclient.models import File
from osfclient.models import Folder
from osfclient.exceptions import FolderExistsException
from osfclient.models.file import _WaterButlerFolder

from osfclient.tests import fake_responses
from osfclient.tests.mocks import FakeResponse, MockFolder

_files_url = 'https://api.osf.io/v2/nodes/f3szh/files/osfstorage/foo123'


@patch.object(OSFCore, '_get')
def test_iterate_files(OSFCore_get):
    store = Folder({})
    store._files_url = _files_url

    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     ['foo/hello.txt', 'foo/bye.txt'])
    response = FakeResponse(200, json)
    OSFCore_get.return_value = response

    files = list(store.files)

    assert len(files) == 2
    for file_ in files:
        assert isinstance(file_, File)
        assert file_.session == store.session

    OSFCore_get.assert_called_once_with(
        'https://api.osf.io/v2/nodes/f3szh/files/osfstorage/foo123')


@patch.object(OSFCore, '_get')
def test_iterate_folders(OSFCore_get):
    store = Folder({})
    store._files_url = _files_url

    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     folder_names=['foo/bar', 'foo/baz'])
    response = FakeResponse(200, json)
    OSFCore_get.return_value = response

    folders = list(store.folders)

    assert len(folders) == 2
    for folder in folders:
        assert isinstance(folder, Folder)
        assert folder.session == store.session
        assert folder.name in ('foo/bar', 'foo/baz')

    OSFCore_get.assert_called_once_with(
        'https://api.osf.io/v2/nodes/f3szh/files/osfstorage/foo123')


def test_iterate_files_and_folders():
    # check we do not attempt to recurse into the subfolders
    store = Folder({})
    store._files_url = _files_url

    json = fake_responses.files_node('f3szh', 'osfstorage',
                                     file_names=['hello.txt', 'bye.txt'],
                                     folder_names=['bar'])
    top_level_response = FakeResponse(200, json)

    def simple_OSFCore_get(url):
        if url == store._files_url:
            return top_level_response
        else:
            print(url)
            raise ValueError()

    with patch.object(OSFCore, '_get',
                      side_effect=simple_OSFCore_get) as mock_osf_get:
        files = list(store.files)

    assert len(files) == 2
    for file_ in files:
        assert isinstance(file_, File)
        assert file_.session == store.session
        assert file_.name in ('hello.txt', 'bye.txt')

    # check we did not try to recurse into subfolders
    expected = [((_files_url,),)]
    assert mock_osf_get.call_args_list == expected


def test_create_existing_folder():
    folder = Folder({})
    new_folder_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                      'osfstorage/foo123/?kind=folder')
    folder._new_folder_url = new_folder_url
    folder._put = MagicMock(return_value=FakeResponse(409, None))

    with pytest.raises(FolderExistsException):
        folder.create_folder('foobar')

    folder._put.assert_called_once_with(new_folder_url,
                                        params={'name': 'foobar'})


def test_create_existing_folder_exist_ok():
    folder = Folder({})
    new_folder_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                      'osfstorage/foo123/?kind=folder')
    folder._new_folder_url = new_folder_url
    folder._put = MagicMock(return_value=FakeResponse(409, None))

    with patch.object(Folder, 'folders',
                      new_callable=PropertyMock) as mock_folder:
        mock_folder.return_value = [MockFolder('foobar'), MockFolder('fudge')]
        existing_folder = folder.create_folder('foobar', exist_ok=True)

    assert existing_folder.name == 'foobar'

    folder._put.assert_called_once_with(new_folder_url,
                                        params={'name': 'foobar'})


def test_create_new_folder():
    folder = Folder({})
    new_folder_url = ('https://files.osf.io/v1/resources/9zpcy/providers/' +
                      'osfstorage/foo123/?kind=folder')
    folder._new_folder_url = new_folder_url
    # use an empty response as we won't do anything with the returned instance
    folder._put = MagicMock(return_value=FakeResponse(201, {'data': {}}))

    new_folder = folder.create_folder('foobar')

    assert isinstance(new_folder, _WaterButlerFolder)

    folder._put.assert_called_once_with(new_folder_url,
                                        params={'name': 'foobar'})


def test_remove_file():
    f = File({})
    f._delete_url = 'http://delete.me/uri'
    f._delete = MagicMock(return_value=FakeResponse(204, {'data': {}}))

    f.remove()

    assert f._delete.called


def test_file_uses_streaming_request():
    # check we use streaming mode to fetch files
    fp = io.BytesIO(b"")
    fp.mode = "b"
    file_content = b"hello world"

    def fake_get(url, stream):
        raw = MagicMock()
        src = io.BytesIO(file_content)
        raw.read = src.read

        res = FakeResponse(200, {})
        res.raw = raw
        res.headers = {'Content-Length': str(len(file_content))}
        return res

    with patch.object(File, "_get", side_effect=fake_get) as mock_get:
        f = File({})
        f._download_url = "http://example.com/download_url/"
        f.write_to(fp)

    fp.seek(0)
    assert file_content == fp.read()
    expected = call('http://example.com/download_url/', stream=True)
    assert expected in mock_get.mock_calls


def test_remove_file_failed():
    f = File({})
    f.path = 'some/path'
    f._delete_url = 'http://delete.me/uri'
    f._delete = MagicMock(return_value=FakeResponse(404, {'data': {}}))

    with pytest.raises(RuntimeError) as e:
        f.remove()

    assert f._delete.called

    assert 'Could not delete' in e.value.args[0]
