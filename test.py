import os
from unittest import TestLoader, TextTestRunner


if __name__ == '__main__':
    loader = TestLoader()
    tests_dir = os.path.join(os.path.dirname(__file__), 'tests')
    tests = loader.discover(tests_dir, pattern='*.py')
    runner = TextTestRunner()
    result = runner.run(tests)
    if result.failures:
        raise SystemExit(f'{len(result.failures)} tests failed.')
