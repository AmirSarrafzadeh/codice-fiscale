import json
import requests
import pycountry
from bs4 import BeautifulSoup

# URL from which the HTML is fetched
# url = "https://www.hl7.it/fhir/base/CodeSystem-istat-unitaAmministrativeTerritorialiEstere.html"
url = "https://www.hl7.it/fhir/base/CodeSystem-istat-unitaAmministrativeTerritoriali.html"

# Sending HTTP GET request to the URL
response = requests.get(url)

# Creating a BeautifulSoup object with the HTML content and specifying the HTML parser
soup = BeautifulSoup(response.text, 'html.parser')

# Extracting and printing all h2 headers' text content from the HTML
h2_headers = soup.find_all('h2')

# Additionally, if you want to extract table contents or specific data
tables = soup.find_all('table')
ISTAT = {}
for table in tables:
    rows = table.find_all('tr')
    for row in rows:
        columns = row.find_all('td')
        column_texts = [col.text.strip() for col in columns]
        if len(column_texts) == 11:
            if column_texts[6].startswith("Z"):
                country = pycountry.countries.get(alpha_3=column_texts[9])
                if country:
                    ISTAT[country.name.lower()] = column_texts[6]
                else:
                    ISTAT[column_texts[2].lower()] = column_texts[6]


with open("ISTAT_it.json", "w") as f:
    json.dump(ISTAT, f)


