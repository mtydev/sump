import threading
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import argparse
import pyfiglet

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url", help="provides site url")
parser.add_argument("-k", "--keywords", help="keywords that you want to see", nargs='+'
                    , type=str)
parser.add_argument("-o", "--output", help="name a output txt file, where links from finished query will be provided")
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
        if not url or not keywords_file or not output_filename:
            raise ValueError("All arguments must be provided: url, keywords_file, output_filename")

    def print_output(self, auction_url, keyword):
        output_file = open(f'{self.output_filename}', 'a')
        output_file.write(f'{keyword} : {auction_url}\n')

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
                    for price in soup.select('[data-testid="ad-price-container"]'):
                        cash = price.find("h3").text
                    print(f"Found keyword: {keyword} for {auction_url}. Price : {cash} \n")
                    self.print_output(auction_url, keyword)

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
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        options.add_argument('--window-size=1200x600')
        self.driver = webdriver.Firefox(options=options)
        self.driver.get(self.url)
        self.driver.implicitly_wait(10)
        self.refuse_cookies()
        self.original_window = self.driver.current_window_handle
        assert len(self.driver.window_handles) == 1
        auction_urls = self.get_auction_urls()
        self.search_for_keywords(auction_urls)
        self.driver.quit()


if __name__ == '__main__':
    try:
        Sump(args.url, args.keywords, args.output).run()
    except ValueError as e:
        print(f"Error: {e}")
        print_logo()
        parser.print_help()
