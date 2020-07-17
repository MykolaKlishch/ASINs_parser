import re
from html import unescape


def to_int(match_string):
    return int(match_string.replace(",", "").strip())


def to_float(match_string):
    return float(match_string.strip())


class Parser:

    def __init__(self, raw_html):
        self.raw_html = unescape(raw_html)

    def _by_regex(self, regex, target_group=0, *,
                  convert=None, if_none_return=None):
        match_object = re.search(regex, self.raw_html, flags=re.UNICODE)
        if match_object is None:
            return if_none_return
        match_group = match_object.groups()[target_group]
        if convert is None:
            return match_group
        return convert(match_group)


class ProductInfoParser(Parser):

    def __init__(self, raw_html):
        super().__init__(raw_html)
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


class ProductReviewParser(Parser):

    def __init__(self, raw_html):
        super().__init__(raw_html)
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
