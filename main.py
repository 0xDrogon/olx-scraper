import requests
import time
import os
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from twilio.rest import Client


def send_sms(msg):
    CLIENT.messages.create(body=msg, from_=SRC_NUMBER, to=DST_NUMBER)
    print(f"Message sent to {DST_NUMBER}")


def filter(ads):
    filtered = [ad for ad in ads if "6" in ad['description']]
    return filtered


def search_parser(response):
    soup = BeautifulSoup(response.content, 'html.parser')
    div = soup.find('div', {'class': 'css-oukcj3'})
    cards = div.find_all('div', {'data-cy': 'l-card'})
    entries = []
    for card in cards:
        ad = card.find('div', {'class': 'css-u2ayx9'})
        url = card.find('a', {'class': 'css-rc5s2u'}).get('href')
        name = ad.find('h6').text
        entry = {'name': name, 'url': WEBSITE+url}
        entries.append(entry)
    return entries


def ad_parser(response):
    soup = BeautifulSoup(response.content, 'html.parser')
    description = soup.find('div', {'class': 'css-bgzo2k er34gjf0'})
    return description.text.strip()


def request(session):
    s_resp = session.get(URL)
    ads = search_parser(s_resp)
    for ad in ads:
        a_resp = session.get(ad['url'])
        description = ad_parser(a_resp)
        ad['description'] = description
    """filtered_ads = filter(ads)
    for f_ad in filtered_ads:
        print(f"{f_ad['name']}, {f_ad['url']}\n{f_ad['description']}")
        print("---------------------\n")"""
    return ads


def scraper():
    prev_entries = []
    if os.path.exists('./output/output.json') and os.path.getsize('./output/output.json') > 0:
        with open('./output/output.json', 'r') as f:
            prev_entries = [json.loads(line.strip()) for line in f]

    while True:
        entries = request(requests.session())
        new_entries = [entry for entry in entries if entry not in prev_entries]
        removed_entries = [entry for entry in prev_entries if entry not in entries]
        
        if len(new_entries) > 0:
            print(f"There are {len(new_entries)} new entries")
            with open('./output/output.json', 'a') as f:
                for entry in new_entries:
                    f.write(json.dumps(entry) + '\n')
                    #send_sms(f"New ticket sale!\n\n{entry['name']}\n{entry['url']}")
        else:
            print("There are no new entries")

        if len(removed_entries) > 0:
            print(f"There are {len(removed_entries)} removed entries")
            with open('./output/output.json', 'w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
        else:
            print("There are no removed entries")

        prev_entries = entries
        time.sleep(5*60)  # sleeps for 5 minutes


if __name__ == '__main__':

    WEBSITE = "https://www.olx.pt"
    ENDPOINT = "/lazer/bilhetes-espectaculos/q-nos-alive/"
    URL = WEBSITE + ENDPOINT

    load_dotenv()
    ACCOUNT_SID = os.getenv('ACCOUNT_SID')
    AUTH_TOKEN = os.getenv('AUTH_TOKEN')
    SRC_NUMBER = os.getenv('SRC_NUMBER')
    DST_NUMBER = os.getenv('DST_NUMBER')
    CLIENT = Client(ACCOUNT_SID, AUTH_TOKEN)

    print("Running...\n")
    print("-----------------------------------------------------\n")
    scraper()