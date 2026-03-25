"""
ParserVis – Bottom-Up Parser Visualizer
Entry point.
"""
import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import ParserVisApp


def main():
    app = ParserVisApp()
    app.run()


if __name__ == "__main__":
    main()
