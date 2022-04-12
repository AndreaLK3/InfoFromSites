# InputData.xlsx, worksheet Fround contains a list of 50 articles dealing with the founding round. In the
# worksheet, the candidate will find the name of the organization, the website, the link to news covering
# the funding round of the company and the company unique identifier (client_id).
# The candidate shall create a Python script to to extract the below information for each of the news_url
# listed:
# 1. The amount of the round as float (preferably denominated in original currency - in the case
# above SEK);
# 2. The date of the round as Timestamp - the article publication date;
# 3. The investors taking part in the round.
# Please note that point 3 is OPTIONAL.
#
import re
import pandas as pd
import logging
import Utils
from bs4 import BeautifulSoup as bs
import csv


def exe():
    Utils.init_logging("FundingRounds.log")
    rounds_df = pd.read_excel("InputData.xlsx", sheet_name=1)
    rounds_df = rounds_df[0:20]

    f = open('FundingRounds.csv', 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(["client_id","news_url","funding_round"])  # add the date next

    driver = Utils.get_webdriver()

    all_currency_symbols = "(CHF|DKK|SEK|NOK|kr|EUR|€|GBP|£|PLN|zł|TRY|UAH|ILS|CAD|CLP|USD|\$|AUD|CNY|¥|HK$|INR|₹|SGD|JPY|" \
                           "BTC|XBT|₿|ETH|Ξ)"

    for i, row in rounds_df.iterrows():
        news_url = row["news_url"]
        try:
            driver.get(news_url)
        except Exception as e:
            logging.warning(e)
            continue

        soup = bs(driver.page_source, features="lxml")
        visible_text = soup.getText(separator=" ")
        money_pt = re.compile('(([0-9.,])+(\s)?'+all_currency_symbols +
                              "|"+all_currency_symbols+'(\s)?([0-9.,])+)'
                               '([mM]|(\s)(million(s)?|Million(s)?|thousand(s)?))')

        all_mentions_of_money = list(set([mtc.group(0).lower() for mtc in re.finditer(money_pt, visible_text)]))
        if len(all_mentions_of_money) > 1:
            all_mentions_of_money = all_mentions_of_money[0:1]
        logging.info((row["news_url"], str(all_mentions_of_money)))
        writer.writerow([row["client_id"], row["news_url"], str(all_mentions_of_money)])




