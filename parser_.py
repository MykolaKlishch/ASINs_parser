import re
from html import unescape


def to_int(match_string):
    return int(match_string.replace(",", "").strip())


def to_float(match_string):
    return float(match_string.strip())


class Parser:

    def __init__(self, raw_html):
        self.raw_html = unescape(raw_html)

    def _by_regex(self, regex, target_group=0,
                  convert=None, if_none_return=None):
        compiled_regex = re.compile(regex, flags=re.UNICODE)
        match_object = compiled_regex.search(self.raw_html)
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
            r'<title>(Amazon.com\s?:\s?)?(.+?)( - - Amazon.com)?</title>',
            target_group=1
        )
        self.ratings = self._by_regex(
            r'<span id="acrCustomerReviewText" '
            r'class="a-size-base">(.*?) ratings</span>',
            convert=to_int
        )
        self.average_rating = self._by_regex(
            r'<span id="acrPopover" class="reviewCountTextLinkedHistogram '
            r'noUnderline" title="(.*?) out of 5 stars">',
            convert=to_float
        )
        self.answered_questions = self._by_regex(
            r'<span class="a-size-base">\n(.*?) answered questions\n</span>',
            convert=to_int, if_none_return=0
        )


class ProductReviewParser(Parser):

    def __init__(self, raw_html):
        super().__init__(raw_html)
        self.review_number = None
        self.positive_review = None
        self.critical_review = None
