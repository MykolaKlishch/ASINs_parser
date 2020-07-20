import re
from html import unescape
from typing import NoReturn
from datetime import datetime


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

    def print_parsing_results(self) -> NoReturn:
        """Can be called after parsing for diagnostics. Base class method
        is empty and should be overridden in subclasses.
        """
        pass

    def upload_to_db(self, conn, table, asin) -> NoReturn:
        """Uploads attributes of the parser instance to the specified
        table in the database specified by connection instance. Base
        class method is empty and should be overridden in subclasses.

        :param conn: sqlalchemy.engine.Connection instance
        :param table: sqlalchemy.sql.schema.Table instance. Column
        names must comply with the attributes of the instance.
        :param asin: parameter that is not present among the instance
        attributes and therefore should be passed to the method.
        :return: None
        """
        pass


class ProductInfoParser(AbstractParser):
    """Instances of this class can be used to parse html with product
    info. Extracted values are saved as the instance attributes.
    Parser can print the values of its attributes or load them
    to the database.
    """

    def __init__(self):
        super().__init__()
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
            r'<title>(Amazon.com\s*:\s*)?(.+?)(\s*- - Amazon.com)?<\/title>',
            target_group=1
        )
        self.total_ratings = self._parse_with_regex(
            r'<span id="acrCustomerReviewText" '
            r'class="a-size-base">(.*?) ratings<\/span>',
            convert=to_int, if_no_match_return=0
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

    def print_parsing_results(self) -> NoReturn:
        print(f" * {'product_name': <25}{self.product_name}")
        print(f" * {'total_ratings': <25}{self.total_ratings}")
        print(f" * {'average_rating': <25}{self.average_rating}")
        print(f" * {'answered_questions': <25}{self.answered_questions}")

    def upload_to_db(self, conn, table, asin) -> NoReturn:
        print("Uploading into the database...")
        conn.execute(
            table.insert().values(
                recorded_at=datetime.now(),
                asin=asin,
                product_name=self.product_name,
                total_ratings=self.total_ratings,
                average_rating=self.average_rating,
                answered_questions=self.answered_questions
            )
        )
        print("Uploaded successfully!")


class ProductReviewParser(AbstractParser):

    """Instances of this class can be used to parse html with product
    reviews. Extracted values are saved as the instance attributes.
    Parser can print the values of its attributes or load them
    to the database.
    """

    def __init__(self):
        super().__init__()
        self.total_reviews = None
        self.positive_reviews = None
        self.critical_reviews = None

    def parse(self, raw_html: str) -> NoReturn:
        """Extracts attribute values from raw html.

        DISCLAIMER: Sometimes there is only total number of reviews on
        the page or numbers of positive and critical reviews do not
        add up. Parser DOES NOT modify the values in such cases but
        leaves them as they are.

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

    def print_parsing_results(self) -> NoReturn:
        print(f" * {'total_reviews': <25}{self.total_reviews}")
        print(f" * {'positive_reviews': <25}{self.positive_reviews}")
        print(f" * {'critical_reviews': <25}{self.critical_reviews}")

    def upload_to_db(self, conn, table, asin) -> NoReturn:
        print("Uploading into the database...")
        conn.execute(
            table.insert().values(
                recorded_at=datetime.now(),
                asin=asin,
                total_reviews=self.total_reviews,
                positive_reviews=self.positive_reviews,
                critical_reviews=self.critical_reviews
            )
        )
        print("Uploaded successfully!")
