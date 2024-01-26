import logging, sys
import threading
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import argparse
import pyfiglet

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url", help="provides site url")
parser.add_argument("-k", "--keywords", help="keywords that you want to see, needs to be a txt file", type=argparse.FileType('r'))
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

    def make_output(self, auction_title, auction_url):
        output_file = open(f'{self.output_filename}', 'a')
        output_file.write(f'{auction_title} : {auction_url}\n')

    def refuse_cookies(self):
        self.driver.find_element(By.ID, 'onetrust-pc-btn-handler').click()
        self.driver.find_element(By.CLASS_NAME, 'ot-pc-refuse-all-handler').click()

    def search_for_keywords(self, auction_search_urls, search_keywords):
        for auction_search_url in auction_search_urls:
            self.driver.switch_to.new_window('tab')
            self.driver.get(auction_search_url)
            content = self.driver.find_elements(By.ID, 'text')
            for word in content:
                if word.text in search_keywords:
                    return True
                else:
                    return False
            self.driver.close()
            self.driver.switch_to.window(self.original_window)

    def get_auction_urls(self):
        auction_list = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="listing-grid"]')
        for item in auction_list:
            try:
                auctions = item.find_elements(By.TAG_NAME, 'a')
                auctions_urls = []
                for auction in auctions:
                    auction_title = auction.find_element(By.TAG_NAME, 'h6').text
                    auction_url = auction.get_attribute('href')
                    auctions_urls.append(auction_url)
                if self.search_for_keywords(auctions_urls, self.keywords):
                    self.make_output(auction_title, auction_url)
                else:
                    pass
            except NoSuchElementException:
                pass

    def run(self):
        print_logo()
        self.driver = webdriver.Firefox()
        self.driver.get(self.url)
        self.driver.implicitly_wait(10)
        self.refuse_cookies()
        self.original_window = self.driver.current_window_handle
        assert len(self.driver.window_handles) == 1
        self.get_auction_urls()
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
