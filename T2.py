
import re
import pandas as pd
import logging
import Utils
from bs4 import BeautifulSoup as bs
import csv
from dateutil import parser
import spacy
import statistics

def get_date_pt():
    """ Get the regex pattern to locate a date in the text"""
    month_letters = "(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)([a-z])*"
    dd_mm_numbers = "(\d{1,2})"
    day_ordinal = "(\d{1,2})(st|nd|rd|th)"
    year = "(\d{2,4})"

    date_pt = re.compile("(" + dd_mm_numbers+"[/\-]" + dd_mm_numbers + "[/\-]"+ year +
                         ")|(" + year + " [/\-]" + dd_mm_numbers + "[/\-]" + dd_mm_numbers +
                         ")|(" + month_letters + "(((\s)the)?\s)?" + "("+day_ordinal+"|"+dd_mm_numbers+")" + "[(\s),]+" + year +
                         ")|(" + day_ordinal + "( of )*" + month_letters + "\s" + year + ")")

    return date_pt


def get_money_pt():
    """The regex for amounts of money, with currency. One for URLs, one for text"""
    all_currency_symbols = "(" + Utils.CURRENCY_SYMBOLS + ")"
    numbers = "(" + "([0-9.])+" + ")|(" + "(one|two|three|four|five|six|seven|eight|nine|ten)(\s)?" + ")"
    numbers_and_currency = "(" + numbers + all_currency_symbols + "|" + all_currency_symbols + numbers + ")"
    text_money_pt = re.compile(numbers_and_currency + '( digit )?' +
                               '(\s(million(s?)|Million(s)?|thousand(s)?|,000))')

    return text_money_pt


def retrieve_money(nlp, soup):
    # The amount of the round as float (preferably denominated in original currency - in the case above SEK);
    # - check if the headers or the title contain information that the regex can pick up
    # - Use SpaCy on the text: get a majority vote on 'money' entities (n: keep only tokens with numbers in the list).
    # - If no majority is available, use the regex on the text
    visible_text = soup.getText(separator=" ")
    money_pt = get_money_pt()

    header_tags = soup.find_all(["h", "title"])
    header_strings = [tag.string for tag in header_tags]

    all_mentions_of_money = list(set([mtc.group(0).lower() for mtc in re.finditer(money_pt, " ".join(header_strings))]))
    if len(all_mentions_of_money) > 0:
        funding = all_mentions_of_money[0]
        # if not(any(cs in funding for cs in Utils.CURRENCY_SYMBOLS.split("|"))):  # no currency symbol found in the title
        #     currency_in_text = list(set([mtc.group(0).lower() for
        #                                  mtc in re.finditer("("+Utils.CURRENCY_SYMBOLS+")", visible_text)]))
        #     currency = currency_in_text[0]
        #     funding = funding + " " + currency
    else:  # nothing found in the headers. Use SpaCy on the page

        for doc in nlp.pipe([visible_text]):
            for token in doc:
                if token.ent_type_ == "MONEY":
                    all_mentions_of_money.append(token)

        counts = [all_mentions_of_money.count(i) for i in all_mentions_of_money]
        different_counts = set(counts)

        if len(different_counts) > 1:  # i.e. one of the entries is found more times than the other
            funding = statistics.mode(all_mentions_of_money)

        else:  # if SpaCy does not give us a definite answer, we use the regex
            all_mentions_of_money = list(set([mtc.group(0).lower() for mtc in re.finditer(money_pt, visible_text)]))
            if len(all_mentions_of_money) > 0:
                funding = all_mentions_of_money[0]  # get the first. The next ones may be total funding, investor etc.
            else:
                funding = []

    return funding, all_mentions_of_money  # the second is returned for debugging purposes


def retrieve_datetime(nlp, soup):
    # using either the time element from BSoup or the spacy token. However, exclude dates found in header elements

    time_elem = soup.find("time")
    all_dates = []
    unwanted = soup.find('span')
    unwanted.extract()
    if time_elem is not None:
        time_txt = time_elem.string
        try:
            date_str = str(parser.parse(time_txt, fuzzy=True))
            return date_str, all_dates
        except:
            pass

    visible_text = soup.getText(separator=" ")
    time_txt = visible_text
    date_pt = get_date_pt()
    all_dates = list(set([mtc.group(0) for mtc in re.finditer(date_pt, time_txt)]))
    for doc in nlp.pipe([visible_text]):
        for token in doc:
            if token.ent_type_ == "DATE":
                all_dates.append(token)
    if len(all_dates) > 1:
        date_str = all_dates[0]  # pick the first
    else:  # we did not find it in the text. Maybe the URL has it
        date_str = "not found"

    return date_str, all_dates


def exe():
    Utils.init_logging("FundingRounds.log")
    rounds_df = pd.read_excel("InputData.xlsx", sheet_name=1)
    # rounds_df = rounds_df[0:3]

    f = open('FundingRounds.csv', 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(["client_id","news_url","funding", "date"])  # add the date next

    nlp = spacy.load("en_core_web_sm")
    # From the Spacy examples: Merge noun phrases and entities for easier analysis
    nlp.add_pipe("merge_entities")
    nlp.add_pipe("merge_noun_chunks")

    for i, row in rounds_df.iterrows():
        news_url = row["news_url"]
        try:
            driver = Utils.get_webdriver()
            driver.get(news_url)
        except Exception as e:
            logging.warning(e)
            continue

        soup = bs(driver.page_source, features="lxml")

        funding, all_mentions_of_money = retrieve_money(nlp, soup)
        date_str, all_dates = retrieve_datetime(nlp, soup)

        if i % max((len(rounds_df) // 5), 1) == 0:
            logging.info(str(i+1) + "/" + str(len(rounds_df))+ "...")
        writer.writerow([row["client_id"], row["news_url"], funding, all_mentions_of_money, date_str, all_dates])

        driver.close()

    f.close()



