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

# temp: add:
# URL to:
# ○ Contact pages; e.g. contact, impressum, kontakt
# ○ Legal pages (both Terms and Conditions and Privacy Policy);  e.g. privacy, privacy-policy, terms-conditions,
# legal-information, datenschutz, politique-de-confidentialite
# ○ About us pages (this page can also be under Mission, Who we are and similar)  e.g. about-us, Über uns, https://kriim.com/en/pages/quienes-somos
# n: Subpage:https://plumetec.it/en: you need to use it as a new root page, if you want to avoid translations
# or an alternate site, https://taxymatch.com/en

def get_webdriver():
    # We need a Selenium webdriver to get 100% of the text from dynamic webpages that rely on javascript

    edge_options = webdriver.EdgeOptions()
    edge_options.use_chromium = True
    edge_options.add_argument('headless')
    edge_options.add_argument('disable-gpu')
    driver = webdriver.Edge(executable_path='msedgedriver.exe', options=edge_options)

    return driver


def get_subpage_links(website_url, page_txt):
    links_pt = re.compile('href='
                          '((\S)+\.([^\s"])+'  # absolute URL
                          '|"/([^\s."])+)')  # or: relative URL
    matches = [xp.group(0) for xp in re.finditer(links_pt, page_txt)]
    all_links = [s.replace('href="', "") for s in matches]
    subpage_links = list(set([l for l in all_links if (l.startswith(website_url) or l.startswith("/"))]))
    extensions_to_exclude = ["xml", "css", "js", "png", "jpg", "jpeg", "json"]
    subpage_links = list(filter(lambda l: not(any([(ext in l for ext in extensions_to_exclude])), subpage_links))
    return subpage_links

def get_emails(page_txt):
    emails_pt = re.compile("(?<=mailto:)?([A-Za-z0-9])+@([A-Za-z0-_9])+(\.[A-Z|a-z]{2,5})+")
    addresses = list(set([xp.group(0) for xp in re.finditer(emails_pt, page_txt)]))
    not_email_fragments = ["sentry", "wixpress", "png", "gif", "jpeg", "example",
                           "jpg"]  # to exclude loader@2x.gif, etc.
    email_addresses_ls = list(filter(lambda addr:
                                     not (any([fragment in addr for fragment in not_email_fragments])), addresses))

    return email_addresses_ls


def get_phone_numbers(page_txt):
    # The phone numbers are taken from the visible text of the HTML pages, thus we need BeautifulSoup
    soup = bs(page_txt, features="lxml")
    visible_text = soup.getText(separator=" _ ")
    numbers_pt = re.compile("(?<=el|ne)?"  # tel/phone
                            "(:|\s)+(\+)?"  # starts with whitespace or directly after :, and maybe a +
                            "(([0-9]){2,10}(\s)+)+")  # 1 or more sequences of numbers
    numbers = [xp.group(0) for xp in re.finditer(numbers_pt, visible_text)]
    numbers_digits = ["".join(list(filter(lambda c: c in string.digits + "+", num_str))) for num_str in numbers]
    phone_numbers_ls = list(filter(lambda num: 7 <= len(num) <= 14, numbers_digits))  # number length
    # are phone numbers already present, starting with +? if so, eliminate the others, they're likely not phones
    if any(["+" in num for num in phone_numbers_ls]):
        phone_numbers_ls = list(filter(lambda num: "+" in num, phone_numbers_ls))
    return phone_numbers_ls


def retrieve_info():
    companies = pd.read_excel("InputData.xlsx", sheet_name=0)
    # rounds = pd.read_excel("InputData.xlsx", sheet_name=1)

    driver = get_webdriver()

    # companies = companies[50:51]
    Utils.init_logging("Info.log")

    # output file. Since it takes > 20 minutes, we save the partial results
    f = open('Info.csv', 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(["website","emails", "phone_numbers", "Contact_pages", "Legal_pages", "AboutUs_pages"])

    for i, row in companies.iterrows():
        website_url = row["website"]
        logging.info("\nPage: " + website_url)
        try:
            driver.get(website_url)
        except Exception as e:
            logging.warning(e)
            continue
        page_txt = driver.page_source
        # Steps:
        # gather the subpages of the site at 1 level of depth
        # run a regex search on the site and its subpages for {alphanum}+@{alphanum}+.{alphabet}+, and phone numbers
        subpage_links = get_subpage_links(website_url, page_txt)
        # logging.info("List of subpages: " + str(subpage_links))

        site_emails = set()
        site_phones = set()

        for subpage_url in subpage_links:
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
            if len(email_addresses_ls) > 0:
                logging.info("Subpage: " + subpage_url + " ; E-mails: " + str(email_addresses_ls))
            site_emails = site_emails.union(set(email_addresses_ls))

            phone_numbers = get_phone_numbers(page_txt)
            if len(phone_numbers) > 0:
                logging.info("Subpage: " + subpage_url + " ; Phone numbers: " + str(phone_numbers))
            site_phones = site_phones.union(set(phone_numbers))

            time.sleep(1)  # to avoid rate limits on HTTP requests to a website

        logging.info("Site: " + website_url + " ; e-mails: " + str(site_emails) + " ; phone numbers: " + str(site_phones))

        writer.writerow([website_url,str(site_emails), str(site_phones)])

    driver.close()
    f.close()

    # Examining the current e-mail and phone results: which sites have missing / questionable elements?
    # grofit.eu: no phone, confirmed.
    # app.wasteout.ru : nothing. it's in Russian and most of the site is not accessible
    # agrionica.com : nothing. Empty page, with a title "insufficient money on the account" in Ciryllic
    # 5: cyberquant.org: why 3757791 among the phone numbers? because of 3,757,791
    # 6: plumetec.it: why 2105159? Because of "Numero REA: 2105159"
    # 7: ilovesnacks.co.uk: why 197624269, 09178679? Because of "Company registration number, VAT number"
    # 8: tukea.de : no phone. confirmed
    # 9: birch.earth: no phone. And why did I not get info@birch.earth? because it has 5 letters in its custom domain
    # circolution.com: why 346035722? Because of "Bel ons: 0341 842121"
    # innova.co.uk: why '01242388633', '+442045308369', '01242371990', '02037874320', they are actually phone numbers
