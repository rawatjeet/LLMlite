
def find_median_sorted_arrays(nums1, nums2):
    """
    Finds the median of two sorted arrays.

    This function uses a binary search approach to efficiently find the median
    in O(log(min(len(nums1), len(nums2)))) time complexity.

    Parameters:
    nums1 (List[int] or List[float]): First sorted array.
    nums2 (List[int] or List[float]): Second sorted array.

    Returns:
    float: The median value of the combined sorted arrays.

    Examples:
    >>> find_median_sorted_arrays([1, 3], [2])
    2.0
    >>> find_median_sorted_arrays([1, 2], [3, 4])
    2.5
    >>> find_median_sorted_arrays([], [1])
    1.0
    >>> find_median_sorted_arrays([2], [])
    2.0

    Edge Cases:
    - One or both arrays are empty.
    - Arrays of different lengths.
    - Arrays with duplicate elements.
    - Arrays with negative numbers or floating point numbers.
    """

    # Ensure nums1 is the smaller array to optimize the binary search
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1

    m, n = len(nums1), len(nums2)
    imin, imax = 0, m
    half_len = (m + n + 1) // 2

    while imin <= imax:
        i = (imin + imax) // 2
        j = half_len - i

        # Check if i is too small, need to move right
        if i < m and nums2[j - 1] > nums1[i]:
            imin = i + 1
        # Check if i is too big, need to move left
        elif i > 0 and nums1[i - 1] > nums2[j]:
            imax = i - 1
        else:
            # i is perfect
            if i == 0:
                max_of_left = nums2[j - 1]
            elif j == 0:
                max_of_left = nums1[i - 1]
            else:
                max_of_left = max(nums1[i - 1], nums2[j - 1])

            # If total length is odd, median is max of left
            if (m + n) % 2 == 1:
                return max_of_left

            # For even total length, need to find min of right
            if i == m:
                min_of_right = nums2[j]
            elif j == n:
                min_of_right = nums1[i]
            else:
                min_of_right = min(nums1[i], nums2[j])

            return (max_of_left + min_of_right) / 2.0


import unittest

class TestFindMedianSortedArrays(unittest.TestCase):
    def test_basic_cases(self):
        self.assertEqual(find_median_sorted_arrays([1, 3], [2]), 2.0)
        self.assertEqual(find_median_sorted_arrays([1, 2], [3, 4]), 2.5)
        self.assertEqual(find_median_sorted_arrays([0, 0], [0, 0]), 0.0)
        self.assertEqual(find_median_sorted_arrays([1], [2, 3, 4]), 2.5)
        self.assertEqual(find_median_sorted_arrays([2], []), 2.0)
        self.assertEqual(find_median_sorted_arrays([], [1]), 1.0)

    def test_with_negative_numbers(self):
        self.assertEqual(find_median_sorted_arrays([-3, -1], [-2, 0]), -1.5)
        self.assertEqual(find_median_sorted_arrays([-5, -3, -1], [-2, 0, 2]), -2.0)

    def test_with_floats(self):
        self.assertAlmostEqual(find_median_sorted_arrays([1.1, 2.2], [3.3, 4.4]), 2.75)
        self.assertAlmostEqual(find_median_sorted_arrays([1.1], [2.2]), 1.65)

    def test_empty_arrays(self):
        # One array empty
        self.assertEqual(find_median_sorted_arrays([], [1]), 1.0)
        self.assertEqual(find_median_sorted_arrays([2], []), 2.0)
        # Both arrays empty should raise an error
        with self.assertRaises(IndexError):
            find_median_sorted_arrays([], [])

    def test_single_element_arrays(self):
        self.assertEqual(find_median_sorted_arrays([1], [2]), 1.5)
        self.assertEqual(find_median_sorted_arrays([1], [1]), 1.0)
        self.assertEqual(find_median_sorted_arrays([2], [2]), 2.0)

    def test_large_arrays(self):
        arr1 = list(range(0, 10000, 2))
        arr2 = list(range(1, 10000, 2))
        self.assertEqual(find_median_sorted_arrays(arr1, arr2), 4999.5)

    def test_error_cases(self):
        # Passing non-list
        with self.assertRaises(TypeError):
            find_median_sorted_arrays(None, [1])
        with self.assertRaises(TypeError):
            find_median_sorted_arrays([1], None)
        # Passing unsupported types
        with self.assertRaises(TypeError):
            find_median_sorted_arrays("not a list", [1])
        with self.assertRaises(TypeError):
            find_median_sorted_arrays([1], "not a list")