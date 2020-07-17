import os
import requests
import time
from typing import Union, NoReturn


class ProductInfoScraper:

    def __init__(
        self,
        apikey="132cacd0-c680-11ea-94f3-3173ea3a9b75",
        zenscrape_url="https://app.zenscrape.com/api/v1/get",
        target_url_template="https://www.amazon.com/dp/{asin}"
            # ProductReviewsParser will have different target_url_template
    ):
        self.apikey = apikey
        self.zenscrape_url = zenscrape_url
        self.target_url_template = target_url_template
        self.asin = None  # scraper doesn't know about asins
        # untill they are passed by the respective methods
        self.cache_file = None
        self.delay = 60
        self.delay_delta = 10
        self.cache_dir = None
        self.retry_list = []

    def _create_cache_folder(self, folder_name: str = "cache"):
        self.cache_dir = os.path.join(os.getcwd(), folder_name)
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)

    def _set_cache_filename(self):
        self.cache_file = os.path.join(self.cache_dir, f"{self.asin}.html")

    def _already_cached(self) -> bool:
        return os.path.isfile(self.cache_file)

    def _get_product_html_from_cache(self):
        f_handle = open(file=self.cache_file, mode="rt", encoding="utf-8-sig")
        product_html = f_handle.read()
        return product_html

    def _cache_product_html(self, product_html: str) -> NoReturn:
        f_handle = open(file=self.cache_file, mode="wt", encoding="utf-8-sig")
        f_handle.write(product_html)

    def get_product_html_from_web(self) -> Union[str, None]:
        response = requests.get(
            url=self.zenscrape_url, timeout=60,
            headers={"apikey": self.apikey},
            params={"url": self.target_url_template.format(self.asin)})
        if response_is_valid(response):
            return response.text
        if response.status_code == 404:
            print(f"Product with ASIN {self.asin} does not exist! "
                  f"Retrying scraping for it doesn't make any sense!")
        return None

    @staticmethod
    def response_is_valid(response: requests.Response) -> bool:
        # todo implement specific behaviour for status_code 404
        #  (Error 404 means that product with such ASIN does not exist)
        status_is_ok = response.status_code == 200
        not_exhausted = (
            '{"error":"Not enough requests."}' not in response.text)
        key_provided = (
            '{"error":"No apikey provided."}' not in response.text)
        is_not_captcha_request = (
            "Sorry, we just need to make sure you're not a robot."
            not in response.text)
        return (
            status_is_ok and not_exhausted
            and key_provided and is_not_captcha_request
        )

    def scrape_one(self, asin, use_cache=True):
        if use_cache and self._already_cached():
            print(f"Product page for ASIN {asin} has already been saved.")
            product_html = self._get_product_html_from_cache()
        else:
            print(f"Scraping page for ASIN {self.asin}...")
            product_html = get_product_html_from_web(asin)
            if product_html is None:
                print(f"Couldn't retrieve product page for ASIN {asin}")
                self.retry_list.append(asin)
                self.delay += self.delay_delta
            else:
                print(f"Page for ASIN {self.asin} retrieved successfully!")
                if use_cache:
                    self._cache_product_html(product_html)
                if self.delay >= self.delay_delta:
                    self.delay -= self.delay_delta
        return product_html

    def scrape_many(self, asins, use_cache=True):
        if use_cache:
            self._create_cache_folder()
        for number, asin in enumerate(asins):

            self.asin = asin
            product_html = self.scrape_one(asin)
            yield product_html
            if number < len(asins):
                print(f"Next request after {self.delay} seconds...")
                time.sleep(self.delay)


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