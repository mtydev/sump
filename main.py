import argparse
import threading
import pandas as pd
import pyfiglet
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

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
        self.data = pd.DataFrame(columns=["Name", "URL", "Keyword", "Price", "Year of Production", "HP", "Mileage", "Gearbox type", "VIN", "Engine capacity", "Petrol"])
        if not url or not keywords_file or not output_filename:
            raise ValueError("All arguments must be provided: url, keywords_file, output_filename")

    class AuctionDataError(Exception):
        """Custom exception for auction data extraction errors."""
        pass

    def initialize_driver(self):
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        options.add_argument('--window-size=1200x600')
        self.driver = webdriver.Firefox(options=options)
        self.driver.get(self.url)
        # Waiting for site to load
        self.driver.implicitly_wait(10)
        self.refuse_cookies()
        self.original_window = self.driver.current_window_handle
        assert len(self.driver.window_handles) == 1

    def make_csv(self, output_filename: str):
        df = pd.DataFrame(self.data)
        df.to_csv(output_filename)

    def append_dictionary(self, auction_url, keyword, auction_name, price, prod_year, hp, mileage, gearbox, vin, engine_cap, petrol):
        new_row = {
            "Name": auction_name,
            "URL": auction_url,
            "Keyword": keyword,
            "Price": price,
            "Year of Production": prod_year,
            "HP": hp,
            "Mileage": mileage,
            "Gearbox type": gearbox,
            "VIN": vin,
            "Engine capacity": engine_cap,
            "Petrol": petrol
        }
        self.data = pd.concat([self.data, pd.DataFrame([new_row])], ignore_index=True)

    def refuse_cookies(self):
        self.driver.find_element(By.ID, 'onetrust-pc-btn-handler').click()
        self.driver.find_element(By.CLASS_NAME, 'ot-pc-refuse-all-handler').click()

    def search_for_keywords(self, auction_urls):

        def process_source(auction_url):

            response = requests.get(auction_url)
            page_source = response.text
            soup = BeautifulSoup(page_source, 'lxml')

            for keyword in self.keywords:
                if keyword in soup.get_text():
                    cash = 'No data'
                    auction_name = 'No data'
                    prod_year = 'No data'
                    hp = 'No data'
                    mileage = 'No data'
                    gearbox = 'No data'
                    vin = 'No data'
                    engine_cap = 'No data'
                    petrol = 'No data'
                    if "otomoto" in auction_url:
                        cash = soup.find('h3', {'class': 'offer-price__number'}).text.replace(" ", '')
                        auction_name = soup.find('h3', {'class': 'offer-title'}).text
                        for auction_parameters in soup.select('[data-testid="advert-details-item"]'):
                            if 'Rok produkcji' in auction_parameters.text:
                                prod_year = auction_parameters.text.replace("Rok produkcji", "")
                            if 'Moc' in auction_parameters.text:
                                hp = auction_parameters.text.replace("Moc", "")
                            if 'Przebieg' in auction_parameters.text:
                                mileage = auction_parameters.text.replace("Przebieg", "")
                            if 'Skrzynia biegów' in auction_parameters.text:
                                gearbox = auction_parameters.text.replace("Skrzynia biegów", "")
                            if 'Pojemność skokowa' in auction_parameters.text:
                                engine_cap = auction_parameters.text.replace("Pojemność skokowa", "")
                            if 'Rodzaj paliwa' in auction_parameters.text:
                                petrol = auction_parameters.text.replace("Rodzaj paliwa", "")

                    else:
                        for price in soup.select('[data-testid="ad-price-container"]'):
                            cash = price.find("h3").text.replace("zł", "").replace(" ", "")
                        for title_container in soup.select('[data-cy="ad_title"]'):
                            auction_name = title_container.find("h4").text
                        # CSS class changes sometimes, so better 'fool-proof' method is needed

                        # Checking if css class name is present
                        if soup.select_one('[class="css-px7scb"]'):
                            for auction_parameters in soup.select('[class="css-px7scb"]'):
                                for x in auction_parameters.find_all('p'):
                                    if "Rok produkcji:" in x.text:
                                        prod_year = x.text.replace("Rok produkcji:", "").strip()
                                    if "Moc silnika:" in x.text:
                                        hp = x.text.replace("Moc silnika:", "").strip()
                                    if "Przebieg:" in x.text:
                                        mileage = x.text.replace("Przebieg:", "").strip()
                                    if "Skrzynia biegów:" in x.text:
                                        gearbox = x.text.replace("Skrzynia biegów:", "").strip()
                                    if "Numer VIN:" in x.text:
                                        vin = x.text.replace("Numer VIN:", "").strip()
                                    if "Poj. silnika:" in x.text:
                                        engine_cap = x.text.replace("Poj. silnika:", "").strip()
                                    if "Paliwo:" in x.text:
                                        petrol = x.text.replace("Paliwo:", "").strip()
                        else:
                            raise self.AuctionDataError("Auction parameters not found.")

                    if args.verbose:
                        print(f"Found keyword: {keyword} for {auction_url} Title: {auction_name}. Price : {cash} \n")
                    self.append_dictionary(auction_url, keyword, auction_name, cash, prod_year, hp, mileage, gearbox, vin, engine_cap, petrol)

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
