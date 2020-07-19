import re
from html import unescape
from typing import NoReturn


def to_int(match_string: str) -> int:
    """Can convert strings like 1,234 to int (1234)"""
    return int(match_string.replace(",", "").strip())


def to_float(match_string: str) -> float:
    return float(match_string.strip())


class AbstractParser:

    """A base class for regex parsers."""

    def __init__(self):
        self.raw_html = None

    def _parse_with_regex(self, regex: str, target_group=0, *,
                          convert=None, if_no_match_return=None):
        """Method used to extract values for any attributes
        from raw html. Regexes differ, logic remains the same.
        Attribytes and regexes should be defined in subclasses.

        :param regex: regular expression that is used for extraction;
        :param target_group: which group to retrieve (if regex has
        multiple groups);
        :param convert: function to convert extracted string;
        :param if_no_match_return: default value to return
        if no match found;
        :return: extracted value or default value.
        """
        match_object = re.search(regex, self.raw_html, flags=re.UNICODE)
        if match_object is None:
            return if_no_match_return
        match_group = match_object.groups()[target_group]
        if convert is None:
            return match_group
        return convert(match_group)


class ProductInfoParser(AbstractParser):

    """Instances of this class can be used to parse html with product info.
    Extracted values are saved as the instance attributes.
    """

    def __init__(self):
        super().__init__()
        self.asin = None
        self.product_name = None
        self.total_ratings = None
        self.average_rating = None
        self.answered_questions = None

    def parse(self, raw_html: str) -> NoReturn:
        """Extracts attribute values from raw html.

        :param raw_html: html to be parsed
        :return: None
        """
        self.raw_html = unescape(raw_html)
        self.product_name = self._parse_with_regex(
            r'<title>(Amazon.com\s?:\s?)?(.+?)( - - Amazon.com)?<\/title>',
            target_group=1
        )
        self.total_ratings = self._parse_with_regex(
            r'<span id="acrCustomerReviewText" '
            r'class="a-size-base">(.*?) ratings<\/span>',
            convert=to_int
        )
        self.average_rating = self._parse_with_regex(
            r'<span id="acrPopover" class="reviewCountTextLinkedHistogram '
            r'noUnderline" title="(.*?) out of 5 stars">',
            convert=to_float
        )
        self.answered_questions = self._parse_with_regex(
            r'<span class="a-size-base">\n'
            r'(.*?)\+? answered questions\n<\/span>',
            convert=to_int, if_no_match_return=0
        )

    def show_parsing_results(self) -> NoReturn:
        """Can be called after parsing for diagnostics."""
        print("# product_name:\t\t\t", self.product_name)
        print("# ratings:\t\t\t\t", self.total_ratings)
        print("# average_rating:\t\t", self.average_rating)
        print("# answered_questions:\t", self.answered_questions)


class ProductReviewParser(AbstractParser):

    """Instances of this class can be used to parse html with product
    reviews. Extracted values are saved as the instance attributes.
    """

    def __init__(self):
        super().__init__()
        self.total_reviews = None
        self.positive_reviews = None
        self.critical_reviews = None

    def parse(self, raw_html: str) -> NoReturn:
        """Extracts attribute values from raw html.

        :param raw_html: html to be parsed
        :return: None
        """
        self.raw_html = unescape(raw_html)
        self.total_reviews = self._parse_with_regex(
            r'Showing [-\d]+ of (.*?) reviews',
            convert=to_int, if_no_match_return=0
        )
        self.positive_reviews = self._parse_with_regex(
            r'See all (.*?) positive reviews',
            convert=to_int, if_no_match_return=0
        )
        self.critical_reviews = self._parse_with_regex(
            r'See all (.*?) critical reviews',
            convert=to_int, if_no_match_return=0
        )

    def show_parsing_results(self) -> NoReturn:
        """Can be called after parsing for diagnostics."""
        print("# total_reviews\t\t\t", self.total_reviews)
        print("# positive_reviews\t\t", self.positive_reviews)
        print("# critical_reviews\t\t", self.critical_reviews)
