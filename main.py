"""
VisParser – Bottom-Up Parser Visualizer
Entry point.
"""
import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import VisParserApp


def main():
    app = VisParserApp()
    app.run()


if __name__ == "__main__":
    main()
