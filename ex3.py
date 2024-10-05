# Extract the product link. Scrape the link further
# and extract one additional piece of data from it


import requests
from bs4 import BeautifulSoup


def scrape_product_details(product_link):
    product_response = requests.get(product_link)

    if product_response.status_code == 200:
        product_soup = BeautifulSoup(product_response.text, 'html.parser')

        description_tag = product_soup.find('div', class_='adPage__content__description grid_18',
                                                        itemprop='description')

        if description_tag:
            description = description_tag.get_text(strip=True)
        else:
            description = "Descriere indisponibilă"

        return description
    else:
        return "Eroare la cererea pentru produs"


url = "https://999.md/ro/list/computers-and-office-equipment/tablet"

response = requests.get(url)
count = 0
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    products = soup.find_all('li', class_='ads-list-photo-item')

    if not products:
        print("Nicio listă de produse găsită! Verificați structura paginii.")

    for product in products:
        if count >= 10:
            break

        name_tag = product.find('div', class_='ads-list-photo-item-title')
        name = name_tag.find('a').get_text(strip=True) if name_tag else "Nume indisponibil"

        link = name_tag.find('a')['href'] if name_tag and name_tag.find('a') else None
        if link:
            link = f"https://999.md{link}" if link.startswith("/") else link
        else:
            print(f"Numele produsului: {name} nu are un link valid.")
            continue

        print(f"Nume produs: {name}")
        print(f"Link: {link}")

        description = scrape_product_details(link)
        print(f"Descriere: {description}")
        print("-" * 40)
        count += 1
else:
    print(f"Eroare la cererea HTTP: {response.status_code}")
