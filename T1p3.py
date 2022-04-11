import T1
import Utils
import pandas as pd
import logging
from bs4 import BeautifulSoup as bs
import requests
from sklearn.feature_extraction.text import TfidfVectorizer


def get_headers():
    # Get a short description of the company activities in English (e.g. The largest AI-powered database of green
    # startups in Europe)

    companies = pd.read_excel("InputData.xlsx", sheet_name=0)
    companies = companies[0:20]
    driver = T1.get_webdriver()

    # companies = companies[0:3]
    Utils.init_logging("Description.log")

    for i, row in companies.iterrows():
        website_url = row["website"]
        logging.info("\nPage: " + website_url)
        try:
            driver.get(website_url)
        except Exception as e:
            logging.warning(e)
            continue

        soup = bs(driver.page_source, features="lxml")
        header_tags = soup.findAll(["h1", "h2", "h3", "h4", "h5", "h6"])
        header_strings = [tag.string for tag in header_tags]

        alt_urls = T1.get_alternative_english_versions(driver, website_url)
        for alt_url in alt_urls:
            try:
                response = requests.get(alt_url)
                if response.status_code!= 200:
                    continue  # probably a 404, page not found
                driver.get(alt_url)
                soup = bs(driver.page_source, features="lxml")
                header_tags_2 = soup.findAll(["h1", "h2", "h3", "h4", "h5", "h6"])
                header_strings_2 = [tag.string for tag in header_tags_2]
                header_strings = header_strings_2
            except Exception as e:
                continue  # we do not expect all sites to be in another language and have an English version

        logging.info(header_strings)

    driver.close()


def tf_idf():
    Utils.init_logging("TF-IDF.log")

    companies = pd.read_excel("InputData.xlsx", sheet_name=0)
    companies = companies[0:8]
    driver = T1.get_webdriver()

    documents_dict = dict()
    for i, row in companies.iterrows():
        website_url = row["website"]
        logging.info("\nPage: " + website_url)
        try:
            driver.get(website_url)
        except Exception as e:
            logging.warning(e)
            continue

        subpage_links = T1.get_page_links(driver, website_url)
        logging.info("List of subpages: " + str(subpage_links))

        contact_pages, legal_pages, about_us_pages = T1.get_relevant_subpages(subpage_links, website_url)

        soup = bs(driver.page_source, features="lxml")
        website_text = soup.getText(separator=" ")
        about_us_text = ""
        for subpage in about_us_pages:
            driver.get(subpage)
            soup = bs(driver.page_source, features="lxml")
            subpage_text = soup.getText(separator=" ")
            about_us_text = about_us_text + subpage_text
        documents_dict[website_url] = website_text + " " + about_us_text

    websites = sorted(companies["website"].tolist())
    return websites


