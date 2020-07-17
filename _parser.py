import re
from html import unescape


def to_int(match_string):
    """Can convert strings like 1,234 to int (1234)"""
    return int(match_string.replace(",", "").strip())


def to_float(match_string):
    return float(match_string.strip())


class Parser:

    """Parser class with 2 methods for parsing 2 kinds of html
    (results saved in the same object). Parsing is done with regexes.
    """

    def __init__(self):
        self.raw_html = None
        self.asin = None
        self.product_name = None
        self.total_ratings = None
        self.average_rating = None
        self.answered_questions = None
        self.total_reviews = None
        self.positive_reviews = None
        self.critical_reviews = None

    def _by_regex(self, regex, target_group=0, *,
                  convert=None, if_none_return=None):
        """Method used to extract values for all attributes
        from raw html. Regexes differ, logic remains the same
        :param regex: regular expression that is used for extraction
        :param target_group: which group to retrieve (if regexes has
        multiple groups)
        :param convert: function to convert extracted string
        :param if_none_return: value to return if no match found
        :return: extracted [and transformed] value or if_none_return value.
        """
        match_object = re.search(regex, self.raw_html, flags=re.UNICODE)
        if match_object is None:
            return if_none_return
        match_group = match_object.groups()[target_group]
        if convert is None:
            return match_group
        return convert(match_group)

    def parse_product_info(self, raw_html):
        self.raw_html = unescape(raw_html)
        self.asin = self._by_regex(
            r'<input type="hidden" id="ASIN" name="ASIN" value="(.*?)">'
        )
        self.product_name = self._by_regex(
            r'<title>(Amazon.com\s?:\s?)?(.+?)( - - Amazon.com)?<\/title>',
            target_group=1
        )
        self.total_ratings = self._by_regex(
            r'<span id="acrCustomerReviewText" '
            r'class="a-size-base">(.*?) ratings<\/span>',
            convert=to_int
        )
        self.average_rating = self._by_regex(
            r'<span id="acrPopover" class="reviewCountTextLinkedHistogram '
            r'noUnderline" title="(.*?) out of 5 stars">',
            convert=to_float
        )
        self.answered_questions = self._by_regex(
            r'<span class="a-size-base">\n'
            r'(.*?)\+? answered questions\n<\/span>',
            convert=to_int, if_none_return=0
        )

    def parse_product_reviews(self, raw_html):
        self.raw_html = unescape(raw_html)
        self.total_reviews = self._by_regex(
            r'Showing [-\d]+ of (.*?) reviews',
            convert=to_int, if_none_return=0
        )
        self.positive_reviews = self._by_regex(
            r'See all (.*?) positive reviews',
            convert=to_int, if_none_return=0
        )
        self.critical_reviews = self._by_regex(
            r'See all (.*?) critical reviews',
            convert=to_int, if_none_return=0
        )

    def show_parsing_results(self):
        """to be called after parsing for - diagnostics"""
        print("# asin:\t\t\t\t\t", self.asin)
        print("# product_name:\t\t\t", self.product_name)
        print("# ratings:\t\t\t\t", self.total_ratings)
        print("# average_rating:\t\t", self.average_rating)
        print("# answered_questions:\t", self.answered_questions)
        print("$ total_reviews\t\t\t", self.total_reviews)
        print("$ positive_reviews\t\t", self.positive_reviews)
        print("$ critical_reviews\t\t", self.critical_reviews)
