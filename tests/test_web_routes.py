from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from web.app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_session_data():
    mock = MagicMock()
    mock.manager = MagicMock()
    mock.event_queue = AsyncMock()
    return mock


class TestReadRoot:
    def test_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestLoadGithub:
    def test_returns_review(self, client, mock_session_data):
        mock_session_data.manager.start_session.return_value = "# Review"
        mock_git = MagicMock()
        mock_git.clone_repository.return_value = "/tmp/repo"

        with (
            patch("web.routes.get_session_data", return_value=mock_session_data),
            patch("web.routes.GitManager", return_value=mock_git),
            patch("web.routes.get_source_files", return_value=[("a.py", "code")]),
            patch("web.routes.markdown.markdown", return_value="<h1>Review</h1>"),
        ):
            response = client.post(
                "/api/load-github", data={"repo_url": "https://github.com/user/repo"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["html_review"] == "<h1>Review</h1>"
        assert data["raw_review"] == "# Review"
        assert "session_id" in data
        mock_git.cleanup.assert_called_once()

    def test_returns_review_invalid_url(self, client):
        response = client.post(
            "/api/load-github", data={"repo_url": "not-a-url"}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"

    def test_no_supported_files(self, client, mock_session_data):
        mock_git = MagicMock()
        mock_git.clone_repository.return_value = "/tmp/repo"

        with (
            patch("web.routes.get_session_data", return_value=mock_session_data),
            patch("web.routes.GitManager", return_value=mock_git),
            patch("web.routes.get_source_files", return_value=[]),
        ):
            response = client.post(
                "/api/load-github", data={"repo_url": "https://github.com/user/repo"}
            )

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "No supported files" in data["message"]
        mock_git.cleanup.assert_called_once()

    def test_clone_failure(self, client, mock_session_data):
        mock_git = MagicMock()
        mock_git.clone_repository.side_effect = RuntimeError("clone failed")

        with (
            patch("web.routes.get_session_data", return_value=mock_session_data),
            patch("web.routes.GitManager", return_value=mock_git),
        ):
            response = client.post(
                "/api/load-github", data={"repo_url": "https://github.com/user/repo"}
            )

        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        mock_git.cleanup.assert_called_once()


class TestLoadLocal:
    def test_returns_review(self, client, mock_session_data):
        mock_session_data.manager.start_session.return_value = "# Review"

        with (
            patch("web.routes.get_session_data", return_value=mock_session_data),
            patch("web.routes.markdown.markdown", return_value="<h1>Review</h1>"),
        ):
            response = client.post(
                "/api/load-local",
                files={"files": ("test.py", "print('hello')", "text/x-python")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["html_review"] == "<h1>Review</h1>"

    def test_no_valid_files(self, client):
        response = client.post(
            "/api/load-local",
            files={"files": ("readme.md", "# Readme", "text/markdown")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "No supported files" in data["message"]

    def test_unicode_decode_error_skips_file(self, client):
        response = client.post(
            "/api/load-local",
            files={"files": ("test.py", b"\xff\xfe\x00\x01", "application/octet-stream")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"

    def test_start_session_failure(self, client, mock_session_data):
        mock_session_data.manager.start_session.side_effect = RuntimeError("LLM error")

        with (
            patch("web.routes.get_session_data", return_value=mock_session_data),
        ):
            response = client.post(
                "/api/load-local",
                files={"files": ("test.py", "print('hello')", "text/x-python")},
            )

        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"


class TestChat:
    def test_returns_response(self, client):
        mock_manager = MagicMock()
        mock_manager.send_message.return_value = "Chat reply"

        with (
            patch("web.routes.get_session", return_value=mock_manager),
            patch("web.routes.markdown.markdown", return_value="<p>Chat reply</p>"),
        ):
            response = client.post(
                "/api/chat",
                data={"session_id": "test-sess", "message": "hello"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["html_response"] == "<p>Chat reply</p>"
        mock_manager.send_message.assert_called_once_with("hello")

    def test_requires_session_id(self, client):
        response = client.post(
            "/api/chat",
            data={"session_id": "", "message": "hello"},
        )
        assert response.status_code in (400, 422)

    def test_send_message_failure(self, client):
        mock_manager = MagicMock()
        mock_manager.send_message.side_effect = RuntimeError("chat error")

        with (
            patch("web.routes.get_session", return_value=mock_manager),
        ):
            response = client.post(
                "/api/chat",
                data={"session_id": "test-sess", "message": "hello"},
            )

        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
