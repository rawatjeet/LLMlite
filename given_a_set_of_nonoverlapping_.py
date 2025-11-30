
def insert_interval(intervals, new_interval):
    """
    Insert a new interval into a list of non-overlapping, sorted intervals and merge if necessary.

    This function takes a list of non-overlapping intervals sorted by their start times
    and inserts a new interval into the list, merging any overlapping intervals to maintain
    the non-overlapping property.

    Parameters:
        intervals (List[List[int]]): A list of non-overlapping intervals, each represented
                                       as a list or tuple of two integers [start, end].
                                       The list is sorted by start times.
        new_interval (List[int]): The interval to insert, represented as [start, end].

    Returns:
        List[List[int]]: The updated list of non-overlapping intervals after insertion and merging.

    Examples:
        1. Basic insertion without overlap:
            intervals = [[1, 3], [6, 9]]
            new_interval = [2, 5]
            Output: [[1, 5], [6, 9]]

        2. Insertion with overlap:
            intervals = [[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]]
            new_interval = [4, 8]
            Output: [[1, 2], [3, 10], [12, 16]]

        3. Insertion at the beginning:
            intervals = [[5, 7], [8, 10]]
            new_interval = [1, 4]
            Output: [[1, 4], [5, 7], [8, 10]]

        4. Insertion at the end:
            intervals = [[1, 2], [3, 5]]
            new_interval = [6, 8]
            Output: [[1, 2], [3, 5], [6, 8]]

        5. Edge case: empty list of intervals
            intervals = []
            new_interval = [2, 3]
            Output: [[2, 3]]

        6. Edge case: new interval overlaps all existing intervals
            intervals = [[2, 3], [4, 5], [6, 7]]
            new_interval = [1, 8]
            Output: [[1, 8]]

    Edge Cases:
        - Empty list of intervals.
        - New interval overlaps multiple existing intervals.
        - New interval is completely before or after all existing intervals.
        - Intervals with zero length (start == end), if such cases are valid.
    """
    result = []
    i = 0
    n = len(intervals)

    # Add all intervals before the new interval
    while i < n and intervals[i][1] < new_interval[0]:
        result.append(intervals[i])
        i += 1

    # Merge overlapping intervals with the new interval
    while i < n and intervals[i][0] <= new_interval[1]:
        new_interval[0] = min(new_interval[0], intervals[i][0])
        new_interval[1] = max(new_interval[1], intervals[i][1])
        i += 1

    # Add the merged new interval
    result.append(new_interval)

    # Add remaining intervals after the new interval
    while i < n:
        result.append(intervals[i])
        i += 1

    return result


import unittest

class TestInsertInterval(unittest.TestCase):

    def test_basic_insertion_no_overlap(self):
        intervals = [[1, 3], [6, 9]]
        new_interval = [2, 5]
        expected = [[1, 5], [6, 9]]
        self.assertEqual(insert_interval(intervals, new_interval), expected)

    def test_insertion_with_overlap(self):
        intervals = [[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]]
        new_interval = [4, 8]
        expected = [[1, 2], [3, 10], [12, 16]]
        self.assertEqual(insert_interval(intervals, new_interval), expected)

    def test_insertion_at_beginning(self):
        intervals = [[5, 7], [8, 10]]
        new_interval = [1, 4]
        expected = [[1, 4], [5, 7], [8, 10]]
        self.assertEqual(insert_interval(intervals, new_interval), expected)

    def test_insertion_at_end(self):
        intervals = [[1, 2], [3, 5]]
        new_interval = [6, 8]
        expected = [[1, 2], [3, 5], [6, 8]]
        self.assertEqual(insert_interval(intervals, new_interval), expected)

    def test_empty_intervals(self):
        intervals = []
        new_interval = [2, 3]
        expected = [[2, 3]]
        self.assertEqual(insert_interval(intervals, new_interval), expected)

    def test_overlap_all_intervals(self):
        intervals = [[2, 3], [4, 5], [6, 7]]
        new_interval = [1, 8]
        expected = [[1, 8]]
        self.assertEqual(insert_interval(intervals, new_interval), expected)

    def test_zero_length_intervals(self):
        intervals = [[1, 1], [2, 2], [3, 3]]
        new_interval = [2, 2]
        expected = [[1, 1], [2, 2], [3, 3]]  # inserting same interval
        self.assertEqual(insert_interval(intervals, new_interval), expected)

    def test_new_interval_before_all(self):
        intervals = [[5, 6], [