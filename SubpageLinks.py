import logging
import re
import langid
import requests
import selenium.common.exceptions
from bs4 import BeautifulSoup as bs
from Utils import remove_nearduplicates


def get_links(driver, website_url):
    """Apply a regxp that includes all HTML links (href) on the site that contain a URL
       Excluding files hosted on the site, like images, css, xml etc."""

    try:
        driver.get(website_url)
        response = requests.get(website_url)
        if response.status_code != 200:  # e.g. if we are in 404, page not found
            return []
    except Exception as e:
        return []  # e.g. we do not expect all sites to be in another language and have an English version

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
    """Intermediate function between get_relevant_subpages() and get_links():
       If the site is not in English, check whether there is an English version (extension or subpage) with .en or /en"""

    page_links = get_links(driver, website_url)
    try:
        soup = bs(driver.page_source, features="lxml")
    except selenium.common.exceptions.TimeoutException as e:
        logging.warning("Selenium timeout exception when trying to access driver.page_source on page "
                        + website_url)
        return []
    visible_text = soup.getText(separator=" ")  # exclude HTMl code for the purpose of language identification
    site_language = langid.classify(visible_text)[0]
    logging.info("site language: " + site_language)

    if site_language != 'en':
        extension_pt = re.compile('\.([\S]){2,5}$')
        alternate_urls = [re.sub(extension_pt, ".en", website_url), website_url + "en"]
        # logging.info("alternate_urls: " + str(alternate_urls))
        for url in alternate_urls:
            page_links = page_links + get_links(driver, url)

    return page_links


def get_relevant_subpages(subpages_urls_ls, website_url):
    """ Gets the URLs to:
    # - Contact pages; e.g. contact, impressum, kontakt
    # - Legal pages (both Terms and Conditions and Privacy Policy);  e.g. privacy-policy, datenschutz, confidentialité
    # - About us pages (this page can also be under Mission, Who we are and similar)  e.g. about-us, Über uns, quienes-somos"""

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