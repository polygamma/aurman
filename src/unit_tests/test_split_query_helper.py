from unittest import TestCase, main

from aurman.own_exceptions import InvalidInput
from aurman.wrappers import split_query_helper


class TestSplit_query_helper(TestCase):
    def test_split_query_helper(self):
        self.assertEqual([["a", "b"]], split_query_helper(3, 1, 0, ("a", "b")))
        self.assertEqual([["a", "b"]], split_query_helper(5, 1, 1, ("a", "b")))
        self.assertEqual([["a"], ["b"]], split_query_helper(4, 1, 1, ("a", "b")))
        self.assertEqual([["a"], ["b"]], split_query_helper(2, 1, 0, ("a", "b")))
        self.assertEqual([["abc"], ["b", "c", "d"], ["e"]], split_query_helper(4, 1, 0, ("abc", "b", "c", "d", "e")))
        with self.assertRaises(InvalidInput):
            split_query_helper(2, 1, 1, ("a", "b"))
        with self.assertRaises(InvalidInput):
            split_query_helper(3, 1, 1, ("a", "bc"))


if __name__ == '__main__':
    main()
