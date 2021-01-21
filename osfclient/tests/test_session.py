from mock import patch
from mock import MagicMock

import pytest

from osfclient.models import OSFSession
from osfclient.exceptions import UnauthorizedException


def test_basic_auth():
    session = OSFSession()
    session.basic_auth('joe@example.com', 'secret_password')
    assert session.auth == ('joe@example.com', 'secret_password')
    assert 'Authorization' not in session.headers

def test_address():
    address = "https://api.test.osf.io/v2/"
    session = OSFSession(address=address)
    assert session.base_url == address
    assert session.base_url != "https://api.osf.io/v2/"

def test_token_auth():
    session = OSFSession()
    session.token_auth('asdfg')
    assert 'Authorization' in session.headers


def test_token_auth():
    session = OSFSession()
    session.token_auth('asdfg')
    assert 'Authorization' in session.headers


def test_basic_build_url():
    session = OSFSession()
    url = session.build_url("some", "path")
    assert url.startswith(session.base_url)
    assert url.endswith("/some/path/")


@patch('osfclient.models.session.requests.Session.put')
def test_unauthorized_put(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 401

    mock_put.return_value = mock_response

    url = 'http://example.com/foo'

    session = OSFSession()

    with pytest.raises(UnauthorizedException):
        session.put(url)

    mock_put.assert_called_once_with(url)


@patch('osfclient.models.session.requests.Session.get')
def test_unauthorized_get(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 401

    mock_get.return_value = mock_response

    url = 'http://example.com/foo'

    session = OSFSession()

    with pytest.raises(UnauthorizedException):
        session.get(url)

    mock_get.assert_called_once_with(url)


@patch('osfclient.models.session.requests.Session.put')
def test_put(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_put.return_value = mock_response

    url = 'http://example.com/foo'

    session = OSFSession()

    response = session.put(url)

    assert response == mock_response
    mock_put.assert_called_once_with(url)


@patch('osfclient.models.session.requests.Session.get')
def test_get(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_get.return_value = mock_response

    url = 'http://example.com/foo'

    session = OSFSession()

    response = session.get(url)

    assert response == mock_response
    mock_get.assert_called_once_with(url)
