import os
import requests
import time
from typing import Union, NoReturn


def create_cache_folder(folder_name: str) -> str:
    cache_dir = os.path.join(os.getcwd(), folder_name)
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)
    return cache_dir


def already_cached(abs_filename: str) -> bool:
    return os.path.isfile(abs_filename)


def get_product_html_from_file(abs_filename: str) -> str:
    file_handle = open(file=abs_filename, mode="rt", encoding="utf-8-sig")
    product_html = file_handle.read()
    return product_html


def cache_product_html(product_html: str, abs_filename: str) -> NoReturn:
    file_handle = open(file=abs_filename, mode="wt", encoding="utf-8-sig")
    file_handle.write(product_html)


def get_product_html_from_web(
        asin: str,
        apikey="132cacd0-c680-11ea-94f3-3173ea3a9b75") -> Union[str, None]:
    zenscrape_url = "https://app.zenscrape.com/api/v1/get"
    amazon_url = f"https://www.amazon.com/dp/{asin}"

    response = requests.get(
        url=zenscrape_url, timeout=60,
        headers={"apikey": apikey},
        params={"url": amazon_url}
    )
    if response_is_valid(response):
        return response.text
    if response.status_code == 404:
        print(f"Product with ASIN {asin} does not exist! "
              f"Retrying scraping for it doesn't make any sense!")
    return None


def response_is_valid(response: requests.Response) -> bool:
    # todo implement specific behaviour for status_code 404
    #  (Error 404 means that product with such ASIN does not exist)
    status_is_ok = response.status_code == 200
    not_exhausted = (
        '{"error":"Not enough requests."}'
        not in response.text
    )
    key_provided = (
        '{"error":"No apikey provided."}'
        not in response.text
    )
    is_not_captcha_request = (
        "Sorry, we just need to make sure you're not a robot."
        not in response.text
    )
    return (
        status_is_ok and not_exhausted
        and key_provided and is_not_captcha_request
    )

    # todo implement database caching instead temporary flat-file caching
    #  Or maybe it is better to leave this functionality -
    #  it allows manual checking
    #  and removes dependence on zenscrape scraping quota


def scraping_generator(asins):
    """Yields html for each asin in the list"""
    cache_dir = create_cache_folder("cache")
    delay = 60
    retry_list = []
    for number, asin in enumerate(asins):
        abs_filename = os.path.join(cache_dir, f"{asin}.html")
        if already_cached(abs_filename):
            print(f"\nProduct page for ASIN {asin} has already been saved.")
            product_html = get_product_html_from_file(abs_filename)
            yield product_html  # todo make a single yield
        else:
            print(f"\nScraping page for ASIN {asin} "
                  f"({number + 1} of {len(asins)})...")
            product_html = get_product_html_from_web(asin)
            if product_html is None:
                print(f"Couldn't retrieve product page for ASIN {asin}")
                retry_list.append(asin)
                delay += 10
            else:
                print(f"Page for ASIN {asin} retrieved successfully!")
                cache_product_html(product_html, abs_filename)
                if delay >= 10:
                    delay -= 10
            yield product_html
            if number < len(asins):
                print(f"Next request after {delay} seconds...")
                time.sleep(delay)
    if retry_list:
        print(f"\nPages for {len(retry_list)} ASIN(s) have not been scraped:")
        print(*retry_list, sep=", ")
        print("If you assume that products with such ASIN(s) do exist,\n"
              "you can retry scraping by restarting this module.")

        # todo create this database earlier to insert ASINs into it
        #  do not add invalid asins to database