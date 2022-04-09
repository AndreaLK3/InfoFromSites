import pandas as pd
import requests
import Utils
import logging
import re
import os
import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def get_webdriver():
    # We need a Selenium webdriver to get 100% of the text from dynamic webpages that rely on javascript

    edge_options = webdriver.EdgeOptions()
    edge_options.use_chromium = True
    edge_options.add_argument('headless')
    edge_options.add_argument('disable-gpu')
    driver = webdriver.Edge(executable_path='msedgedriver.exe', options=edge_options)

    return driver


def retrieve_emails():
    companies = pd.read_excel("InputData.xlsx", sheet_name=0)
    rounds = pd.read_excel("InputData.xlsx", sheet_name=1)

    driver = get_webdriver()

    companies = companies[0:4]
    Utils.init_logging("Companies.log")

    # output file. Since it takes > 5 minutes, we save the partial results
    f = open('Emails.csv', 'w')
    writer = csv.writer(f)
    writer.writerow("website,emails_set")

    # close the file
    f.close()

    for i, row in companies.iterrows():
        website_url = row["website"]

        driver.get(website_url)
        page_txt = driver.page_source
        # Steps:
        # gather the subpages of the site at 1 level of depth
        # run a regex search on the site and its subpages for {alphanum}+@{alphanum}+.{alphabet}+
        links_pt = re.compile('href=(\S)+\.([^\s"])+')
        matches = [xp.group(0) for xp in re.finditer(links_pt, page_txt)]
        all_links = [s.replace('href="', "") for s in matches]
        subpage_links = list(set([l for l in all_links if l.startswith(website_url)]))
        logging.info("\nPage: " + website_url)

        site_emails = set()
        for subpage_url in subpage_links:
            logging.info("Subpage:" + subpage_url)
            driver.get(subpage_url)
            page_txt = driver.page_source
            # *** Debug ***
            ampersand_pt = re.compile("(.)+@(.+)")
            amps = list(set([xp.group(0) for xp in re.finditer(ampersand_pt, page_txt)]))
            # logging.info("@ found in: " + str(amps))
            # ***
            emails_pt = re.compile("([A-Za-z0-9])+@([A-Za-z0-_9])+(\.[A-Z|a-z]{2,})+")
            addresses = list(set([xp.group(0) for xp in re.finditer(emails_pt, page_txt)]))
            if len(addresses) > 0:
                logging.info("Addresses: " + str(addresses))

            not_email_fragments = ["sentry", "wixpress"]
            email_addresses_ls = []
            for address in addresses:
                if any([fragment in address for fragment in not_email_fragments]):
                    continue
                else:
                    email_addresses_ls.append(address)
            if len(email_addresses_ls) > 0:
                logging.info("Subpage: " + subpage_url + " ; E-mails: " + str(email_addresses_ls))

            site_emails = site_emails.union(set(email_addresses_ls))

        logging.info("Site: " + website_url + " ; e-mails: " + str(site_emails))
        writer.writerow(website_url + ","+ str(site_emails))

    driver.close()

    return companies, rounds