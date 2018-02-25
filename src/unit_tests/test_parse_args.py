from unittest import TestCase, main

from aurman.own_exceptions import InvalidInput
from aurman.parse_args import parse_args, group_args, args_to_string


class TestParse_args(TestCase):
    def test_args_to_string(self):
        self.assertIn("a b", args_to_string({"": ["a", "b"], "a": ["anice"], "ab": ["bnice"]}))
        self.assertIn("-a anice", args_to_string({"": ["a", "b"], "a": ["anice"], "ab": ["bnice"]}))
        self.assertIn("--ab bnice", args_to_string({"": ["a", "b"], "a": ["anice"], "ab": ["bnice"]}))

    def test_parse_args(self):
        self.assertEqual(
            {"S": [], "y": [], "u": ["well"], "packages": ["p1", "p2"], "needed": [], "t": ["a"], "nice": []},
            parse_args("-Syu well --packages p1 p2 --needed -t a --nice".split()))

        self.assertEqual({"S": []}, parse_args("-S".split()))

        self.assertEqual({"S": [], "y": ["a"]}, parse_args("-Sy a".split()))

        self.assertEqual({"S": []}, parse_args("--S".split()))

        self.assertEqual({"ka": ["a", "b", "c"], "nice": []}, parse_args("--ka a b c --nice".split()))

        self.assertEqual({"k": [], "a": ["a", "b", "c"], "nice": []}, parse_args("-ka a b c --nice".split()))

        self.assertEqual({}, parse_args(" ".split()))

        self.assertEqual({"a": ["a", "b"]}, parse_args("-a a -a b".split()))

        with self.assertRaises(InvalidInput):
            parse_args("k -Syu well --packages p1 p2 --needed -t a --nice".split())

        with self.assertRaises(InvalidInput):
            parse_args("k".split())

    def test_group_args(self):
        self.assertEqual(("S", {'aurman': {"u": [], "pk": ["a", "b"], "needed": []},
                                'S': {"y": [], "u": [], "needed": []}, 'U': {}, 'other': {}}),
                         group_args("-Syu --pk a b --needed".split()))

        self.assertEqual(("S", {'aurman': {"u": [], "pk": ["a", "b"], "needed": [], "noconfirm": []},
                                'S': {"y": [], "u": [], "needed": [], "noconfirm": []}, 'U': {"noconfirm": []},
                                'other': {}}), group_args("-Syu --pk a b --needed --noconfirm".split()))

        self.assertEqual(("R", {'aurman': {}, 'S': {}, 'U': {}, 'other': {"s": [], "c": [], "gg": ["a"]}}),
                         group_args("-Rsc --gg a".split()))

        self.assertEqual(("remove", {'aurman': {}, 'S': {}, 'U': {}, 'other': {"s": [], "c": [], "gg": ["a"]}}),
                         group_args("--remove -sc --gg a".split()))

        self.assertEqual(("sync", {'aurman': {"u": [], "pk": ["a", "b"], "needed": []},
                                   'S': {"y": [], "u": [], "needed": []}, 'U': {}, 'other': {}}),
                         group_args("-yu --sync --pk a b --needed".split()))

        self.assertEqual(("sync", {'aurman': {"u": [], "pk": ["a", "b"], "needed": []},
                                   'S': {"y": [], "u": [], "needed": []}, 'U': {}, 'other': {"t": []}}),
                         group_args("-yu --sync --pk a b --needed -t".split()))


if __name__ == '__main__':
    main()
