import argparse
import unittest

from parsers import ProductInfoParser, ProductReviewsParser
from main import (DEFAULT_FILENAME, get_filename_from_cmd, valid_filename,
                  get_asins_from_csv_file)


class TestCmdArgumentParsing(unittest.TestCase):

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
    not the get_asins_from_csv_file() function.
    """

    def test_asins_list(self):
        asins_list = get_asins_from_csv_file(DEFAULT_FILENAME)
        asins_set = set(asins_list)
        self.assertEqual(len(asins_list), len(asins_set))
        for asin in asins_set:
            self.assertIsInstance(obj=asin, cls=str)
        self.assertNotIn(member="", container=asins_set)


class TestParsersMatchingAccuracy(unittest.TestCase):
    """Tests if regexes in parse() method of parser classes
     extract and transform values as expected.
     """

    def test_product_name_extraction(self):
        parser = ProductInfoParser()
        html_no_match = ''
        parser.parse(html_no_match)
        self.assertEqual(parser.product_name, None)

        html_leading_company_name = \
            '<title>Amazon.com: Product Name</title>'
        parser.parse(html_leading_company_name)
        self.assertEqual(parser.product_name, 'Product Name')

        html_leading_company_name_extra_whitespace = \
            '<title>Amazon.com : Product Name</title>'
        parser.parse(html_leading_company_name_extra_whitespace)
        self.assertEqual(parser.product_name, 'Product Name')

        html_trailing_company_name = \
            '<title>Product Name - - Amazon.com</title>'
        parser.parse(html_trailing_company_name)
        self.assertEqual(parser.product_name, 'Product Name')

        html_trailing_company_name = \
            '<title>Amazon.com: Product &quot; &amp; Name</title>'
        parser.parse(html_trailing_company_name)
        self.assertEqual(parser.product_name, 'Product " & Name')

    def test_total_ratings_extraction(self):
        parser = ProductInfoParser()
        html = (
            '<span id="acrCustomerReviewText" '
            'class="a-size-base">1,775 ratings</span>'
        )
        parser.parse(html)
        self.assertEqual(parser.total_ratings, 1775)

    def test_average_rating_extraction(self):
        parser = ProductInfoParser()
        html = (
            '<span id="acrPopover" class="reviewCountTextLinkedHistogram '
            'noUnderline" title="4.0 out of 5 stars">'
        )
        parser.parse(html)
        self.assertEqual(parser.average_rating, 4.0)

    def test_answered_questions_extraction(self):
        parser = ProductInfoParser()
        html_no_match = ''
        parser.parse(html_no_match)
        self.assertEqual(parser.answered_questions, 0)

        html_typical = """
<span class="a-size-base">
37 answered questions
</span>
        """
        parser.parse(html_typical)
        self.assertEqual(parser.answered_questions, 37)

        html_plus = """
<span class="a-size-base">
1000+ answered questions
</span>
"""
        parser.parse(html_plus)
        self.assertEqual(parser.answered_questions, 1000)

    def test_total_reviews_extraction(self):
        parser = ProductReviewsParser()
        html = 'class="a-size-base">Showing 1-10 of 1,863 reviews</span>'
        parser.parse(html)
        self.assertEqual(parser.total_reviews, 1863)

    def test_positive_reviews_extraction(self):
        parser = ProductReviewsParser()
        html = 'filterByStar=positive">See all 1,664 positive reviews</a>'
        parser.parse(html)
        self.assertEqual(parser.positive_reviews, 1664)

    def test_critical_reviews_extraction(self):
        parser = ProductReviewsParser()
        html = 'filterByStar=critical">See all 199 critical reviews</a>'
        parser.parse(html)
        self.assertEqual(parser.critical_reviews, 199)


if __name__ == '__main__':
    unittest.main()
