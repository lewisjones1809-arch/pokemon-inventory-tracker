from dotenv import load_dotenv
import requests
import os
import sqlite3
import json

# load .env file
load_dotenv()

# create a connection to the database
con = sqlite3.connect('pokemon_tracker.db')

# set URL and API key
url = "https://api.pokemontcg.io/v2/cards"
api_key = os.getenv("POKEMON_API_KEY")

# call the API and get the response
response = requests.get(url, headers={"X-Api-Key": api_key}, params={"select": "id,name,set,number,cardmarket,rarity"})
response_json = response.json()
print(response_json['data'][0])

# insert the data into the allCards table
for item in response_json['data']:
    cardmarket = item.get('cardmarket')
    if cardmarket is not None:
        url = cardmarket.get('url')
    else:
        url = None
    con.execute("INSERT INTO allCards (id, cardName, setName, setNumber, url, rarity) VALUES (?,?, ?, ?, ?, ?)", (item['id'], item['name'], item['set']['name'], item['number'], url, item.get('rarity', 'Unknown')))

# commit the changes and close the connection
con.commit()
con.close()
