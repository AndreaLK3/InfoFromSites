import pandas as pd
import requests
import Utils
import logging
from bs4 import BeautifulSoup
import re

def exe():
    companies = pd.read_excel("InputData.xlsx", sheet_name=0)
    rounds = pd.read_excel("InputData.xlsx", sheet_name=1)

    companies = companies[0:2]
    Utils.init_logging("Companies.log")

    for i, row in companies.iterrows():
        website_url = row["website"]
        page_response = requests.get(website_url)
        # Steps:
        # gather the subpages of the site at 1 level of depth
        # run a regex search on the site and its subpages for {alphanum}+@{alphanum}+.{alphabet}+
        links_pt = r'href=[":A-Za-z0-9.\/-]+[.](\w)+'
        all_links = re.search(links_pt, page_response.text)
        logging.info(all_links)
        logging.info(page_response.json())
        # logging.info(page_response.text)

    return companies, rounds