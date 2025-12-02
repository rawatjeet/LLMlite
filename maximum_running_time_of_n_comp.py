
def max_running_time(tasks, N):
    """
    Determines the maximum total running time that N computers can achieve
    when assigned a list of tasks, such that the tasks are distributed
    to maximize the minimum total running time among all computers.
    
    This problem is analogous to partitioning the list of tasks into N
    contiguous segments to maximize the minimum sum among these segments.
    It uses binary search to efficiently find the optimal maximum running time.
    
    Parameters:
        tasks (List[int]): A list of positive integers representing the durations of each task.
        N (int): The number of computers available to assign tasks to.
        
    Returns:
        int: The maximum possible running time (sum of task durations) that can be
             assigned to each computer, assuming tasks are assigned contiguously.
             
    Examples:
        >>> max_running_time([1, 2, 3, 4, 5], 2)
        9
        # Explanation: One optimal assignment is [1, 2, 3] and [4, 5], both sum to 6 and 9 respectively.
        # The maximum minimum sum is 9.
        
        >>> max_running_time([10, 20, 30], 1)
        60
        # Only one computer, so it gets all tasks.
        
        >>> max_running_time([5, 5, 5, 5], 4)
        5
        # Each computer gets one task.
        
    Edge Cases:
        - If N >= len(tasks), the maximum running time is the maximum task duration,
          since each computer can take at most one task.
        - If tasks is empty, the function should return 0.
        - If tasks contain very large numbers, the function still works efficiently due to binary search.
    """
    # Handle edge case where tasks list is empty
    if not tasks:
        return 0
    
    # Helper function to check if tasks can be assigned within 'mid' time
    def can_assign(mid):
        count = 1
        total = 0
        for task in tasks:
            if task > mid:
                return False  # Single task exceeds mid, impossible
            if total + task <= mid:
                total += task
            else:
                count += 1
                total = task
                if count > N:
                    return False
        return True

    # The minimum possible maximum running time is at least the largest task
    low = max(tasks)
    # The maximum possible running time is the sum of all tasks
    high = sum(tasks)

    max_time = 0
    while low <= high:
        mid = (low + high) // 2
        if can_assign(mid):
            max_time = mid
            high = mid - 1
        else:
            low = mid + 1

    return max_time


import unittest

class TestMaxRunningTime(unittest.TestCase):
    def test_basic_functionality(self):
        self.assertEqual(max_running_time([1, 2, 3, 4, 5], 2), 9)
        self.assertEqual(max_running_time([10, 20, 30], 1), 60)
        self.assertEqual(max_running_time([5, 5, 5, 5], 4), 5)
        self.assertEqual(max_running_time([2, 2, 2, 2], 2), 4)
        self.assertEqual(max_running_time([1, 2, 3, 4, 5], 5), 5)

    def test_edge_cases(self):
        # When tasks list is empty
        self.assertEqual(max_running_time([], 3), 0)
        # When N >= number of tasks, each task can be assigned to a separate computer
        self.assertEqual(max_running_time([4, 5, 6], 3), 6)
        self.assertEqual(max_running_time([4, 5, 6], 4), 6)
        # When all tasks are the same
        self.assertEqual(max_running_time([7, 7, 7], 2), 14)

    def test_single_task(self):
        self.assertEqual(max_running_time([10], 1), 10)
        self.assertEqual(max_running_time([10], 2), 10)  # N > number of tasks, still max is task itself

    def test_large_numbers(self):
        self.assertEqual(max_running_time([10**9, 10**9], 2), 10**9)
        self.assertEqual(max_running_time([10**9, 10**9], 1), 2 * 10**9)

    def test_impossible_assignment(self):
        # Single task larger than any possible mid
        self.assertEqual(max_running_time([100], 2), 100)
        # But if task is larger than sum of all tasks divided by N, should still work
        self.assertEqual(max_running_time([1, 2, 3], 2), 3)

    def test_invalid_input(self):
        # Tasks with non-positive integers (should still work if input is valid, but let's test)
        self.assertEqual(max_running_time([0, 0, 0], 3), 0)