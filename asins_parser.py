# TODO add docstring - it will be used as description
#  in ArgumentParser object as well

import argparse
import csv
import os
from sqlalchemy import (
    create_engine, MetaData,
    Table, Column,
    Integer, String,
    ForeignKey,
)
import sys
from typing import Union, List

from _scrapers import ProductInfoScraper, ProductReviewsScraper
from _parser import Parser

DEFAULT_FILENAME = os.path.join(os.getcwd(), "Asins sample.csv")


def get_filename_from_cmd(args: Union[List[str], None] = None) -> str:
    """Get the filename as command line argument -i.
    :param args: List of strings to parse. If args is None, sys.argv is used
    :return: filename
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", type=valid_filename, default=DEFAULT_FILENAME,
                        help="Abs. or rel. filename of CSV file with ASINs.")
    arguments = parser.parse_args(args=args)
    filename = arguments.i
    return filename


def valid_filename(filename: str) -> str:
    """Used for validation of the command line argument -i.
    Checks if filename parameter is the name of existing file.

    :param filename: -i value
    :raise ArgumentTypeError: if validation fails
    """
    if not os.path.isfile(filename):
        raise argparse.ArgumentTypeError(
            f"'File '{filename}' does not exist!")
    return filename


def get_asins_from_csv_file(filename: str) -> List[str]:
    """Gets ASINs from CSV file. The file should not contain headers and
    ASINs should be stored in a single column.

    :param filename: pre-validated filename
    :return: List of ASINs
    """
    with open(file=filename, mode="rt", encoding="utf-8-sig") as file_handle:
        reader = csv.reader(file_handle)
        asins = list(map(list.pop, reader))
        return asins


def scrape_parse_and_print(asins, scraper_class):
    scraper = scraper_class()
    html_iterator = scraper.scrape_many(asins)
    for asin, html in html_iterator:
        if html is not None:
            parser = Parser()
            if isinstance(scraper, ProductInfoScraper):
                parser.parse_product_info(html)
            if isinstance(scraper, ProductReviewsScraper):
                parser.parse_product_reviews(html)
            parser.show_parsing_results()
    assert not scraper.unscraped_asins


def main():
    csv_filename = get_filename_from_cmd()
    asins = get_asins_from_csv_file(csv_filename)

    scrape_parse_and_print(
        asins=asins,
        scraper_class=ProductInfoScraper,
    )
    scrape_parse_and_print(
        asins=asins,
        scraper_class=ProductReviewsScraper,
    )

    # engine = create_engine(
    #     "postgres://postgres:1111@localhost:5432/postgres"
    # )
    # metadata = MetaData()
    # metadata.create_all(engine)


if __name__ == "__main__":
    main()
