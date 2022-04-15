## Data Scientist Task

### TASK #1

Data retrieval executed with `T1.retrieve_info()`

Give a company's website, our first step is to collect the URLs
of the site's subpages at 1 level of depth, which include contact pages, legal pages etc.. <br/>
We use a regex to extract the addresses in `<href>`
elements of the main page. We have to manually exclude .css and .js and
similar extensions, since they still constitute valid URLs accessible from the
main page but are not subpages of the site. The core of this step is found in 
the function<br/>
`get_links(driver, website_url)`, in the module SubpageLinks.py.

#### Relevant subpages

Since we have the subpage links already, we address point 3 in <br/>
`SubpageLinks.get_relevant_subpages(subpages_urls_ls, website_url)`<br/>
We define a number of identifiers in several languages (e.g.  "impressum", "kontakt", "contatti", "contacto")
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

Having said that, as a workaround and partial solution in `T1.get_candidate_description(page_txt_source)`