import socket
import ssl
from bs4 import BeautifulSoup
from functools import reduce
from datetime import datetime, timezone

host = '999.md'
port = 443
base_url = f"https://{host}"

request = f"GET /ro/list/computers-and-office-equipment/tablet HTTP/1.1\r\nHost: {host}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0 Safari/537.36\r\nConnection: close\r\n\r\n"

context = ssl.create_default_context()

with socket.create_connection((host, port)) as sock:
    with context.wrap_socket(sock, server_hostname=host) as ssl_sock:
        ssl_sock.sendall(request.encode())

        response_data = b""
        while True:
            chunk = ssl_sock.recv(4096)
            if not chunk:
                break
            response_data += chunk

response_text = response_data.decode()

header_end_idx = response_text.find("\r\n\r\n")
if header_end_idx != -1:
    html_body = response_text[header_end_idx + 4:]

soup = BeautifulSoup(html_body, 'html.parser')

def scrape_product_details(product_link):
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssl_sock:
            request = f"GET {product_link} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0 Safari/537.36\r\nConnection: close\r\n\r\n"
            ssl_sock.sendall(request.encode())
            
            product_response_data = b""
            while True:
                chunk = ssl_sock.recv(4096)
                if not chunk:
                    break
                product_response_data += chunk

    product_response_text = product_response_data.decode()
    header_end_idx = product_response_text.find("\r\n\r\n")
    if header_end_idx != -1:
        product_html_body = product_response_text[header_end_idx + 4:]  # The actual HTML content
    else:
        return "Descriere indisponibilă"

    product_soup = BeautifulSoup(product_html_body, 'html.parser')
    description_tag = product_soup.find('div', class_='adPage__content__description grid_18', itemprop='description')

    if description_tag:
        description = description_tag.get_text(strip=True)
    else:
        description = "Descriere indisponibilă"

    return description

def convert_to_eur(price_mdl):
    conversion_rate = 20
    return round(price_mdl / conversion_rate, 2)

def convert_to_mdl(price_eur):
    conversion_rate = 20
    return round(price_eur * conversion_rate, 2)

products = soup.find_all('li', class_='ads-list-photo-item')

product_data = []
for index, product in enumerate(products):
    if index >= 20:
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

min_price = 10.00
max_price = 200.00

filtered_products = list(filter(lambda x: min_price <= x['price_eur'] <= max_price, product_data))

total_price_eur = reduce(lambda acc, x: acc + x['price_eur'], filtered_products, 0.0)

results = {
    'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
    'filtered_products': filtered_products,
    'total_price_eur': total_price_eur,
}

def serialize_to_json(data):
    json_string = '{'
    json_string += f'"timestamp": "{data["timestamp"]}",'
    json_string += '"filtered_products": ['
    
    for product in data['filtered_products']:
        json_string += '{'
        json_string += f'"name": "{product["name"]}",'
        json_string += f'"link": "{product["link"]}",'
        json_string += f'"price_mdl": {product["price_mdl"]},'
        json_string += f'"price_eur": {product["price_eur"]},'
        json_string += f'"description": "{product["description"].replace("\"", "\\\"")}"'  # Escape quotes
        json_string += '},'
    
    if data['filtered_products']:
        json_string = json_string[:-1]  # Remove last comma
    
    json_string += '],'
    json_string += f'"total_price_eur": {total_price_eur}'
    json_string += '}'
    
    return json_string

# XML Serialization
def serialize_to_xml(data):
    xml_string = '<results>'
    xml_string += f'<timestamp>{data["timestamp"]}</timestamp>'
    xml_string += '<filtered_products>'
    
    for product in data['filtered_products']:
        xml_string += '<product>'
        xml_string += f'<name>{product["name"]}</name>'
        xml_string += f'<link>{product["link"]}</link>'
        xml_string += f'<price_mdl>{product["price_mdl"]}</price_mdl>'
        xml_string += f'<price_eur>{product["price_eur"]}</price_eur>'
        xml_string += f'<description>{product["description"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</description>'  # Escape XML special characters
        xml_string += '</product>'
    
    xml_string += '</filtered_products>'
    xml_string += f'<total_price_eur>{total_price_eur}</total_price_eur>'
    xml_string += '</results>'
    
    return xml_string

# Serialize results
json_output = serialize_to_json(results)
xml_output = serialize_to_xml(results)

# Print/log outputs
print("JSON Output:")
print(json_output)
print("----------------------------")
print("\nXML Output:")
print(xml_output)
