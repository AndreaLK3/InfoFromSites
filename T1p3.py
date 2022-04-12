import T1
import Utils
import pandas as pd
import logging
from bs4 import BeautifulSoup as bs
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
import langid

def filter_for_english_subpages(driver, urls):
    # If we have pages in multiple languages and only a few of them are in EN, drop those that are not
    # If there is only one language or EN is not present, the list is unchanged
    urls_en = []
    languages = []
    for url in urls:
        driver.get(url)
        soup = bs(driver.page_source, features="lxml")
        visible_text = soup.getText(separator=" ")  # exclude HTMl code for the purpose of language identification
        site_language = langid.classify(visible_text)[0]
        languages.append(site_language)
    if len(set(languages))>1 and ('en' in set(languages)):
        for i in range(len(urls)):
            if languages[i]== 'en':
                urls_en.append(urls[i])
    else:
        urls_en = urls
    return urls_en


def get_weighted_sentence(sentence, site, websites, tfidf_obj, tfidf_mat):

    weights = []
    for word in sentence:
        doc_idx = websites.index(site)
        w_idx = tfidf_obj.vocabulary_[word]
        weights.append(tfidf_mat[doc_idx][w_idx])

    return sum(weights) / len(weights)


def get_headers():
    # Get a short description of the company activities in English (e.g. The largest AI-powered database of green
    # startups in Europe)

    companies = pd.read_excel("InputData.xlsx", sheet_name=0)
    companies = companies[5:8]
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

        logging.info(header_strings)

    driver.close()

    return header_strings


def tf_idf():
    Utils.init_logging("TF-IDF.log")

    companies = pd.read_excel("InputData.xlsx", sheet_name=0)
    companies = companies[5:8]
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
        # if we have pages in English and in another language, keep only the former


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
        print(documents_dict.keys())

    websites = sorted(companies["website"].tolist())

    docs = [documents_dict[k] for k in websites]
    tfidf_obj = TfidfVectorizer()
    tfidf_mat = tfidf_obj.fit_transform(docs, y=None)

    return websites, tfidf_obj, tfidf_mat