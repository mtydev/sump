from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import argparse
import pyfiglet

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url", help="provides site url")
parser.add_argument("-k", "--keywords", help="keywords that you want to see, needs to be a txt file")
parser.add_argument("-o", "--output", help="name a output txt file, where links from finished query will be provided")
args = parser.parse_args()


def print_logo():
    logo = pyfiglet.figlet_format('|--SUMP--|', font='speed')
    print(logo)


if args.url:
    # "https://www.olx.pl/motoryzacja/q-miska-olejowa-bmw-e87/"
    url = args.url
    f = open(args.keywords, 'r')
    keywords = f.read().split(',')
    output_file_name = args.output

    print_logo()

    driver = webdriver.Firefox()
    driver.get(url)
    driver.implicitly_wait(10)


    def refuse_cookies():
        driver.find_element(By.ID, 'onetrust-pc-btn-handler').click()
        driver.find_element(By.CLASS_NAME, 'ot-pc-refuse-all-handler').click()

    refuse_cookies()

    auction_list = driver.find_elements(By.CLASS_NAME, 'css-1sw7q4x')
    for item in auction_list:
        try:
            auction = item.find_element(By.TAG_NAME, 'h6')
            auction_title = auction.text
            last_auction_title = ''
            for keyword in keywords:
                if keyword in auction_title:
                    continue
                if last_auction_title != auction_title:
                    auction.click()
                    output_file = open(f'{output_file_name}', 'a')
                    output_file.write(f'{auction_title}\n')
                last_auction_title = auction_title

        except NoSuchElementException:
            pass
    driver.close()