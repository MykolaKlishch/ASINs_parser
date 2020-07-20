import os
import requests
import time
from typing import Iterable, Sequence, Tuple, Union, NoReturn


class AbstractScraper:

    """This abstract class provide two methods to scrape webpages by ASIN(s).
    The class should be subclassed!!! Features (available in subclasses):
      * scraping for a single ASIN using or multiple ASINs at once
        (using generator) with ProductInfoScraper.scrape_one() and
        ProductInfoScraper.scrape_many() methods respectively;
      * adaptive delay between requests;
      * scraping is performed with the help or Zenscrape API;
      * scraped pages can be cached in order to save request attempts
        (Zenscrape API key (free tier) has a limit of 1000 requests/month);
      * default caching directory can be overridden when creating
        new parser instances;
      * to disable cache, set use_cache=False when calling scraping methods;
      * default Zenscrape API key is provided but can be changed
        when creating new instances;
      * ASINS that were not scraped for the first time are saved in
        ProductInfoScraper.unscraped_asins
      * Invalid ASINs (i.e. response with status code 404) are logged in
        ProductInfoScraper.invalid_asins
    Overriding 2 class-level attributes from superclass provides different
    behaviour of scraping methods - they retrieve different webpages
    for the same ASIN and cache them under different names.
    """

    target_url_template = None
    cache_file_template = None
    zenscrape_url = "https://app.zenscrape.com/api/v1/get"

    def __init__(
        self,
        apikey="132cacd0-c680-11ea-94f3-3173ea3a9b75",
        cache_dir=os.path.join(os.getcwd(), "cache"),
        initial_delay=0, delay_delta=10
    ):
        self.apikey = apikey
        self.cache_dir = cache_dir
        self.asin = None
        self.cache_file = None
        self.delay = initial_delay
        self.delay_delta = delay_delta
        self.unscraped_asins = []
        self.invalid_asins = []

    def scrape_many(self, asins: Sequence[str], 
                    *, use_cache=True, max_iterations=5,
                    ) -> Iterable[Tuple[str, str]]:
        """Method is a generator which yields tuples. Each tuple
        consists of ASIN and html of a scraped web page.

        At the first scraping iteration, it tries to scrape web pages
        for all ASINs that were passed to it. If the scraping for any
        ASIN was unsuccessful or ASIN appeared to be invalid (response
        status code was 404), generator does not yield anything.

        If webpages for some ASINs were not scraped, the method loads
        the list of unscraped ASINs from the previous iteration and
        tries to scrape the web pages for them in the next iteration.
        If invalid ASIN appeared in the original list, scraping attempt
        for it is not repeated.

        Generator stops if the web pages for all valid ASINs have been
        scraped or if it completed max number of iterations allowed.

        :param asins: sequence of ASINs for scraping;
        :param use_cache: if True: 1) raw html is being retrieved
        from cached files and 2) scraped pages are being cached;
        :param max_iterations: highest number of scraping iterations allowed
        :return: iterable of tuples (asin, html)
        and None values (for unsuccessful scraping).
        """
        scraping_iteration = 1
        while asins and scraping_iteration <= max_iterations:
            self.unscraped_asins.clear()
            print(f"\nScraping iteration {scraping_iteration} "
                  f"({len(asins)} ASIN(s) to scrape):")
            for number, asin in enumerate(asins):
                print(f"\nASIN {asin} ({number + 1} of {len(asins)}):")
                product_html = self.scrape_one(
                    asin, use_cache=use_cache, last=(number + 1 == len(asins)))
                if product_html is not None:
                    yield asin, product_html
            asins = self.unscraped_asins[:]
            scraping_iteration += 1

    def scrape_one(self, asin: str,
                   *, use_cache=True, last=False) -> Union[str, None]:
        """Performs scraping for a single ASIN.

        :param asin: ASIN for scraping
        :param use_cache: if True: 1) raw html is being retrieved
        from cached files and 2) scraped pages are being cached;
        :param last: if method is called from scrape_many, and this asin
        is the last one, no delay is required
        :return: raw html (for successful scraping)
        or None (for unsuccessful scraping)
        """
        self.asin = asin
        if use_cache:
            self._set_cache_filename()
            if not os.path.exists(self.cache_dir):
                os.mkdir(self.cache_dir)
        if use_cache and self._already_cached():
            product_html = self._get_product_html_from_cache()
            print(f"Page for ASIN {self.asin} retrieved from cache.")
        else:
            print(f"Scraping page for ASIN {self.asin}...")
            product_html = self._get_product_html_from_web()
            if self.asin in self.unscraped_asins:
                print(f"Couldn't retrieve product page for ASIN {self.asin}")
            elif self.asin in self.invalid_asins:
                print(f"Product with ASIN {self.asin} does not exist!")
            elif product_html is not None:
                print(f"Page for ASIN {self.asin} retrieved successfully!")
                if use_cache:
                    self._cache_product_html(product_html)
            if not last:
                print(f"Next request after {self.delay} seconds...")
                time.sleep(self.delay)
        return product_html

    def _set_cache_filename(self) -> NoReturn:
        self.cache_file = os.path.join(
            self.cache_dir, self.cache_file_template.format(self.asin))

    def _already_cached(self) -> bool:
        return os.path.isfile(self.cache_file)

    def _get_product_html_from_cache(self) -> str:
        with open(file=self.cache_file, mode="rt", encoding="utf-8-sig") as f:
            product_html = f.read()
            return product_html

    def _get_product_html_from_web(self) -> Union[str, None]:
        """Makes request, modifies Scraper instance
        attributes and returns raw html or None

        :return: raw html (for successful scraping)
        or None (for unsuccessful scraping)
        """
        try:
            response = requests.get(
                url=self.zenscrape_url, timeout=60,
                headers={"apikey": self.apikey},
                params={"url": self.target_url_template.format(self.asin)})
        except requests.exceptions.ReadTimeout:
            return None
        self._adjust_delay_and_update_logs(response)
        if self.asin not in self.unscraped_asins + self.invalid_asins:
            return response.text
        return None

    def _adjust_delay_and_update_logs(
            self, response: requests.Response) -> NoReturn:
        """Modifies Scraper's instance delay and updates its logging
        attributes (self.unscraped_asins and self.invalid_asins)
        based on HTTP response:
        1. Logs ASIN as invalid if response status code is 404.
        2. Logs ASINs for unsuccessful attempts as well.
        3. Decreases delay after successful request (status code is 200
        and the text can be passed to parser).
        4. Increases delay after unsuccessful request. Request is
        considered unsuccessful if a) status code is neither 200
        nor 404 or b) status code is 200 but the text from response
        cannot be passed to parser because its contents are different
        from expected.

        :param response: requests.Response instance to be analyzed.
        :return: None
        """
        status = response.status_code
        if status == 200 and self._text_is_ok(response.text):
            if self.delay >= self.delay_delta:
                self.delay -= self.delay_delta
        if (status == 200 and not self._text_is_ok(response.text)
                or status not in (200, 404)):
            self.unscraped_asins.append(self.asin)
            self.delay += self.delay_delta
        if status == 404:
            self.invalid_asins.append(self.asin)

    @staticmethod
    def _text_is_ok(response_text) -> bool:
        """Checks text for response with status code == 200.

        :return True if the text can be passed to parser, False otherwise.
        """
        exhausted = ('{"error":"Not enough requests."}' in response_text)
        no_apikey = ('{"error":"No apikey provided."}' in response_text)
        is_captcha_request = (
            "Sorry, we just need to make sure you're not a robot."
            in response_text)
        return not (exhausted or no_apikey or is_captcha_request)

    def _cache_product_html(self, product_html: str) -> NoReturn:
        f_handle = open(file=self.cache_file, mode="wt", encoding="utf-8-sig")
        f_handle.write(product_html)


class ProductInfoScraper(AbstractScraper):
    """Overriding 2 class-level attributes from superclass provides
    the ability to scrape product info data by ASIN(s).
    """
    target_url_template = "https://www.amazon.com/dp/{}"
    cache_file_template = "{}.html"


class ProductReviewsScraper(AbstractScraper):
    """Overriding 2 class-level attributes from superclass provides
    the ability to scrape product reviews data by ASIN(s).
    """
    target_url_template = "https://www.amazon.com/product-reviews/{}"
    cache_file_template = "reviews-{}.html"
