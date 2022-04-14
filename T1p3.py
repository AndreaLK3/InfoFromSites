import numpy as np

import T1
import Utils
import pandas as pd
import logging
from bs4 import BeautifulSoup as bs
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
import langid


def dummy_fun(doc):
    # Dummy function for the TF-IDF vectorizer. Given how we use it (getting TF-IDF weights for words in a header)
    # we tokenize the documents manually
    return doc

def setup_tf_idf(companies):
    Utils.init_logging("TF-IDF.log")
    driver = Utils.get_webdriver()
    documents_ls = []

    for i, row in companies.iterrows():
        website_url = row["website"]
        logging.info("Page: " + website_url)
        try:
            driver.get(website_url)
        except Exception as e:
            logging.warning(e)
            continue

        # subpage_links = T1.get_page_links(driver, website_url)
        # # if we have pages in English and in another language, keep only the former
        # logging.info("List of subpages: " + str(subpage_links))
        # contact_pages, legal_pages, about_us_pages = T1.get_relevant_subpages(subpage_links, website_url)

        soup = bs(driver.page_source, features="lxml")
        website_text = soup.getText(separator=" ")
        website_text_tokenized = website_text.split()
        documents_ls.append(website_text_tokenized)

    tfidf_obj = TfidfVectorizer(tokenizer=dummy_fun, preprocessor=dummy_fun, token_pattern=None)
    tfidf_mat = tfidf_obj.fit_transform(documents_ls, y=None).todense()

    return tfidf_obj, tfidf_mat


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


def get_sentence_weight(sentence, site_idx, tfidf_obj, tfidf_mat):

    weights = []
    for word in sentence.split():
        doc_idx = site_idx
        try:
            w_idx = tfidf_obj.vocabulary_[word.lower()]
            weights.append(tfidf_mat[doc_idx][w_idx])
        except KeyError:
            logging.warning("Not found in doc tf-idf matrix: '" + word + "'")
        except IndexError:
            logging.info((doc_idx, w_idx))
            logging.info(tfidf_mat.shape)

    return sum(weights) / len(weights)


def get_headers(companies_df, driver):
    # Get a short description of the company activities in English (e.g. The largest AI-powered database of green
    # startups in Europe)

    websites = (companies_df["website"].tolist())
    all_pages_headers = []

    for website_url in websites:
        try:
            driver.get(website_url)
        except Exception as e:
            logging.warning(e)
            continue

        soup = bs(driver.page_source, features="lxml")
        header_tags = soup.findAll(["h1", "h2", "h3", "h4", "h5", "h6"])
        header_strings = [tag.string for tag in header_tags]

        # logging.info(header_strings)
        all_pages_headers.append(header_strings)

    driver.close()

    return all_pages_headers


def exe():
    Utils.init_logging("Description.log")
    companies_df = pd.read_excel("InputData.xlsx", sheet_name=0)
    companies_df = companies_df[0:8]
    # sorted_websites = sorted(companies_df["website"].tolist())
    driver = Utils.get_webdriver()

    tfidf_obj, tfidf_mat = setup_tf_idf(companies_df)
    all_pages_headers = get_headers(companies_df, driver)

    candidate_desc_ls = []
    for i, row in companies_df.iterrows():
        page_headers_ls = all_pages_headers[i]
        if page_headers_ls is not None:
            page_headers_ls = [h for h in page_headers_ls if h is not None]
            page_headers_ls = list(filter(lambda h: len(h.split())>2, page_headers_ls))  # eliminate headers with <2 words
            page_headers_ls.sort(key=lambda h: get_sentence_weight(h, i, tfidf_obj, tfidf_mat), reverse=True)
        else: # empty site
            page_headers_ls = []
        candidate_desc_ls.append(page_headers_ls)
    logging.info("***candidate_desc_ls : \n" + str(candidate_desc_ls))

    return all_pages_headers

