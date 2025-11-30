def mock_function():
    return 'mock'
# Mock documentation

import unittest

class TestMock(unittest.TestCase):
    def test_mock(self):
        self.assertEqual(mock_function(), 'mock')

if __name__ == '__main__':
    unittest.main()