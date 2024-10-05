# Before storing the product information in your
# data models/structures, add two validations to the
# data.


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

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    products = soup.find_all('li', class_='ads-list-photo-item')

    if not products:
        print("Nicio listă de produse găsită! Verificați structura paginii.")

    for index, product in enumerate(products):
        if index >= 10:
            break

        name_tag = product.find('div', class_='ads-list-photo-item-title')
        name = name_tag.find('a').get_text(strip=True) if name_tag else "Nume indisponibil"

        price_tag = product.find('div', class_='ads-list-photo-item-price')
        price_text = price_tag.get_text(strip=True).replace('lei', '').replace(' ', '') if price_tag else "0"
        price = price_text

        if not isinstance(name, str) or not name:
            print(f"Numele produsului '{name}' este invalid.")
            continue

        try:
            price = float(price)
        except ValueError:
            print(f"Prețul '{price}' nu este valid.")
            continue

        print(f"Nume produs: {name}")
        print(f"Preț: {price} lei")

        link = name_tag.find('a')['href'] if name_tag and name_tag.find('a') else None
        if link:
            link = f"https://999.md{link}" if link.startswith("/") else link
        else:
            print(f"Numele produsului: {name} nu are un link valid.")
            continue

        print(f"Link: {link}")

        description = scrape_product_details(link)
        print(f"Descriere: {description}")
        print("-" * 40)
else:
    print(f"Eroare la cererea HTTP: {response.status_code}")
