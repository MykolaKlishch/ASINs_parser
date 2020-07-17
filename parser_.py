import re
from html import unescape


class Parser:

    def __init__(self, raw_html):
        self.raw_html = unescape(raw_html)

    def _find_with_regex(self, regex, target_group=0):
        compiled_regex = re.compile(regex, flags=re.UNICODE)
        match_object = compiled_regex.search(self.raw_html)
        if match_object is None:
            return None
        return match_object.groups()[target_group]


class ProductInfoParser(Parser):

    def __init__(self, raw_html):
        super().__init__(raw_html)
        self.asin = self._find_with_regex(
            r'<input type="hidden" id="ASIN" name="ASIN" value="(.*?)">'
        )
        self.product_name = self._find_with_regex(
            r'<title>(Amazon.com\s?:\s?)?(.+?)( - - Amazon.com)?</title>',
            target_group=1
        )
        self.ratings = self._get_ratings()
        self.average_rating = self._get_average_rating()
        self.answered_questions = self._get_answered_questions()

    def _get_ratings(self):
        ratings_str = self._find_with_regex(
            r'<span id="acrCustomerReviewText" '
            r'class="a-size-base">(.*?) ratings</span>'
        )
        if ratings_str is None:
            return None
        ratings_int = int(ratings_str.replace(",", "").strip())  # todo try except
        return ratings_int

    def _get_average_rating(self):
        average_rating_str = self._find_with_regex(
            r'<span id="acrPopover" class="reviewCountTextLinkedHistogram '
            r'noUnderline" title="(.*?) out of 5 stars">'
        )
        if average_rating_str is None:
            return None
        average_rating_float = float(average_rating_str.strip())  # todo try except
        return average_rating_float

    def _get_answered_questions(self):
        answered = self._find_with_regex(
            r'<span class="a-size-base">\n(.*?) answered questions\n</span>'
        )
        if answered is None:
            return 0
        answered_int = int(answered.replace(",", "").strip())
        return answered_int


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
