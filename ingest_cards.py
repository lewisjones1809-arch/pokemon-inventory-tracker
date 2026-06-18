from dotenv import load_dotenv
import requests
import os
import sqlite3
from datetime import datetime

# load .env file
load_dotenv()

# create a connection to the database and create cursor
con = sqlite3.connect('pokemon_tracker.db')
cur = con.cursor()

# set URL and API key
url = "https://api.pokemontcg.io/v2/cards"
api_key = os.getenv("POKEMON_API_KEY")

# call the API and get the response
response = requests.get(url, headers={"X-Api-Key": api_key}, params={"select": "id,name,set,number,cardmarket,rarity"})
response_json = response.json()
'''
print the first 10 items in the response for debugging purposes
print(response_json['data'][0:10])
'''

# insert the data into the allCards table
for item in response_json['data']:

    # check if cardmarket data exists for the card
    cardmarket = item.get('cardmarket')

    #if data exists, extract the relevant fields, otherwise set them to None
    if cardmarket is not None:
        url = cardmarket.get('url')
        has_reverse_holo = (cardmarket.get('prices').get('reverseHoloAvg30') != 0)
        trend_price = cardmarket.get('prices').get('trendPrice')
        avg30 = cardmarket.get('prices').get('avg30')
        reverse_holo_avg30 = cardmarket.get('prices').get('reverseHoloAvg30')
        reverse_holo_trend = cardmarket.get('prices').get('reverseHoloTrend')
        updated_at = cardmarket.get('updatedAt')
    else:
        url = None
        has_reverse_holo = False
        trend_price = None
        avg30 = None
        reverse_holo_avg30 = None
        reverse_holo_trend = None
        updated_at = None

    # insert card into allCards
    cur.execute("INSERT INTO allCards (id, cardName, setName, setNumber, url, rarity) VALUES (?,?, ?, ?, ?, ?)", (item['id'], item['name'], item['set']['name'], item['number'], url, item.get('rarity', 'Unknown')))

    # add normal variant and price history
    cur.execute("INSERT INTO cardVariants (cardID, finish) VALUES (?, ?)", (item['id'], 'Normal'))
    cur.execute("INSERT INTO priceHistory (variantID, averageSellPrice, trendPrice, updatedAt,capturedAt) VALUES(?, ?, ?, ?, datetime('now'))", (cur.lastrowid, avg30, trend_price, updated_at))

    # if reverse holo exists, add reverse holo variant and price history
    if has_reverse_holo:
        cur.execute("INSERT INTO cardVariants (cardID, finish) VALUES (?, ?)", (item['id'], 'Reverse Holo'))
        cur.execute("INSERT INTO priceHistory (variantID, averageSellPrice, trendPrice, updatedAt,capturedAt) VALUES(?, ?, ?, ?, datetime('now'))", (cur.lastrowid, reverse_holo_avg30, reverse_holo_trend, updated_at))


# commit the changes and close the connection
con.commit()
con.close()
