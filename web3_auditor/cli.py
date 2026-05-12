from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from web3_auditor import validate_config

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)


def main() -> None:
    validate_config()
    from PyQt6.QtWidgets import QApplication

    from web3_auditor.gui import AICodeReviewerGUI

    app = QApplication(sys.argv)
    window = AICodeReviewerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
