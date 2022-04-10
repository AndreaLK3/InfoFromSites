import pandas as pd
import requests
import Utils
import logging
import re
import os
import time
import csv
from selenium import webdriver
from bs4 import BeautifulSoup as bs
import string

def get_webdriver():
    # We need a Selenium webdriver to get 100% of the text from dynamic webpages that rely on javascript

    edge_options = webdriver.EdgeOptions()
    edge_options.use_chromium = True
    edge_options.add_argument('headless')
    edge_options.add_argument('disable-gpu')
    driver = webdriver.Edge(executable_path='msedgedriver.exe', options=edge_options)

    return driver


def retrieve_emails_and_numbers():
    companies = pd.read_excel("InputData.xlsx", sheet_name=0)
    # rounds = pd.read_excel("InputData.xlsx", sheet_name=1)

    driver = get_webdriver()

    companies = companies[0:20]
    Utils.init_logging("Companies.log")

    # output file. Since it takes > 5 minutes, we save the partial results
    f = open('Info.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(["website","emails", "phone_numbers"])

    for i, row in companies.iterrows():
        website_url = row["website"]
        try:
            driver.get(website_url)
        except Exception as e:
            logging.warning(website_url)
            logging.warning(e)
            continue
        page_txt = driver.page_source
        # Steps:
        # gather the subpages of the site at 1 level of depth
        # run a regex search on the site and its subpages for {alphanum}+@{alphanum}+.{alphabet}+, and phone numbers
        links_pt = re.compile('href='
                              '((\S)+\.([^\s"])+'  # absolute URL
                              '|"/([^\s"])+)'  # or: relative URL
                              '(?!\.(.)+)')  # not ending in .xml, .css, or similar
        matches = [xp.group(0) for xp in re.finditer(links_pt, page_txt)]
        all_links = [s.replace('href="', "") for s in matches]
        subpage_links = list(set([l for l in all_links if (l.startswith(website_url) or l.startswith("/"))]))
        # subpage_links = list(filter(lambda l: not(l.endswith("xml")), potential_subpage_links))
        logging.info("\nPage: " + website_url)
        # logging.info("List of subpages: " + str(subpage_links))

        site_emails = set()
        site_phones = set()
        session = requests.Session()

        for subpage_url in subpage_links:
            if subpage_url.startswith(("/")):  # relative URL
                subpage_url = website_url + subpage_url[1:]
            logging.info("Subpage:" + subpage_url)
            try:
                # for speed, and because we do not need to follow any dynamic links, use requests to get the static text
                response = session.get(subpage_url)
            except Exception as e:
                logging.warning(e)
                continue
            page_txt = response.text
            # *** Debug ***
            # ampersand_pt = re.compile("(.)+@(.+)")
            # amps = list(set([xp.group(0) for xp in re.finditer(ampersand_pt, page_txt)]))
            # logging.info("@ found in: " + str(amps))
            # ***
            emails_pt = re.compile("(?<=mailto:)?([A-Za-z0-9])+@([A-Za-z0-_9])+(\.[A-Z|a-z]{2,})+")
            addresses = list(set([xp.group(0) for xp in re.finditer(emails_pt, page_txt)]))
            #if len(addresses) > 0:
            #    logging.info("Addresses: " + str(addresses))

            not_email_fragments = ["sentry", "wixpress"]
            # email_addresses_ls = []
            email_addresses_ls = list(filter(lambda addr:
                                             not(any([fragment in addr for fragment in not_email_fragments])), addresses))
            # for address in addresses:
            #     if any([fragment in address for fragment in not_email_fragments]):
            #         continue
            #     else:
            #         email_addresses_ls.append(address)

            if len(email_addresses_ls) > 0:
                logging.info("Subpage: " + subpage_url + " ; E-mails: " + str(email_addresses_ls))

            site_emails = site_emails.union(set(email_addresses_ls))

            # The phone numbers are taken from the visible text of the HTML pages, thus we need BeautifulSoup
            soup = bs(response.text, features="lxml")
            visible_text = soup.getText(separator=" _ ")
            numbers_pt = re.compile("(:|\s)+"  # starts with whitespace or directly after :
                                    "(\+)?"    # the first char may be a +
                                    "(([0-9]){2,10}(\s)+)+")  # 1 or more sequences of numbers
            numbers = [xp.group(0) for xp in re.finditer(numbers_pt, visible_text)]
            numbers_digits = ["".join(list(filter(lambda c: c in string.digits+"+", num_str))) for num_str in numbers]
            phone_numbers = list(filter(lambda num: 7 <= len(num) <= 14, numbers_digits))  # number length
            phone_numbers = list(filter(lambda num: not(any([num.count(c) > len(num) / 2 for c in num])),
                                        phone_numbers)) # not too many identical digits
            if len(phone_numbers) > 0:
                logging.info("Subpage: " + subpage_url + " ; Phone numbers: " + str(phone_numbers))
            site_phones = site_phones.union(set(phone_numbers))


            time.sleep(1)  # to avoid rate limits on HTTP requests to a website

        logging.info("Site: " + website_url + " ; e-mails: " + str(site_emails) + " ; phone numbers: " + str(site_phones))

        writer.writerow([website_url,str(site_emails), str(site_phones)])

    driver.close()
    f.close()

    # Examining the current e-mail results: which sites do not have e-mails, or have questionable e-mails?