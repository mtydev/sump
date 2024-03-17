import threading
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import argparse
import pyfiglet
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url", help="provides site url")
parser.add_argument("-k", "--keywords", help="keywords that you want to see", nargs='+'
                    , type=str)
parser.add_argument("-o", "--output", help="name an output txt file, where links from finished query will be provided")
parser.add_argument("-v", "--verbose", help="verbose mode for showing processes in terminal", action='store_true')
args = parser.parse_args()


def print_logo():
    logo = pyfiglet.figlet_format('| SUMP |', font='speed')
    print(logo)


class Sump:
    def __init__(self, url, keywords_file, output_filename):
        self.original_window = None
        self.driver = None
        self.keywords = args.keywords
        self.output_filename = output_filename
        self.keywords_file = keywords_file
        self.url = url
        self.data = {
            "Name": [],
            "URL": [],
            "Keyword": [],
            "Price": []
        }
        if not url or not keywords_file or not output_filename:
            raise ValueError("All arguments must be provided: url, keywords_file, output_filename")

    def initialize_driver(self):
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        options.add_argument('--window-size=1200x600')
        self.driver = webdriver.Firefox(options=options)
        self.driver.get(self.url)
        self.driver.implicitly_wait(10)
        self.refuse_cookies()

    def make_csv(self, output_filename):
        df = pd.DataFrame(self.data)
        df.to_csv(output_filename)

    def append_dictionary(self, auction_url, keyword, auction_name, price):

        self.data["Name"].append(auction_name)
        self.data["URL"].append(auction_url)
        self.data["Keyword"].append(keyword)
        self.data["Price"].append(price)

    def refuse_cookies(self):
        self.driver.find_element(By.ID, 'onetrust-pc-btn-handler').click()
        self.driver.find_element(By.CLASS_NAME, 'ot-pc-refuse-all-handler').click()

    def search_for_keywords(self, auction_urls):

        def process_source(auction_url):

            response = requests.get(auction_url)
            page_source = response.text
            soup = BeautifulSoup(page_source, 'html.parser')

            for keyword in self.keywords:
                if keyword in soup.get_text():
                    cash = 'No data'
                    auction_name = 'Not found'
                    if "otomoto" in auction_url:
                        currency = soup.find('p', {'class': 'offer-price__currency'}).text
                        cash = soup.find('h3', {'class': 'offer-price__number'}).text + "" + currency
                        cash.strip()
                        auction_name = soup.find('h3', {'class': 'offer-title'}).text
                    else:
                        for price in soup.select('[data-testid="ad-price-container"]'):
                            cash = price.find("h3").text.replace("zł", "PLN").strip()
                        for title_container in soup.select('[data-cy="ad_title"]'):
                            auction_name = title_container.find("h4").text
                    if args.verbose:
                        print(f"Found keyword: {keyword} for {auction_url} Title: {auction_name}. Price : {cash} \n")
                    self.append_dictionary(auction_url, keyword, auction_name, cash)

        threads = []

        for url in auction_urls:
            t = threading.Thread(target=process_source, args=(url,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def get_auction_urls(self):
        auction_list = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="listing-grid"]')
        auctions_urls = []
        for item in auction_list:
            try:
                auctions = item.find_elements(By.TAG_NAME, 'a')
                for auction in auctions:
                    auction_url = auction.get_attribute('href')
                    auctions_urls.append(auction_url)
            except NoSuchElementException:
                pass
        return auctions_urls

    def run(self):
        print_logo()
        self.initialize_driver()
        self.original_window = self.driver.current_window_handle
        assert len(self.driver.window_handles) == 1
        auction_urls = self.get_auction_urls()
        self.search_for_keywords(auction_urls)
        self.make_csv(self.output_filename)
        print("Finished!")
        self.driver.quit()


if __name__ == '__main__':
    try:
        Sump(args.url, args.keywords, args.output).run()
    except ValueError as e:
        print(f"Error: {e}")
        print_logo()
        parser.print_help()

# TODO:
#   - add multiple auction sites handling
