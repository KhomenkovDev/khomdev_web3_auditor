#!/usr/bin/env python
import sys
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from web3_auditor.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
