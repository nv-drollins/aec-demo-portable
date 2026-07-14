#!/usr/bin/env python3
"""Compatibility shim for models that typo portable as portal."""
from __future__ import annotations

import os
from pathlib import Path
import sys

TARGET = Path(__file__).with_name("run-portable-hermes-authorized-cycle.py")
os.execv(sys.executable, [sys.executable, str(TARGET), *sys.argv[1:]])
