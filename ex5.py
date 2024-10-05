# Process the list of products using Map/Filter/Reduce functions.[3] Map the price to EUR. If it’s already in EUR, convert it to MDL. Filter the products within a range of prices. Use reduce to sum
# up the prices of the filtered products. Attach that
# sum to the new data model/structure along with
# the filtered products. Attach a UTC timestamp as
# well.

import requests
from bs4 import BeautifulSoup
from functools import reduce
from datetime import datetime, timezone


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


def convert_to_eur(price_mdl):
    conversion_rate = 20
    return round(price_mdl / conversion_rate, 2)


def convert_to_mdl(price_eur):
    conversion_rate = 20
    return round(price_eur * conversion_rate, 2)


url = "https://999.md/ro/list/computers-and-office-equipment/tablet"

response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    products = soup.find_all('li', class_='ads-list-photo-item')

    product_data = []
    for index, product in enumerate(products):
        if index >= 5:
            break

        name_tag = product.find('div', class_='ads-list-photo-item-title')
        name = name_tag.find('a').get_text(strip=True) if name_tag else "Nume indisponibil"

        price_tag = product.find('div', class_='ads-list-photo-item-price')
        price_text = price_tag.get_text(strip=True) if price_tag else "0"

        price_mdl = 0
        price_eur = 0

        if 'lei' in price_text:
            price_text = price_text.replace('lei', '').replace(' ', '')
            try:
                price_mdl = float(price_text)
                price_eur = convert_to_eur(price_mdl)
            except ValueError:
                print(f"Prețul '{price_text}' nu este valid.")
                continue
        elif '€' in price_text:
            price_text = price_text.replace('€', '').replace(' ', '')
            try:
                price_eur = float(price_text)  # Convert to EUR
                price_mdl = convert_to_mdl(price_eur)  # Convert to MDL
            except ValueError:
                print(f"Prețul '{price_text}' nu este valid.")
                continue

        link = name_tag.find('a')['href'] if name_tag and name_tag.find('a') else None
        if link:
            link = f"https://999.md{link}" if link.startswith("/") else link
        else:
            print(f"Numele produsului: {name} nu are un link valid.")
            continue

        product_data.append({
            'name': name,
            'link': link,
            'price_mdl': price_mdl,
            'price_eur': price_eur,
            'description': scrape_product_details(link),
        })

    # Filter products within a price range
    min_price = 10.00
    max_price = 200.00

    filtered_products = list(filter(lambda x: min_price <= x['price_eur'] <= max_price, product_data))

    total_price_eur = reduce(lambda acc, x: acc + x['price_eur'], filtered_products, 0.0)

    results = {
        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
        'filtered_products': filtered_products,
        'total_price_eur': total_price_eur,
    }

    print(results)

else:
    print(f"Eroare la cererea HTTP: {response.status_code}")
