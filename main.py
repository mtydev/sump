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
parser.add_argument("-k", "--keywords", help="keywords that you want to see, needs to be a txt file")
parser.add_argument("-o", "--output", help="name a output txt file, where links from finished query will be provided")
args = parser.parse_args()


def print_logo():
    logo = pyfiglet.figlet_format('| SUMP |', font='speed')
    print(logo)


if args.url:
    # "https://www.olx.pl/motoryzacja/q-miska-olejowa-bmw-e87/"
    url = args.url
    f = open(args.keywords, 'r')
    keywords = f.read().split(',')
    f.close()
    output_file_name = args.output

    print_logo()

    def refuse_cookies(drv):
        drv.find_element(By.ID, 'onetrust-pc-btn-handler').click()
        drv.find_element(By.CLASS_NAME, 'ot-pc-refuse-all-handler').click()

    driver = webdriver.Firefox()
    driver.get(url)
    driver.implicitly_wait(10)
    refuse_cookies(driver)


    def search_for_keywords(auction_search_url, search_keywords):
        driver.switch_to.new_window('tab')
        driver.get(auction_search_url)
        content = driver.find_elements(By.TAG_NAME, 'h1, h2, h3, h4, h5, h6, p')
        for word in content:
            if word.text in search_keywords:
                return True
            else:
                return False
        driver.close()
        driver.switch_to.window(original_window)


    original_window = driver.current_window_handle
    assert len(driver.window_handles) == 1
    auction_list = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="listing-grid"]')
    for item in auction_list:
        try:
            auctions = item.find_elements(By.TAG_NAME, 'a')
            for auction in auctions:
                auction_title = auction.find_element(By.TAG_NAME, 'h6').text
                auction_url = auction.get_attribute('href')
                if search_for_keywords(auction_url, keywords):
                    output_file = open(f'{output_file_name}', 'a')
                    output_file.write(f'{auction_title} : {auction_url}\n')
        except NoSuchElementException:
            pass
    driver.quit()

# TEST RUN
#   python ./main.py -u "https://www.olx.pl/motoryzacja/q-miska-olejowa-bmw-e87/" -k input.txt -o output.txt
#
