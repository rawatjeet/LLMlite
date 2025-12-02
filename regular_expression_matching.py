
import re

def is_match(text: str, pattern: str) -> bool:
    """
    Checks if a given text string matches a regular expression pattern with support for '.' and '*'.

    The function implements regular expression matching with support for the following special characters:
    - '.' (dot): Matches any single character.
    - '*' (asterisk): Matches zero or more occurrences of the preceding element.

    The matching should cover the entire input string (not partial matching).

    Args:
        text (str): The input string to be matched.
        pattern (str): The regular expression pattern.

    Returns:
        bool: True if the pattern matches the entire text string, False otherwise.

    Examples:
        >>> is_match("aa", "a")
        False
        >>> is_match("aa", "a*")
        True
        >>> is_match("ab", ".*")
        True
        >>> is_match("aab", "c*a*b")
        True
        >>> is_match("mississippi", "mis*is*p*.")
        False
        >>> is_match("aaa", "a*a")
        True
        >>> is_match("abc", "abc")
        True
        >>> is_match("abcd", "abc")
        False
        >>> is_match("abc", "abcd")
        False
        >>> is_match("", "a*")
        True
        >>> is_match("", ".*")
        True
        >>> is_match("a", ".*a")
        True
        >>> is_match("a", "ab*")
        True
        >>> is_match("a", ".*b*")
        True

    Edge Cases:
        - Empty text string and empty pattern: should return True if the pattern allows for empty string (e.g., "a*", ".*").
        - Empty text string and non-empty pattern: should return True if the pattern allows for empty string (e.g., "a*").
        - Non-empty text string and empty pattern: should return False.
        - Pattern starting with '*': should be handled correctly (though typically invalid, the re module handles it).
        - Consecutive '*': should be handled correctly by the re module.
    """

    # Use the re module to perform the regular expression matching.
    # ^ asserts the start of the string
    # $ asserts the end of the string
    # re.compile compiles the pattern for efficiency if it's used multiple times
    regex = re.compile(pattern)
    match = regex.fullmatch(text)  # fullmatch requires the entire string to match

    return bool(match)


import unittest
from typing import Tuple
import re

def is_match(text: str, pattern: str) -> bool:
    """
    Checks if a given text string matches a regular expression pattern with support for '.' and '*'.

    The function implements regular expression matching with support for the following special characters:
    - '.' (dot): Matches any single character.
    - '*' (asterisk): Matches zero or more occurrences of the preceding element.

    The matching should cover the entire input string (not partial matching).

    Args:
        text (str): The input string to be matched.
        pattern (str): The regular expression pattern.

    Returns:
        bool: True if the pattern matches the entire text string, False otherwise.

    Examples:
        >>> is_match("aa", "a")
        False
        >>> is_match("aa", "a*")
        True
        >>> is_match("ab", ".*")
        True
        >>> is_match("aab", "c*a*b")
        True
        >>> is_match("mississippi", "mis*is*p*.")
        False
        >>> is_match("aaa", "a*a")
        True
        >>> is_match("abc", "abc")
        True
        >>> is_match("abcd", "abc")
        False
        >>> is_match("abc", "abcd")
        False
        >>> is_match("", "a*")
        True
        >>> is_match("", ".*")
        True
        >>> is_match("a", ".*a")
        True
        >>> is_match("a", "ab*")
        True
        >>> is_match("a", ".*b*")
        True

    Edge Cases:
        - Empty text string and empty pattern: should return True if the pattern allows for empty string (e.g., "a*", ".*").
        - Empty text string and non-empty pattern: should return True if the pattern allows for empty string (e.g., "a*").
        - Non-empty text string and empty pattern: should return False.
        - Pattern starting with '*': should be handled correctly (though typically invalid, the re module handles it).
        - Consecutive '*': should be handled correctly by the re module.