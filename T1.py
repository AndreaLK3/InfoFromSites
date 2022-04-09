import pandas as pd
import requests
import Utils
import logging
import re
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def get_webdriver():
    # We need a Selenium webdriver to get 100% of the text from dynamic webpages that rely on javascript

    opts = Options()
    # opts.add_argument(" — headless") # Uncomment if the headless version needed
    opts.binary_location = "<path to Chrome executable>"

    # # Set the location of the webdriver
    # chrome_driver = os.getcwd() + "<Chrome webdriver filename>"
    #
    # # Instantiate a webdriver
    # driver = webdriver.Chrome(options=opts, executable_path=chrome_driver)

    # Load the HTML page
    # driver.get(os.getcwd() + "/test.html")
    #
    # # Parse processed webpage with BeautifulSoup
    # soup = BeautifulSoup(driver.page_source)
    # print(soup.find(id="test").get_text())


def exe():
    companies = pd.read_excel("InputData.xlsx", sheet_name=0)
    rounds = pd.read_excel("InputData.xlsx", sheet_name=1)

    companies = companies[0:2]
    Utils.init_logging("Companies.log")

    for i, row in companies.iterrows():
        website_url = row["website"]

        edge_options = webdriver.EdgeOptions()
        edge_options.use_chromium = True
        edge_options.add_argument('headless')
        edge_options.add_argument('disable-gpu')
        driver = webdriver.Edge(executable_path='msedgedriver.exe', options=edge_options)
        driver.get(website_url)
        page_txt = driver.page_source
        # Steps:
        # gather the subpages of the site at 1 level of depth
        # run a regex search on the site and its subpages for {alphanum}+@{alphanum}+.{alphabet}+
        links_pt = re.compile('href=(\S)+\.([\w])+/([a-zA-z0-9-_])+')
        matches = [xp.group(0) for xp in re.finditer(links_pt, page_txt)]
        all_links = [s.replace('href="', "") for s in matches]
        subpage_links = list(set([l for l in all_links if l.startswith(website_url)]))
        logging.info(website_url + ": " + str([link for link in subpage_links]))

        for subpage_url in subpage_links:
            driver.get(subpage_url)
            page_txt = driver.page_source
            emails_pt =re.compile("([A-Za-z0-_9])+@([A-Za-z0-_9])+(\.[A-Z|a-z]{2,})+")
            email_addresses = list(set([xp.group(0) for xp in re.finditer(emails_pt, page_txt)]))
            if len(email_addresses) > 0:
                logging.info(subpage_url + ": " + str([address for address in email_addresses]))





    return companies, rounds