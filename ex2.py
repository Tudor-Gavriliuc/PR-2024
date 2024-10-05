# Use an HTML parser to extract the name and price
# of the products

import requests
from bs4 import BeautifulSoup

url = "https://999.md/ro/list/computers-and-office-equipment/tablet"

response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    products = soup.find_all('li', class_='ads-list-photo-item')

    for product in products:
        name_tag = product.find('div', class_='ads-list-photo-item-title')
        name = name_tag.find('a').get_text(strip=True) if name_tag else "Nume indisponibil"

        link = name_tag.find('a')['href'] if name_tag and name_tag.find('a') else "#"
        link = f"https://999.md{link}" if link.startswith("/") else link

        price_tag = product.find('div', class_='ads-list-photo-item-price')
        price = price_tag.get_text(strip=True) if price_tag else "Preț indisponibil"

        print(f"Nume produs: {name}")
        print(f"Link: {link}")
        print(f"Preț: {price}")
        print("-" * 40)
else:
    print(f"Eroare la cererea HTTP: {response.status_code}")
