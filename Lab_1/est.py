import socket
from bs4 import BeautifulSoup
from functools import reduce
from datetime import datetime, timezone


def scrape_product_details(product_link):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('999.md', 80))

        request = f"GET {product_link} HTTP/1.1\r\nHost: 999.md\r\nConnection: close\r\n\r\n"
        sock.send(request.encode())

        response = b""
        while True:
            part = sock.recv(4096)
            if not part:
                break
            response += part

        sock.close()

        response = response.decode('utf-8', errors='ignore')

        # Check for redirection
        if response.startswith("HTTP/1.1 301"):
            new_url = response.split("Location: ")[1].split("\r\n")[0]
            return scrape_product_details(new_url)  # Follow the redirect

        body = response.split("\r\n\r\n", 1)[1]
        product_soup = BeautifulSoup(body, 'html.parser')

        description_tag = product_soup.find('div', class_='adPage__content__description grid_18',
                                            itemprop='description')

        if description_tag:
            description = description_tag.get_text(strip=True)
        else:
            description = "Descriere indisponibilă"

        return description
    except Exception as e:
        return f"Error: {str(e)}"


def convert_to_eur(price_mdl):
    conversion_rate = 20
    return round(price_mdl / conversion_rate, 2)


def convert_to_mdl(price_eur):
    conversion_rate = 20
    return round(price_eur * conversion_rate, 2)


url = "/ro/list/computers-and-office-equipment/tablet"  # Use the path only for the socket request

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('999.md', 80))

request = f"GET {url} HTTP/1.1\r\nHost: 999.md\r\nConnection: close\r\n\r\n"
sock.send(request.encode())

response = b""
while True:
    part = sock.recv(4096)
    if not part:
        break
    response += part

sock.close()

response = response.decode('utf-8', errors='ignore')

# Check for redirection
if response.startswith("HTTP/1.1 301"):
    new_url = response.split("Location: ")[1].split("\r\n")[0]
    print(f"Redirected to: {new_url}")

# Now handle the redirection properly or just proceed if no redirection
body = response.split("\r\n\r\n", 1)[1]
soup = BeautifulSoup(body, 'html.parser')

products = soup.find_all('li', class_='ads-list-photo-item')
print(f"Found {len(products)} products.")

product_data = []
for index, product in enumerate(products):
    if index >= 10:
        break

    name_tag = product.find('div', class_='ads-list-photo-item-title')
    name = name_tag.find('a').get_text(strip=True) if name_tag else "Nume indisponibil"

    price_tag = product.find('div', class_='ads-list-photo-item-price')
    price_text = price_tag.get_text(strip=True) if price_tag else "0"
    print(f"Processing product: {name}, Price text: {price_text}")

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
            price_eur = float(price_text)
            price_mdl = convert_to_mdl(price_eur)
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

print(f"Product data collected: {len(product_data)} items.")
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
