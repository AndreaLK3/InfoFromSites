## Data Scientist Task

Python script: `script.py`

### TASK #1

Data retrieval executed with `T1.retrieve_info()` <br>
Output found in the file `Info.csv`. Execution time: ~40 minutes

Given a company's website, our first step is to collect the URLs
of the site's subpages at 1 level of depth, which include contact pages, legal pages etc.. <br/>
We use a regex to extract the addresses in `<href>`
elements of the main page. We have to manually exclude .css and .js and
similar extensions, since they still constitute valid URLs accessible from the
main page but are not subpages of the site. The core of this step is found in 
the function `get_links(driver, website_url)`, in the module SubpageLinks.py.

#### Relevant subpages

Since we have the subpage links already, we define a number of identifiers in several languages (e.g.  "impressum", "kontakt", "contatti", "contacto")
and then simply check if they are present in the URLs.

#### E-mails

The next step is to go through all the subpages and use a regex to find 
the e-mails they contain, as specified in `T1.get_emails(page_txt)`

#### Phone numbers

We retrieve phone numbers the same way as e-mails, applying the appropriate regex to a site's subpages.
In this case we also check that they have between 7 and 14 digits and whether the site indicates
phone numbers with a '+' (in which case any digit strings without a '+' are ignored).

#### Description

This is without a doubt the most difficult point of Task 1. Rather than a description, I believe it would be 
more opportune to extract keywords, either as a classification task, turning the
readable text on the site into a vector and applying a neural network, or by selecting a 
number of relevant words and weighing them by TF-IDF.

As a workaround and partial solution in `T1.get_candidate_description(page_txt_source)`,
we use BeautifulSoup to find the page headers (<h*>) and return the first that is not None 
and has more than 2 words.
If we had more time, a quick refinement would involve eliminating all non-English words
and using TF-IDF to try to determine which header is most relevant (e.g. "our business is ..." rather than "Privacy and Legal terms")


### TASK #2

Data retrieval executed with `T2.exe()` <br>
Output found in the file `FundingRounds.csv`. Execution time: ~10 minutes

#### Funding amount

We have 3 ways of retrieving funding information, so if one does not return anything we use the next:
- Check if the headers or the title of the webpage already contain information that a money regex can pick up
- Get a webpage's visible text via BeautifulSoup and use SpaCy's tool for English to find all the "MONEY" entities. We suppose that the funding amount is either mentioned first or mentioned more times, so we get a majority vote
- If no majority is available, use the money regex on the page's text

#### Date

Similarly, we make 3 attempts to retrieve datetime information:
- Use BeautifulSoup to find the \<time\> elements in the page
- Use the regex for dates on the page's visible text
- Use SpaCy to get the "DATE" entities 

n: The regex is vulnerable to other dates being present in the page, like today's date. 
The headers could be excluded from the text being examined, to trade completeness for correctness.



