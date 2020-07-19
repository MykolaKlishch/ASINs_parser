# TODO add docstring - it will be used as description
#  in ArgumentParser object as well

import argparse
import csv
import os
from datetime import datetime
from typing import Union, List

from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, Float,
                        String, DateTime, ForeignKey)

from _parsers import ProductInfoParser, ProductReviewParser
from _scrapers import ProductInfoScraper, ProductReviewsScraper


def get_filename_from_cmd(args: Union[List[str], None] = None) -> str:
    """Get the filename as command line argument -i.
    :param args: List of strings to parse. If args is None, sys.argv is used
    :return: filename
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", type=valid_filename,
                        default=os.path.join(os.getcwd(), "Asins sample.csv"),
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


# todo remove redundant functions!!!
def scrape_parse_and_print(asins, scraper_class, parser_class):
    """Can be called for diagnostics."""
    scraper = scraper_class()
    html_generator = scraper.scrape_many(asins)
    for asin, html in html_generator:
        if html is not None:
            parser = parser_class()
            parser.parse(html)
            parser.print_parsing_results()


def format_db_url(
        dialect="postgresql",
        driver="psycopg2",
        username="postgres",  # input("password: ").strip(),
        password="kgz4f7ZahFc0LghRwMKX",  # input("password: ").strip(),
        # todo Change password for the master DB instance user after testing!.
        host="asins-db-instance.cvkioejijss6.eu-central-1.rds.amazonaws.com",
        port="5432",
        database="postgres"
):
    # print("Type your credentials to connect"
    #       "to the Amazon RDS DB instance:")
    db_url = f"{dialect}+{driver}://{username}:{password}" \
          f"@{host}:{port}/{database}"
    return db_url


def test_engine(engine):
    with engine.connect() as conn:
        query_results = conn.execute("""SELECT now()""")
        for query_result in query_results:
            print(query_result)


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
            connection.execute(
                asins_table.insert().values(
                    asin=asin,
                    recorded_at=datetime.now()
                )
            )

        scraper = ProductInfoScraper()
        html_generator = scraper.scrape_many(asins)
        for asin, html in html_generator:
            if html is not None:
                parser = ProductInfoParser()
                parser.parse(html)
                parser.print_parsing_results()
                parser.upload_to_db(conn=connection, asin=asin,
                                    table=product_info_table)

        scraper = ProductReviewsScraper()
        html_generator = scraper.scrape_many(asins)
        for asin, html in html_generator:
            if html is not None:
                parser = ProductReviewParser()
                parser.parse(html)
                parser.print_parsing_results()
                parser.upload_to_db(conn=connection, asin=asin,
                                    table=product_reviews_table)

        print("Selecting uploaded rows...")
        select_statement = asins_table.select()
        select_result = connection.execute(select_statement)
        for row in select_result:
            print("&&| ", row)

        print("Selecting uploaded rows...")
        select_statement = product_info_table.select()
        select_result = connection.execute(select_statement)
        for row in select_result:
            print("&&| ", row)

        print("Selecting uploaded rows...")
        select_statement = product_info_table.select()
        select_result = connection.execute(select_statement)
        for row in select_result:
            print("&&| ", row)

    exit()  # todo remove after completing

    scrape_parse_and_print(
        asins=asins,
        scraper_class=ProductInfoScraper,
        parser_class=ProductInfoParser
    )
    scrape_parse_and_print(
        asins=asins,
        scraper_class=ProductReviewsScraper,
        parser_class=ProductReviewParser
    )


if __name__ == "__main__":
    main()
