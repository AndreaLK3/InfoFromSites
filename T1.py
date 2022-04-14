import pandas as pd
import logging
import re
import csv
from bs4 import BeautifulSoup as bs
import string

import Utils
from Load import get_page_links, get_relevant_subpages
from Utils import remove_nearduplicates, get_webdriver, init_logging
import time


def get_emails(page_txt):
    emails_pt = re.compile("(?<=mailto:)?([A-Za-z0-9])+@([A-Za-z0-_9])+(\.[A-Z|a-z]{2,5})+")
    addresses = list(set([xp.group(0) for xp in re.finditer(emails_pt, page_txt)]))
    not_email_fragments = ["sentry", "wixpress", "png", "gif", "jpeg", "example",
                           "jpg"]  # to exclude loader@2x.gif, etc.
    email_addresses_ls = list(filter(lambda addr:
                                     not (any([fragment in addr for fragment in not_email_fragments])), addresses))
    return email_addresses_ls


def get_phone_numbers(page_source_txt):
    # The phone numbers are taken from the visible text of the HTML pages, thus we need BeautifulSoup
    soup = bs(page_source_txt, features="lxml")
    visible_text = soup.getText(separator=" _ ")
    numbers_pt = re.compile("(?<=el|ne)?"  # tel/phone
                            "(:|\s)+(\+)?"  # starts with whitespace or directly after :, and maybe a +
                            "(([0-9]){2,10}(\s)+)+")  # 1 or more sequences of numbers
    numbers = [xp.group(0) for xp in re.finditer(numbers_pt, visible_text)]
    numbers_digits = ["".join(list(filter(lambda c: c in string.digits + "+", num_str))) for num_str in numbers]
    phone_numbers_ls = list(filter(lambda num: 7 <= len(num) <= 14, numbers_digits))  # number length

    return phone_numbers_ls


def retrieve_info():
    # Steps:
    # gather the subpages of the site at 1 level of depth
    # if there is a version of the site in English, add the subpages from it
    # determine the Contact, Legal, and About Us pages
    # run a regex search on the site and its significant (see above) subpages for e-mails and phone numbers
    t0 = time.time()
    companies = pd.read_excel("InputData.xlsx", sheet_name=0)
    driver = get_webdriver()

    # companies = companies[0:10]
    init_logging("Info.log")

    # output file. Since it takes > 20 minutes, we save the partial results
    f = open('Info.csv', 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(["website","emails", "phone_numbers", "Contact_pages", "Legal_pages", "AboutUs_pages"])

    for i, row in companies.iterrows():
        website_url = row["website"]
        logging.info("Page: " + website_url)
        try:
            driver.get(website_url)
        except Exception as e:
            logging.warning(e)
            continue

        subpage_links = remove_nearduplicates(get_page_links(driver, website_url))
        contact_pages, legal_pages, about_us_pages = get_relevant_subpages(subpage_links, website_url)

        site_emails = set()
        site_phones = set()
        pages_to_consult = contact_pages + legal_pages + about_us_pages

        for subpage_url in pages_to_consult:
            if subpage_url.startswith(("/")):  # relative URL
                subpage_url = website_url + subpage_url[1:]
            logging.info("Subpage:" + subpage_url)
            try:
                driver.get(subpage_url)
            except Exception as e:
                logging.warning(e)
                continue
            page_txt = driver.page_source

            email_addresses_ls = get_emails(page_txt)
            site_emails = site_emails.union(set(email_addresses_ls))

            phone_numbers = get_phone_numbers(page_txt)
            site_phones = site_phones.union(set(phone_numbers))
            # post-processing:
            # are phone numbers already present, starting with +? if so, eliminate the others, they're likely not phones
            if any(["+" in num for num in site_phones]):
                site_phones = set(filter(lambda num: "+" in num, site_phones))

            time.sleep(1)  # to avoid rate limits on HTTP requests to a website

        # logging.info("Site: " + website_url + " ; e-mails: " + str(site_emails) + " ; phone numbers: " + str(site_phones)
                     # + " ; contact_pages: " + str(contact_pages) + " ; legal_pages: " + str(legal_pages) +
                     # " ; about_us_pages: " + str(about_us_pages))

        writer.writerow([website_url,str(site_emails), str(site_phones),
                         str(contact_pages), str(legal_pages), str(about_us_pages)])

    driver.close()
    f.close()
    t1 = time.time()
    logging.info("Time elapsed=" + str(round(t1 - t0, 2)))