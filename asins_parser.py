# TODO add docstring - it will be used as description
#  in ArgumentParser object as well

# todo rename this module
#  parser_.py is a good name but if this module is named asins_parser.py
#  it creates confusion

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
from typing import Union, List, Sequence, NoReturn

from scraper import scraping_generator
from parser_ import ProductInfoParser, ProductReviewParser

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


def validate_asins_list(asins_list: Sequence[str]) -> NoReturn:
    """Validates asins in the list: if they are unique
    and if all values are in proper format.

    :raise AssertionError: if validation fails.
    """
    # todo this function DOES NOT check if a particular ASIN actually exist
    #  It may be a valid reason to rename the function
    asins_set = set(asins_list)
    assert len(asins_list) == len(asins_set)
    assert "" not in asins_set
    for asin in asins_set:
        assert isinstance(asin, str)
        assert len(asin) == 10
        assert asin.strip() == asin


def main():
    csv_filename = get_filename_from_cmd(args=["-i", "Asins sample.csv"])
    asins = get_asins_from_csv_file(csv_filename)
    validate_asins_list(asins)
    # todo save them in database before scraping

    asins.remove("B01ETNF300")  # TEMPORARY!!!
    asins.remove("B07CRZQ9MY")  # TEMPORARY!!!
    # todo handle non-existing ASINS downstream

    html_iterator = scraping_generator(asins)
    print(html_iterator)
    for product_info_html in html_iterator:
        if product_info_html is not None:
            product_info = ProductInfoParser(product_info_html)
            print("# asin:\t\t\t\t", product_info.asin, sep="\t")
            print("# product_name:\t\t", product_info.product_name, sep="\t")
            print("# ratings:\t\t\t",
                  product_info.ratings,
                  type(product_info.ratings),
                  sep="\t")
            print("# average_rating:\t",
                  product_info.average_rating,
                  type(product_info.average_rating),
                  sep="\t")
            print("# answered_questions:",
                  product_info.answered_questions,
                  type(product_info.answered_questions),
                  sep="\t")

    # engine = create_engine(
    #     "postgres://postgres:1111@localhost:5432/postgres"
    # )
    # metadata = MetaData()
    # metadata.create_all(engine)


if __name__ == "__main__":
    main()
