import logging
import re
import sys

# Invoked to write a message to a text logfile and also print it
import Levenshtein
from selenium import webdriver

# constants
CURRENCY_SYMBOLS = 'CHF|DKK|SEK|NOK|kr|EUR|€|GBP|£|PLN|zł|TRY|UAH|ILS|CAD|CLP|USD|\$|AUD|CNY|¥|HK$|INR|₹|SGD|JPY| \
                    "BTC|XBT|₿|ETH|Ξ'

def init_logging(logfilename, loglevel=logging.INFO):
  for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
  logging.basicConfig(level=loglevel, filename=logfilename, filemode="w",
                      format='%(levelname)s : %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

  if len(logging.getLogger().handlers) < 2:
      outlog_h = logging.StreamHandler(sys.stdout)
      outlog_h.setLevel(loglevel)
      logging.getLogger().addHandler(outlog_h)


def remove_nearduplicates(str_ls):
    # Auxiliary function
    str_ls_1 = []
    anchor_pt = re.compile("/#(\S)+$")
    for s in str_ls:
        if s in str_ls_1:
            continue
        if any([Levenshtein.distance(s, s1) <= 2 for s1 in str_ls_1]):
            continue
        if re.sub(anchor_pt, "", s) in str_ls_1:
            continue
        str_ls_1.append(s)
    return str_ls_1


def get_webdriver():
    # We need a Selenium webdriver to get 100% of the text from dynamic webpages that rely on javascript

    edge_options = webdriver.EdgeOptions()
    edge_options.use_chromium = True
    edge_options.add_argument('headless')
    edge_options.add_argument('disable-gpu')
    driver = webdriver.Edge(executable_path='msedgedriver.exe', options=edge_options)

    return driver


def store_pages_t1():
    # Preliminary step: access the websites and the relevant subpages only once, storing them in .csv files