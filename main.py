"""This script performs the following:
1.  Download ASINs list from a CSV file and saves them in the database.
2.  Scrapes product web pages for each ASIN, parses them and saves
    the following info in the database:
      * product name;
      * total ratings;
      * average rating;
      * number of answered questions;
3. Scrapes web pages with product reviews for each ASIN, parses them and saves
    the following info in the database:
      * total reviews;
      * number of positive reviews;
      * number of critical_reviews.
"""

import argparse
import csv
import os
import re
from datetime import datetime
from typing import Union, List, Iterable, Any

from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, Float,
                        String, DateTime, ForeignKey)

from parsers import ProductInfoParser, ProductReviewsParser
from scrapers import ProductInfoScraper, ProductReviewsScraper

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
        asins = sorted(set(map(list.pop, reader)))
        return asins


def format_db_url(
        dialect="postgresql",
        driver="psycopg2",
        host="asins-db-instance.cvkioejijss6.eu-central-1.rds.amazonaws.com",
        port="5432",
        database="postgres"
) -> str:
    print("Type your credentials to connect "
          "to the Amazon RDS DB instance:")
    username = input("username: ").strip()
    password = input("password: ").strip()
    db_url = \
        f"{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}"
    return db_url


def scrape_parse_print_and_insert(asins, *, scraper_class,
                                  parser_class, table, connection):
    """For a given list of ASINs, performs full cycle of scraping,
    parsing and data uploading.

    :param asins: list of ASINs
    :param scraper_class: scraper class to be used
    :param parser_class: parser class to be used
    :param table: a table for saving parsing results
    :param connection: sqlalchemy.engine.Connection instance
    :return: None
    """
    scraper = scraper_class()
    html_generator = scraper.scrape_many(asins)
    for asin, html in html_generator:
        if html is not None:
            parser = parser_class()
            parser.parse(html)
            parser.print_parsing_results()
            parser.upload_to_db(conn=connection, asin=asin, table=table)


def proceed_or_exit():
    inp_msg = ("\nData for all ASINs have been scraped, parsed and uploaded "
               "to the database. \nWould you like to print the contents "
               "of the tables? (y|n)\n")
    while True:
        choice = input(inp_msg).strip()
        if choice in "Nn":
            exit()
        elif choice in "Yy":
            break
        else:
            inp_msg = "Press (y|n) to choose"


def select_and_print(table, connection):
    print(f"\nSelecting all rows from '{table.name}' table...\n")
    selected_rows = connection.execute(table.select())
    pretty_print_query_result(
        headers=[str(full_coll_name).split(".")[-1]
                 for full_coll_name in table.columns],
        records=selected_rows
    )


def pretty_print_query_result(headers, records, truncate_after=26):
    """Prints query result as a table.
    Automatically detects column width.
    """
    def _align_fields(column: Iterable[Any]) -> Iterable[str]:
        """Transforms all values in the column
        into str type and unifies their length.
        """
        def _align_cell(field: str) -> str:
            if max_length <= truncate_after:
                return f"{field: ^{max_length}}"
            elif len(field) > truncate_after:
                field = field[:truncate_after] + '...'
            return f"{field: ^{truncate_after + 3}}"

        column_str_only = tuple(map(str, column))
        max_length = max(map(len, column_str_only))
        return map(_align_cell, column_str_only)

    def _join_row(row: Iterable[str]) -> str:
        return " │ ".join(row)

    columns = zip(headers, *records)
    columns_aligned = map(_align_fields, columns)
    records_aligned = zip(*columns_aligned)
    records_strings = map(_join_row, records_aligned)
    headers_aligned = next(records_strings)
    header_body_sep = re.sub(
        "│", "┼", re.sub("[^│]", "─", headers_aligned))
    print(headers_aligned, header_body_sep,
          *records_strings, sep="\n")


def main():

    csv_filename = get_filename_from_cmd()
    asins = get_asins_from_csv_file(csv_filename)

    db_url = format_db_url()
    print("Creating an engine...")
    engine = create_engine(db_url)

    print("Creating database schema...")
    metadata = MetaData()
    asins_table = Table(
        "asins", metadata,
        Column("asin", String, primary_key=True),
        Column("recorded_at", DateTime),
    )
    product_info_table = Table(
        "product_info", metadata,
        Column("id", Integer, primary_key=True),
        Column("recorded_at", DateTime),
        Column("asin", String, ForeignKey("asins.asin")),
        Column("product_name", String),
        Column("total_ratings", Integer),
        Column("average_rating", Float),
        Column("answered_questions", Integer),
    )
    product_reviews_table = Table(
        "product_reviews", metadata,
        Column("id", Integer, primary_key=True),
        Column("recorded_at", DateTime),
        Column("asin", String, ForeignKey("asins.asin")),
        Column("total_reviews", Integer),
        Column("positive_reviews", Integer),
        Column("critical_reviews", Integer)
    )
    product_reviews_table.drop(bind=engine, checkfirst=True)
    product_info_table.drop(bind=engine, checkfirst=True)
    asins_table.drop(bind=engine, checkfirst=True)
    asins_table.create(bind=engine)
    product_info_table.create(bind=engine)
    product_reviews_table.create(bind=engine)

    print("Connecting to the database...")
    with engine.connect() as connection:

        for asin in asins:
            connection.execute(asins_table.insert().values(
                asin=asin, recorded_at=datetime.now()))
        scrape_parse_print_and_insert(
            asins=asins,
            scraper_class=ProductInfoScraper,
            parser_class=ProductInfoParser,
            table=product_info_table,
            connection=connection
        )
        scrape_parse_print_and_insert(
            asins=asins,
            scraper_class=ProductReviewsScraper,
            parser_class=ProductReviewsParser,
            table=product_reviews_table,
            connection=connection
        )

        proceed_or_exit()

        select_and_print(
            table=asins_table,
            connection=connection
        )
        select_and_print(
            table=product_info_table,
            connection=connection
        )
        select_and_print(
            table=product_reviews_table,
            connection=connection
        )


if __name__ == "__main__":
    main()
