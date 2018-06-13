import os
from unittest import TestLoader, TextTestRunner


if __name__ == '__main__':
    loader = TestLoader()
    tests = loader.discover(os.path.dirname(__file__), pattern='*.py')
    runner = TextTestRunner()
    runner.run(tests)