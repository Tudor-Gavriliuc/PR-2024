# Select your website and make an HTTP GET request.[1] It should return a valid HTTP response
# with HTML content/body :)

import requests

url = "https://999.md/ro/list/computers-and-office-equipment/tablet"

response = requests.get(url)

if response.status_code == 200:
    print("Cererea a fost un succes!")
    print("Codul de răspuns:", response.status_code)
    print("Continut HTML (primele 500 de caractere):")
    print(response.text[:500])
else:
    print(f"Eroare la cererea HTTP: {response.status_code}")
