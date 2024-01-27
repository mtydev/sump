import logging, sys
import threading
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import argparse
import pyfiglet
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.support.wait import WebDriverWait

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url", help="provides site url")
parser.add_argument("-k", "--keywords", help="keywords that you want to see, needs to be a txt file")
parser.add_argument("-o", "--output", help="name a output txt file, where links from finished query will be provided")
args = parser.parse_args()


def print_logo():
    logo = pyfiglet.figlet_format('| SUMP |', font='speed')
    print(logo)


class Sump:
    def __init__(self, url, keywords_file, output_filename):
        self.original_window = None
        self.driver = None
        self.keywords = None
        self.output_filename = output_filename
        self.keywords_file = keywords_file
        self.url = url
        if not url or not keywords_file or not output_filename:
            raise ValueError("All arguments must be provided: url, keywords_file, output_filename")

    def read_keywords(self):
        with open(self.keywords_file, 'r') as f:
            self.keywords = f.read().split(',')

    def print_output(self, auction_title, auction_url):
        output_file = open(f'{self.output_filename}', 'a')
        output_file.write(f'{auction_title} : {auction_url}\n')

    def refuse_cookies(self):
        self.driver.find_element(By.ID, 'onetrust-pc-btn-handler').click()
        self.driver.find_element(By.CLASS_NAME, 'ot-pc-refuse-all-handler').click()

    def search_for_keywords(self, auction_urls, timeout):
        self.read_keywords()

        def search_in_auction(url):
            self.driver.switch_to.new_window('tab')
            self.driver.get(url)
            try:
                content = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_all_elements_located((By.ID, 'text'))
                )
            except TimeoutException:
                self.driver.close()
                self.driver.switch_to.window(self.original_window)
                return False

            found = False
            for word in content:
                if word.text in self.keywords:
                    found = True
                    break
            self.driver.close()
            self.driver.switch_to.window(self.original_window)
            return found

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(search_in_auction, url): url for url in auction_urls}
            for future in as_completed(futures):
                url = futures[future]
                try:
                    result = future.result(timeout)
                except TimeoutError:
                    print(f"Timeout for url: {url}")
                    continue
                if result:
                    return True
            return False

    def get_auction_urls(self):
        auction_list = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="listing-grid"]')
        auctions_urls = []
        for item in auction_list:
            try:
                auctions = item.find_elements(By.TAG_NAME, 'a')
                for auction in auctions:
                    auction_title = auction.find_element(By.TAG_NAME, 'h6').text
                    auction_url = auction.get_attribute('href')
                    auctions_urls.append(auction_url)
            except NoSuchElementException:
                pass
        return auctions_urls

    def run(self):
        print_logo()
        self.driver = webdriver.Firefox()
        self.driver.get(self.url)
        self.driver.implicitly_wait(10)
        self.refuse_cookies()
        self.original_window = self.driver.current_window_handle
        assert len(self.driver.window_handles) == 1
        auction_urls = self.get_auction_urls()
        self.read_keywords()
        self.search_for_keywords(auction_urls, 10)
        self.driver.quit()


# TEST RUN
#   python ./main.py -u "https://www.olx.pl/motoryzacja/q-miska-olejowa-bmw-e87/" -k input.txt -o output.txt
#
if __name__ == '__main__':
    try:
        Sump(args.url, args.keywords, args.output).run()
    except ValueError as e:
        print(f"Error: {e}")
        print_logo()
        parser.print_help()
