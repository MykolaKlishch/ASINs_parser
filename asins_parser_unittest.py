import unittest
import argparse
from asins_parser import (
    DEFAULT_FILENAME,
    get_filename_from_cmd,
    valid_filename,
    get_asins_from_csv,
)


class TestArgumentParsing(unittest.TestCase):

    def test_get_filename_from_cmd(self):
        # calling without arguments must return DEFAULT_FILENAME:
        self.assertEqual(
            get_filename_from_cmd(), DEFAULT_FILENAME
        )
        # argument -i: existing file
        # It is assumed that file DEFAULT_FILENAME exists:
        self.assertEqual(
            get_filename_from_cmd(["-i", DEFAULT_FILENAME]), DEFAULT_FILENAME
        )
        invalid_arguments = [
            ["-i", "file_that_does_not_exist.csv"],  # invalid filename
            ["-invalidargname", DEFAULT_FILENAME],  # invalid argument
            ["-i"],  # missing value
            [DEFAULT_FILENAME],  # passing valid filename outside the argument
        ]
        for invalid_argument in invalid_arguments:
            self.assertRaises(
                (
                    argparse.ArgumentTypeError,
                    argparse.ArgumentError,
                    SystemExit
                ),
                get_filename_from_cmd,
                invalid_argument
            )

    def test_valid_filename(self):
        self.assertEqual(
            valid_filename(DEFAULT_FILENAME), DEFAULT_FILENAME
        )
        with self.assertRaises(argparse.ArgumentTypeError):
            valid_filename("file_that_does_not_exist.csv")


class ValidateAsins(unittest.TestCase):
    """validates DEFAULT_FILENAME file contents,
    not the get_asins_from_csv() function"""
    def test_asins_list(self):
        asins_list = get_asins_from_csv
        asins_set = set(asins_list)
        assert len(asins_list) == len(asins_set)
        for asin in asins_set:
            assert isinstance(asin, str)
        assert "" not in asins_set


if __name__ == '__main__':
    unittest.main()
