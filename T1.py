import pandas as pd
import requests
import logging
import re
import time
import csv
from bs4 import BeautifulSoup as bs
import string
import langid
from Utils import remove_nearduplicates, get_webdriver, init_logging
import time


def get_links(driver, website_url):
    # apply a regxp that includes all HTML links (href) on the site that contain a URL
    # excluding files hosted on the site, like images, css, xml etc.
    try:
        driver.get(website_url)
    except Exception as e:
        return []  # e.g. we do not expect all sites to be in another language and have an English version
    response = requests.get(website_url)
    if response.status_code != 200:  # e.g. if we are in 404, page not found
        return []

    page_txt = driver.page_source
    links_pt = re.compile('href='
                          '((\S)+\.([^\s"])+'  # absolute URL
                          '|"/([^\s."])+)')  # or: relative URL
    matches = [xp.group(0) for xp in re.finditer(links_pt, page_txt)]
    all_links = [s.replace('href="', "") for s in matches]
    subpage_links = list(set([l for l in all_links if (l.startswith(website_url) or l.startswith("/"))]))
    extensions_to_exclude = ["xml", "css", "js", "png", "jpg", "jpeg", "json", "ico", "fonts"]
    subpage_links = list(filter(lambda l: not (any([ext in l for ext in extensions_to_exclude])), subpage_links))

    return subpage_links


def get_page_links(driver, website_url):
    page_links = get_links(driver, website_url)
    # If the site is not in English, check whether there is an English version (extension or subpage)
    soup = bs(driver.page_source, features="lxml")
    visible_text = soup.getText(separator=" ")  # exclude HTMl code for the purpose of language identification
    site_language = langid.classify(visible_text)[0]
    logging.info("site language: " + site_language)

    if site_language != 'en':
        extension_pt = re.compile('\.([\S]){2,5}$')
        alternate_urls = [re.sub(extension_pt, ".en", website_url), website_url + "en"]
        logging.info("alternate_urls: " + str(alternate_urls))
        for url in alternate_urls:
            page_links = page_links + get_links(driver, url)

    return page_links



def get_emails(page_txt):
    emails_pt = re.compile("(?<=mailto:)?([A-Za-z0-9])+@([A-Za-z0-_9])+(\.[A-Z|a-z]{2,5})+")
    addresses = list(set([xp.group(0) for xp in re.finditer(emails_pt, page_txt)]))
    not_email_fragments = ["sentry", "wixpress", "png", "gif", "jpeg", "example",
                           "jpg"]  # to exclude loader@2x.gif, etc.
    email_addresses_ls = list(filter(lambda addr:
                                     not (any([fragment in addr for fragment in not_email_fragments])), addresses))
    return email_addresses_ls


def get_phone_numbers(driver):
    # The phone numbers are taken from the visible text of the HTML pages, thus we need BeautifulSoup
    page_txt = driver.page_source
    soup = bs(page_txt, features="lxml")
    visible_text = soup.getText(separator=" _ ")
    numbers_pt = re.compile("(?<=el|ne)?"  # tel/phone
                            "(:|\s)+(\+)?"  # starts with whitespace or directly after :, and maybe a +
                            "(([0-9]){2,10}(\s)+)+")  # 1 or more sequences of numbers
    numbers = [xp.group(0) for xp in re.finditer(numbers_pt, visible_text)]
    numbers_digits = ["".join(list(filter(lambda c: c in string.digits + "+", num_str))) for num_str in numbers]
    phone_numbers_ls = list(filter(lambda num: 7 <= len(num) <= 14, numbers_digits))  # number length

    return phone_numbers_ls


def get_relevant_subpages(subpages_urls_ls, website_url):
    # Gets the URLs to:
    # ○ Contact pages; e.g. contact, impressum, kontakt
    # ○ Legal pages (both Terms and Conditions and Privacy Policy);  e.g. privacy-policy, datenschutz, confidentialité
    # ○ About us pages (this page can also be under Mission, Who we are and similar)  e.g. about-us, Über uns, quienes-somos

    subpages_urls = []
    for url in subpages_urls_ls:
        if url.startswith("/"):
            subpages_urls.append(website_url+url)
        else:
            subpages_urls.append(url)

    contact_identifiers = ["contact", "impressum", "kontakt", "contatti", "contacto", "contato"]
    contact_pages = [url for url in subpages_urls if any([cid in url for cid in contact_identifiers])]

    legal_identifiers = ["privacy", "legal", "terms", "datenschutz", "confidentialit", "privacidad", "datenschutz"]
    legal_pages = [url for url in subpages_urls if any([lid in url for lid in legal_identifiers])]

    about_us_identifiers = ["about", "who-we-are", "qui-nous-sommes", "Über-uns", "somos",
                            "mission", "om-os", "sobre-nos", "nous"]
    about_us_pages = [url for url in subpages_urls if any([aid in url for aid in about_us_identifiers])]

    contact_pages = remove_nearduplicates(contact_pages)
    legal_pages = remove_nearduplicates(legal_pages)
    about_us_pages = remove_nearduplicates(about_us_pages)

    return contact_pages, legal_pages, about_us_pages



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
        logging.info("\nPage: " + website_url)
        try:
            driver.get(website_url)
        except Exception as e:
            logging.warning(e)
            continue

        subpage_links = remove_nearduplicates(get_page_links(driver, website_url))
        logging.info("List of subpages: " + str(subpage_links))

        contact_pages, legal_pages, about_us_pages = get_relevant_subpages(subpage_links, website_url)

        site_emails = set()
        site_phones = set()

        if len(subpage_links) < 50:
            pages_to_consult = subpage_links
        else:
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

            phone_numbers = get_phone_numbers(driver)
            site_phones = site_phones.union(set(phone_numbers))
            # post-processing:
            # are phone numbers already present, starting with +? if so, eliminate the others, they're likely not phones
            if any(["+" in num for num in site_phones]):
                site_phones = set(filter(lambda num: "+" in num, site_phones))

            time.sleep(1)  # to avoid rate limits on HTTP requests to a website

        logging.info("Site: " + website_url + " ; e-mails: " + str(site_emails) + " ; phone numbers: " + str(site_phones)
                     + " ; contact_pages: " + str(contact_pages) + " ; legal_pages: " + str(legal_pages) +
                     " ; about_us_pages: " + str(about_us_pages))

        writer.writerow([website_url,str(site_emails), str(site_phones),
                         str(contact_pages), str(legal_pages), str(about_us_pages)])

    driver.close()
    f.close()
    t1 = time.time()
    logging.info("Time elapsed=" + str(round(t1 - t0, 2)))