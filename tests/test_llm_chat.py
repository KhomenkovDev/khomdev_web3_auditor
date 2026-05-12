from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from web3_auditor.llm_chat import DEFAULT_MODEL, LLMChatManager

VALID_JSON = '{"overview": "review", "findings": [], "improvements": []}'
NON_JSON = "this is not json"


class TestLLMChatManager:
    def test_start_session_requires_api_key(self):
        manager = LLMChatManager()
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError, match="GEMINI_API_KEY"),
        ):
            manager.start_session([])

    def test_send_message_requires_active_session(self):
        manager = LLMChatManager()
        with pytest.raises(RuntimeError, match="No active chat session"):
            manager.send_message("hello")

    @patch("web3_auditor.llm_chat.genai.Client")
    def test_start_session_creates_chat(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_chat = MagicMock()
        mock_client.chats.create.return_value = mock_chat
        mock_chat.send_message.return_value.text = VALID_JSON

        manager = LLMChatManager()
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            result = manager.start_session([("test.py", "print('hello')")])

        assert "review" in result
        mock_client.chats.create.assert_called_once()

    @patch("web3_auditor.llm_chat.genai.Client")
    def test_send_message_returns_response(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_chat = MagicMock()
        mock_client.chats.create.return_value = mock_chat
        mock_chat.send_message.return_value.text = VALID_JSON

        manager = LLMChatManager()
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            manager.start_session([("test.py", "print('x')")])
            result = manager.send_message("What do you think?")

        assert result == VALID_JSON

    @patch("web3_auditor.llm_chat.genai.Client")
    def test_start_session_uses_custom_model(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_chat = MagicMock()
        mock_client.chats.create.return_value = mock_chat
        mock_chat.send_message.return_value.text = VALID_JSON

        manager = LLMChatManager()
        with patch.dict(
            "os.environ", {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-2.5-flash"}
        ):
            manager.start_session([("test.py", "x = 1")])

        mock_client.chats.create.assert_called_once_with(model="gemini-2.5-flash")

    @patch("web3_auditor.llm_chat.genai.Client")
    def test_start_session_uses_default_model(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_chat = MagicMock()
        mock_client.chats.create.return_value = mock_chat
        mock_chat.send_message.return_value.text = VALID_JSON

        manager = LLMChatManager()
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            manager.start_session([("test.py", "x = 1")])

        mock_client.chats.create.assert_called_once_with(model=DEFAULT_MODEL)

    @patch("time.sleep")
    @patch("web3_auditor.llm_chat.genai.Client")
    def test_send_retry_transient_then_succeeds(self, mock_client_class, mock_sleep):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_chat = MagicMock()
        mock_client.chats.create.return_value = mock_chat

        ok_response = MagicMock(text=VALID_JSON)
        success_response = MagicMock(text="Success after retry")
        mock_chat.send_message.side_effect = [
            ok_response,
            Exception("503 Service Unavailable"),
            Exception("503 Service Unavailable"),
            success_response,
        ]

        manager = LLMChatManager()
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            manager.start_session([("test.py", "x = 1")])
            result = manager.send_message("hello")

        assert result == "Success after retry"
        assert mock_chat.send_message.call_count == 4

    @patch("time.sleep")
    @patch("web3_auditor.llm_chat.genai.Client")
    def test_send_retry_all_transient_fail(self, mock_client_class, mock_sleep):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_chat = MagicMock()
        mock_client.chats.create.return_value = mock_chat

        ok_response = MagicMock(text=VALID_JSON)
        mock_chat.send_message.side_effect = [ok_response] + [
            Exception("503 Service Unavailable")
        ] * 6

        manager = LLMChatManager()
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            manager.start_session([("test.py", "x = 1")])
            with pytest.raises(Exception, match="503 Service Unavailable"):
                manager.send_message("hello")

    @patch("time.sleep")
    @patch("web3_auditor.llm_chat.genai.Client")
    def test_send_non_transient_error_immediately_raises(self, mock_client_class, mock_sleep):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_chat = MagicMock()
        mock_client.chats.create.return_value = mock_chat

        ok_response = MagicMock(text=VALID_JSON)
        mock_chat.send_message.side_effect = [ok_response, Exception("invalid argument")]

        manager = LLMChatManager()
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            manager.start_session([("test.py", "x = 1")])
            with pytest.raises(Exception, match="invalid argument"):
                manager.send_message("hello")
        assert mock_chat.send_message.call_count == 2
