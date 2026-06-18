from dotenv import load_dotenv
import requests
import os
import sqlite3
from card_functions import update_prices, create_new_card

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

# insert the data
for item in response_json['data']:

    create_new_card(cur, item)
    update_prices(cur, item)

# commit the changes and close the connection
con.commit()
con.close()
