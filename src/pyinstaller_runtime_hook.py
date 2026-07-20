"""Resolve the bundled relative data paths before importing the GUI app."""

import os
import sys


if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)
