from __future__ import annotations

import logging
import os
from pathlib import Path

import markdown  # type: ignore[import-untyped]
from dotenv import load_dotenv
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from web3_auditor.github import GitManager
from web3_auditor.llm_chat import LLMChatManager
from web3_auditor.scanner import get_source_files

logger = logging.getLogger(__name__)

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

APP_NAME = os.environ.get("APP_NAME", "Code Reviewer")


class LoadWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, mode: str, target: str, llm_manager: LLMChatManager) -> None:
        super().__init__()
        self.mode = mode
        self.target = target
        self.llm_manager = llm_manager
        self.git_manager = GitManager()

    def run(self) -> None:
        try:
            files: list[tuple[str, str]] = []
            if self.mode == "github":
                repo_path = self.git_manager.clone_repository(self.target)
                files = get_source_files(repo_path)
            elif self.mode == "local":
                files = get_source_files(self.target)
            if not files:
                self.error.emit("No supported files (.py, .sol, .js) found in the target.")
                return
            review_output = self.llm_manager.start_session(files)
            self.finished.emit(review_output)
        except Exception as e:
            logger.exception("LoadWorker failed")
            self.error.emit(str(e))
        finally:
            self.git_manager.cleanup()


class ChatWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, message: str, llm_manager: LLMChatManager) -> None:
        super().__init__()
        self.message = message
        self.llm_manager = llm_manager

    def run(self) -> None:
        try:
            response = self.llm_manager.send_message(self.message)
            self.finished.emit(response)
        except Exception as e:
            logger.exception("ChatWorker failed")
            self.error.emit(str(e))


class DropLabel(QLabel):
    fileDropped = pyqtSignal(str)  # noqa: N815

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                padding: 20px;
                background-color: #2b2b2b;
                color: #ccc;
            }
        """
        )
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:  # noqa: N802
        if event is None:
            return
        mime = event.mimeData()
        if mime is not None and mime.hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent | None) -> None:  # noqa: N802
        if event is None:
            return
        mime = event.mimeData()
        if mime is None:
            return
        urls = mime.urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.fileDropped.emit(file_path)


class AICodeReviewerGUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(900, 700)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.llm_manager = LLMChatManager()
        self.setup_ui()

    def setup_ui(self) -> None:
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        top_layout = QHBoxLayout()
        self.github_input = QLineEdit()
        self.github_input.setPlaceholderText("Paste GitHub Repository URL here...")
        self.github_input.setStyleSheet(
            "padding: 8px; background-color: #333; border: 1px solid #555;"
        )
        self.load_btn = QPushButton("Load GitHub")
        self.load_btn.setStyleSheet("padding: 8px; background-color: #007acc; color: white;")
        self.load_btn.clicked.connect(self.load_github)
        top_layout.addWidget(self.github_input)
        top_layout.addWidget(self.load_btn)

        drop_layout = QHBoxLayout()
        self.drop_label = DropLabel(
            "Drag and Drop Local Folder, .py, .sol, or .js File Here"
        )
        self.drop_label.fileDropped.connect(self.load_local_file)
        browse_layout = QVBoxLayout()
        self.browse_file_btn = QPushButton("Browse File...")
        self.browse_dir_btn = QPushButton("Browse Folder...")
        self.browse_file_btn.setStyleSheet(
            "padding: 10px; background-color: #4CAF50; color: white; border-radius: 5px;"
        )
        self.browse_dir_btn.setStyleSheet(
            "padding: 10px; background-color: #008CBA; color: white; border-radius: 5px;"
        )
        self.browse_file_btn.clicked.connect(self.browse_file)
        self.browse_dir_btn.clicked.connect(self.browse_dir)
        browse_layout.addWidget(self.browse_file_btn)
        browse_layout.addWidget(self.browse_dir_btn)
        drop_layout.addWidget(self.drop_label)
        drop_layout.addLayout(browse_layout)

        self.chat_display = QTextBrowser()
        self.chat_display.setStyleSheet(
            "background-color: #252526; padding: 10px; font-size: 14px;"
        )
        self.chat_display.setOpenExternalLinks(True)
        self.append_to_chat(
            "System", "Welcome! Drag a file/folder or paste a GitHub URL to begin the code review."
        )

        bottom_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(60)
        self.message_input.setPlaceholderText("Ask AI about the code or request upgrades...")
        self.message_input.setStyleSheet("background-color: #333; padding: 5px;")
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedHeight(60)
        self.send_btn.setStyleSheet("background-color: #007acc; padding: 10px;")
        self.send_btn.clicked.connect(self.send_message)
        bottom_layout.addWidget(self.message_input)
        bottom_layout.addWidget(self.send_btn)

        layout.addLayout(top_layout)
        layout.addLayout(drop_layout)
        layout.addWidget(self.chat_display)
        layout.addLayout(bottom_layout)

    def load_github(self) -> None:
        url = self.github_input.text().strip()
        if not url:
            return
        self.start_loading("github", url)

    def load_local_file(self, file_path: str) -> None:
        self.start_loading("local", file_path)

    def browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Code File", "", "Code Files (*.py *.sol *.js);;All Files (*)"
        )
        if path:
            self.load_local_file(path)

    def browse_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Folder", "")
        if path:
            self.load_local_file(path)

    def start_loading(self, mode: str, target: str) -> None:
        self.append_to_chat(
            "System", f"Loading code from {target}... Please wait (This might take a minute)."
        )
        self.load_btn.setEnabled(False)
        self.load_worker = LoadWorker(mode, target, self.llm_manager)
        self.load_worker.finished.connect(self.on_load_finished)
        self.load_worker.error.connect(self.on_error)
        self.load_worker.start()

    def on_load_finished(self, review_text: str) -> None:
        self.load_btn.setEnabled(True)
        self.append_to_chat("AI Reviewer", review_text)

    def send_message(self) -> None:
        msg = self.message_input.toPlainText().strip()
        if not msg:
            return
        if not self.llm_manager.chat_session:
            QMessageBox.warning(
                self, "Warning", "Please load code (GitHub or Local File) first before chatting."
            )
            return
        self.append_to_chat("You", msg)
        self.message_input.clear()
        self.send_btn.setEnabled(False)
        self.chat_worker = ChatWorker(msg, self.llm_manager)
        self.chat_worker.finished.connect(self.on_chat_finished)
        self.chat_worker.error.connect(self.on_error)
        self.chat_worker.start()

    def on_chat_finished(self, response_text: str) -> None:
        self.send_btn.setEnabled(True)
        self.append_to_chat("AI Reviewer", response_text)

    def on_error(self, error_msg: str) -> None:
        self.load_btn.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.append_to_chat("Error", f"<font color='red'>{error_msg}</font>")

    def append_to_chat(self, sender: str, text: str) -> None:
        html_text = markdown.markdown(text, extensions=["fenced_code", "codehilite"])
        color = "#569cd6" if sender == "You" else "#4ec9b0"
        if sender in ("System", "Error"):
            color = "#d4d4d4"
        message = f"<b><font size='4' color='{color}'>{sender}:</font></b><br>{html_text}<br><hr>"
        self.chat_display.append(message)
