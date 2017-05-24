import requests
from bs4 import BeautifulSoup

from db.models import Company
from crawler.models import WebPage


## Get list of companies listed on WSE
page = WebPage("http://infostrefa.com/infostrefa/pl/spolki?market=mainMarket")
soup = BeautifulSoup(page.content, "html.parser")

# Locate table with companies (can change in the future) and extract data
table_body = soup.select("div#companiesList table")[0]
rows = table_body.find_all("tr")

headers = list(map(lambda x: x.text.strip(), rows[0].find_all("td")))
companies = []
for row in rows[1:]:
    values = [ele.text.strip() for ele in row.find_all("td")]
    companies.append(dict(zip(headers, values)))

## Load more infro from gpw.pl

response = requests.post(
	"https://www.gpw.pl/ajaxindex.php",
	params = {
		"action": "GPWListaSp",
		"start": "infoTab",
		"gls_isin": "PLSNZKA00033",
		"lang": "PL"
	}
)
soup = BeautifulSoup(response.content.decode("utf-8"), "lxml")
rows = soup.find_all("tr")

data = list()
for row in rows:
    values = tuple(ele.text.strip() for ele in row.find_all(["th", "td"]))
    data.append(values)

companies[150].update(data)