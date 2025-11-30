

def fibonacci(n):
    """
    A function to calculate Fibonacci sequence up to a specified number.

    The Fibonacci sequence is a series of numbers in which each number after the first two (0 and 1)
    is the result of addition of the two preceding ones: 0, 1, 1, 2, 3, 5, 8, 13, 21, ...

    Parameters:
    n (int): The upper limit for the fibonacci sequence. Only Fibonacci numbers less than this number will be returned.

    Returns:
    list: A list of Fibonacci numbers that are less than n.

    Examples:
    >>> fibonacci(10)
    [0, 1, 1, 2, 3, 5, 8]
    >>> fibonacci(22)
    [0, 1, 1, 2, 3, 5, 8, 13, 21]

    Edge cases:
    If n is 0 or less, the returned list will be empty.
    If n is 1, the returned list will contain a single element: 0.

    Note: If you'd like the Fibonacci series to a specific term or position rather than up to a number, 
    you will need a different function.
    """

    result = []
    a, b = 0, 1
    while a < n:
        result.append(a)
        a, b = b, a+b
    return result



import unittest


def fibonacci(n):
    result = []
    a, b = 0, 1
    while a < n:
        result.append(a)
        a, b = b, a+b
    return result


class TestFibonacci(unittest.TestCase):

    def test_basic_functionality(self):
        self.assertEqual(fibonacci(10), [0, 1, 1, 2, 3, 5, 8])

    def test_various_inputs(self):
        self.assertEqual(fibonacci(22), [0, 1, 1, 2, 3, 5, 8, 13, 21])
        self.assertEqual(fibonacci(2), [0, 1, 1])
        self.assertEqual(fibonacci(1), [0])

    def test_edge_cases(self):
        self.assertEqual(fibonacci(0), [])
        self.assertEqual(fibonacci(-2), [])

    def test_error_cases(self):
        with self.assertRaises(TypeError):
            fibonacci("10")
        with self.assertRaises(TypeError):
            fibonacci(None)


if __name__ == '__main__':
    unittest.main()