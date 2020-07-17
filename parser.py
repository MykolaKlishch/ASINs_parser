import re


class Parser:

    def __init__(self, raw_html):
        self.raw_html = raw_html

    def _find_with_regex(self, regex):
        flags = re.UNICODE
        compiled_regex = re.compile(regex, flags=flags)
        matches_found = compiled_regex.findall(self.raw_html)
        # findall is used instead of search to check for multiple entries
        if len(matches_found) > 1:
            assert len(set(matches_found)) == 1
        print(matches_found)
        return matches_found.pop()


class ProductInfoParser(Parser):

    def __init__(self, raw_html):
        super().__init__(raw_html)
        # TODO currently all attributes are str.
        #  Some of them should be converted to int
        # TODO some strings have amp; in them
        #  add function to remove it and other similar things
        self.asin = self._find_with_regex(
            r'<input type="hidden" id="ASIN" name="ASIN" value="(.*?)">'
        )
        self.product_name = self._find_with_regex(
            r'<title>Amazon.com: (.*?)</title>'
        )
        self.ratings = self._find_with_regex(
            r'<span id="acrCustomerReviewText" '
            r'class="a-size-base">(.*?) ratings</span>'
        )
        self.average_rating = self._find_with_regex(
            r'<span id="acrPopover" class="reviewCountTextLinkedHistogram '
            r'noUnderline" title="(.*?) out of 5 stars">'
        )
        self.answered_questions = self._find_with_regex(
            r'<span class="a-size-base">\n'
            r'(.*?) answered questions\n'
            r'</span>'
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
