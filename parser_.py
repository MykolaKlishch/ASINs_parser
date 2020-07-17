import re
from html import unescape


class Parser:

    def __init__(self, raw_html):
        self.raw_html = unescape(raw_html)

    def _by_regex(self, regex, target_group=0,
                  convert_into=None, if_none_return=None):
        compiled_regex = re.compile(regex, flags=re.UNICODE)
        match_object = compiled_regex.search(self.raw_html)
        if match_object is None:
            return if_none_return
        match_group = match_object.groups()[target_group]
        if convert_into == float:
            return float(match_group.strip())
        elif convert_into == int:
            return int(match_group.replace(",", "").strip())
        else:
            return match_group


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
            convert_into=int
        )
        self.average_rating = self._by_regex(
            r'<span id="acrPopover" class="reviewCountTextLinkedHistogram '
            r'noUnderline" title="(.*?) out of 5 stars">',
            convert_into=float
        )
        self.answered_questions = self._by_regex(
            r'<span class="a-size-base">\n(.*?) answered questions\n</span>',
            convert_into=int, if_none_return=0
        )


class ProductReviewParser(Parser):

    def __init__(self, raw_html):
        super().__init__(raw_html)
        self.review_number = None
        self.positive_review = None
        self.critical_review = None


if __name__ == "__main__":
    import os

    filename = os.path.join(os.getcwd(), "cache", "B000Q5NG78.html")
    product_info_html = open(filename, mode="rt", encoding="utf-8").read()
    product_info = ProductInfoParser(product_info_html)
    print(product_info.asin)
    print(product_info.product_name)
    print(product_info.ratings)
    print(product_info.average_rating)
    print(product_info.answered_questions)

    # filename = os.path.join(os.getcwd(), "cache", "B000Q5NG78.html")
    # product_review_html = open(filename, mode="rt", encoding="utf-8").read()
    # product_reviews = ProductReviewParser(html)
    # print(product_reviews.review_number)
    # print(product_reviews.positive_review)
    # print(product_reviews.critical_review)
