from unittest import TestCase, main

from aurman.own_exceptions import InvalidInput
from aurman.parse_args import parse_pacman_args, PacmanOperations


class TestParse_pacman_args(TestCase):
    def test_parse_pacman_args(self):
        args = "-Syu --needed --noconfirm package1 --domain localhost package2 -v package3".split()
        ret_val = parse_pacman_args(args)
        self.assertEqual(["package1", "package2", "package3"], ret_val.targets)
        self.assertTrue(ret_val.verbose)
        self.assertFalse(ret_val.force)
        self.assertTrue(ret_val.refresh)
        self.assertTrue(ret_val.sysupgrade)
        self.assertEqual(["localhost"], ret_val.domain)

        with self.assertRaises(AttributeError):
            self.assertFalse(ret_val.test)
        with self.assertRaises(InvalidInput):
            parse_pacman_args("-Syu --v package1 - test".split())
        with self.assertRaises(InvalidInput):
            parse_pacman_args("-Syu -v package1 - test".split())

        args = "--sync --search aurman-git --verbose -s helper aur".split()
        ret_val = parse_pacman_args(args)
        self.assertEqual(PacmanOperations.SYNC, ret_val.operation)
        self.assertEqual(["aurman-git", "helper", "aur"], ret_val.search)
        self.assertTrue(ret_val.verbose)
        self.assertFalse(ret_val.needed)
        self.assertIsInstance(ret_val.domain, list)
        self.assertIsInstance(ret_val.cachedir, list)

        args = "-Syyu -c --clean".split()
        ret_val = parse_pacman_args(args)
        self.assertEqual(['something'], ret_val.refresh)
        self.assertEqual(['something'], ret_val.clean)
        self.assertEqual(True, ret_val.sysupgrade)

        args = "-Syu -c --clean".split()
        ret_val = parse_pacman_args(args)
        self.assertEqual(True, ret_val.refresh)
        self.assertNotEqual(['something'], ret_val.refresh)
        self.assertEqual(['something'], ret_val.clean)
        self.assertEqual(True, ret_val.sysupgrade)

        self.assertEqual(2, ret_val.as_list().count("--clean"))
        self.assertEqual(1, ret_val.as_list().count("--sysupgrade"))
        self.assertEqual(1, ret_val.as_list().count("--refresh"))


if __name__ == '__main__':
    main()
