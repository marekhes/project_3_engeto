"""
projekt_3.py: třetí projekt do Engeto Online Python Akademie
author: Marek Hes
email: marekhes@proton.me
discord: Petr Svetr#4490
"""

import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
# naimportování veškerých knihoven, které budou potřeba k fungování scraperu

data = []
url = ""

def main():
  global url
  if len(sys.argv) != 3:  # kontrola argumentů
    print("Usage: python projekt_3.py <url> <output_file>")
    sys.exit(1)

  url = sys.argv[1]
  output_file = sys.argv[2]
  try:
    process_okres(url)
    save_to_csv(output_file)
    print(f"Data were successfully saved to {output_file}")
  except Exception as e:
    print(f"An error occurred: {e}")

print("Downloading html website content.")

def fetch_page(url):
  """Stáhne HTML obsah stránky a vrátí BeautifulSoup objekt."""
  response = requests.get(url)
  response.raise_for_status()
  return BeautifulSoup(response.text, 'html.parser')
  

def save_to_csv(output_file):
  """Extrahuje data z tabulky na stránce a vrátí je jako seznam slovníků."""
  df = pd.DataFrame(data)
  df.to_csv(output_file, index=False)

def process_okres(url):
  """Zpracuje data z url okresu (url, kterou dostaneme na vstupu v argumentech)."""
  soup = fetch_page(url)
  print("Processing downloaded data.")
  process_okres_table(soup)

def process_obec(url):
  """Zpracuje data z url obce."""
  soup = fetch_page(url)
  obec_table = get_obec_table(soup)
  return obec_table

def process_okres_table(soup):
  """Zpracuje data z okresové stránky (ta, kterou dostaneme na vstupu v argumentech)."""
  global data
  table = soup.find('table', {'class': 'table'})
  if not table:
    raise ValueError("Table with 'okres parts' results not found.")
  headers = ['kód obce', 'název obce', 'voliči v seznamu', 'vydané obálky', 'platné hlasy']
  for row in table.find_all('tr')[2:]:  # Přeskočí první dva řádky
    cells = row.find_all('td')
    if len(cells) > 1:
      obec_info = {}
      obec_info['kód obce'] = cells[0].get_text(strip=True)
      obec_info['název obce'] = cells[1].get_text(strip=True)
      obec_url = get_base_url(url) + cells[2].find('a')['href']
      obec_info_from_X_url = process_obec(obec_url)
      obec_info.update(obec_info_from_X_url)
      data.append(obec_info)

def process_okrsky_obce(table):
  """Některé obce jsou dále rozdělené na okrsky a místo tabulky s hlasováním mají tabulku s odkazama na okrsky. Po prokliknutí už máme data o hlasování."""
  obec_info = {}
  for okrsek_row in table.find_all('tr')[1].find_all('td'):  # Přeskočí řádek
    okrsek_url = get_base_url(url) + okrsek_row.find('a')['href']
    soup = fetch_page(okrsek_url)
    okrsek_table = get_okrsek_table(soup)

    if 'voliči v seznamu' not in obec_info:
      obec_info['voliči v seznamu'] = okrsek_table['voliči v seznamu']
    if 'vydané obálky' not in obec_info:
      obec_info['vydané obálky'] = okrsek_table['vydané obálky']
    if 'platné hlasy' not in obec_info:
      obec_info['platné hlasy'] = okrsek_table['platné hlasy']
    for key in okrsek_table:
      if key in ['kód obce', 'název obce', 'voliči v seznamu', 'vydané obálky', 'platné hlasy'] or key == '-':
        continue
      
      if okrsek_table[key] == '-':
          okrsek_table[key] = 0

      if key not in obec_info:
        obec_info[key] = okrsek_table[key]
      else:
        obec_info[key] = int(obec_info[key]) + int(okrsek_table[key])
  
  return obec_info

def get_okrsek_table(soup):
  """Některé obce jsou dále rozdělené na okrsky s trochu jinou sturkturou, než obce. Tato funkce zpracuje data z okrskové stránky."""
  okrsek_info = {}

  table = soup.find_all('table', {'class': 'table'})

  general_info_table = table[0]
  politicke_strany_table_left = table[1]
  politicke_strany_table_right = table[2]

  if not general_info_table or not politicke_strany_table_left or not politicke_strany_table_right:
    raise ValueError("Table 'obec' with results not found.")
  for row in general_info_table.find_all('tr')[1:]:  # Přeskočí řádek
    cells = row.find_all('td')

    if len(cells) > 1:
      okrsek_info['voliči v seznamu'] = cells[0].get_text(strip=True)
      okrsek_info['vydané obálky'] = cells[1].get_text(strip=True)
      okrsek_info['platné hlasy'] = cells[4].get_text(strip=True)

  for row in (politicke_strany_table_left.find_all('tr')[2:] + politicke_strany_table_right.find_all('tr')[2:]):  # Skip two header rows and add data from two tables together
    cells = row.find_all('td')
    if len(cells) > 1:
      okrsek_info[cells[1].get_text(strip=True)] = cells[2].get_text(strip=True)
  
  return okrsek_info

def get_obec_table(soup):
  """Zpracuje data ze stránky o obci"""  
  obec_info = {}

  table = soup.find_all('table', {'class': 'table'})
  if table[0].find_all('th')[0].get_text(strip=True) == 'Okrsek':
    return process_okrsky_obce(table[0])

  general_info_table = table[0]
  politicke_strany_table_left = table[1]
  politicke_strany_table_right = table[2]

  if not general_info_table or not politicke_strany_table_left or not politicke_strany_table_right:
    raise ValueError("Table 'obec' with results not found.") # kontrola, zda jsou nalezeny všechny požadované tabulky na stránce
  for row in general_info_table.find_all('tr')[2:]:  # přeskočí první dva řádky
    cells = row.find_all('td')
    if len(cells) > 1:
      obec_info['voliči v seznamu'] = cells[3].get_text(strip=True)
      obec_info['vydané obálky'] = cells[4].get_text(strip=True)
      obec_info['platné hlasy'] = cells[7].get_text(strip=True)

  for row in (politicke_strany_table_left.find_all('tr')[2:] + politicke_strany_table_right.find_all('tr')[2:]):  # přeskočí první dva řádky a sloučí data z dvou tabulek
    cells = row.find_all('td')
    if len(cells) > 1:
      if cells[1].get_text(strip=True) == '-':
        continue

      if cells[2].get_text(strip=True) == '-':
        hlasy = 0
      else:
        hlasy = cells[2].get_text(strip=True)
      obec_info[cells[1].get_text(strip=True)] = hlasy
  
  return obec_info

def get_base_url(url):
  """Odebere query z url, aby se k url dala připojit relativní url z 'X' linků na stránce"""
  u = url.split('ps32')[0]
  return u

if __name__ == '__main__':
  main()