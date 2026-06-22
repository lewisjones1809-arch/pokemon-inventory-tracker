import sqlite3
import requests
from dotenv import load_dotenv
import os
import pandas as pd
import streamlit as st

@st.cache_resource
def get_connection():
    return sqlite3.connect('pokemon_tracker.db', check_same_thread=False)

def safe_get(d, *keys, default=None):
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key)
    return d if d is not None else default

# call the api and return the response as a json object
def call_api(params: dict, id: str ="") -> dict:
    # load .env file
    load_dotenv()

    # set URL and API key
    url = f"https://api.pokemontcg.io/v2/cards/{id}"
    api_key = os.getenv("POKEMON_API_KEY")

    # call the API and get the response
    response = requests.get(url, headers={"X-Api-Key": api_key}, params=params)
    return response

def get_sets_from_api(params, id):
    # load .env file
    load_dotenv()

    # set URL and API key
    url = f"https://api.pokemontcg.io/v2/sets/{id}"
    api_key = os.getenv("POKEMON_API_KEY")

    # call the API and get the response
    response = requests.get(url, headers={"X-Api-Key": api_key}, params=params)
    return response

def get_set_id_from_name(set_name):
    load_dotenv()

    url = f"https://api.pokemontcg.io/v2/sets"
    api_key = os.getenv("POKEMON_API_KEY")
    params = {'q': f'name:"{set_name}"','select': 'id,name'}

    response = requests.get(url, headers={"X-Api_key": api_key}, params=params)
    response_json = response.json()
    set_id = response_json['data'][0].get('id')
    return set_id

# add new card to allCards table
def create_new_cards(cur: sqlite3.Cursor, cards: dict[dict]) -> None:
    # ensure input is a list
    if isinstance(cards, dict):
        cards = [cards]

    # initialise counters for new cards and variants
    new_cards_counter = 0
    new_variants_counter = 0

    # loop through all cards
    for card in cards:

        # check if cardmarket data exists for the card
        cardmarket = safe_get(card, 'cardmarket')
        tcgplayer = safe_get(card, 'tcgplayer')

        # reverse-holo existence is only reliable from tcgplayer - cardmarket
        # populates reverseHolo* price fields for every card regardless of
        # whether a reverse holo actually exists, so it can't be trusted here.
        has_reverse_holo = safe_get(tcgplayer, 'prices', 'reverseHolofoil') is not None

        # prefer cardmarket for the url, falling back to tcgplayer
        if cardmarket is not None:
            url = safe_get(cardmarket, 'url')
        elif tcgplayer is not None:
            url = safe_get(tcgplayer, 'url')
        else:
            url = None

        # if card not in table already, insert into allCards table
        if cur.execute("SELECT id FROM allCards WHERE id = ?", (card['id'],)).fetchone() is None:
            cur.execute("INSERT INTO allCards (id, cardName, setName, setNumber, url, rarity, imageURL) VALUES (?,?, ?, ?, ?, ?, ?)", (card['id'], card['name'], card['set']['name'], card['number'], url, card.get('rarity', 'Unknown'), card['images']['large']))
            new_cards_counter += 1

        # if variant not in table already, insert into cardVariants table
        if cur.execute("SELECT id FROM cardVariants WHERE cardID = ? AND finish = ?", (card['id'], 'Regular')).fetchone() is None:    
            cur.execute("INSERT INTO cardVariants (cardID, finish) VALUES (?, ?)", (card['id'], 'Regular'))
            new_variants_counter += 1
    
        # if reverse holo exists and not in table already, insert into cardVariants table
        if has_reverse_holo and cur.execute("SELECT id FROM cardVariants WHERE cardID = ? AND finish = ?", (card['id'], 'Reverse Holo')).fetchone() is None:
            cur.execute("INSERT INTO cardVariants (cardID, finish) VALUES (?, ?)", (card['id'], 'Reverse Holo'))
            new_variants_counter += 1

    # feed back to the user how many new cards and variants were added to the database
    print(f"Inserted {new_cards_counter} new cards and {new_variants_counter} new variants into the database.")

# update price history
def update_prices(cur: sqlite3.Cursor, cards: dict[dict]) -> None:
    # ensure input is a list
    if isinstance(cards, dict):
        cards = [cards]

    # initialise a counter variable
    counter = 0

    #loop through all cards
    for card in cards:

        # check if cardmarket data exists for the card
        cardmarket = safe_get(card, 'cardmarket')
        tcgplayer = safe_get(card, 'tcgplayer')

        # reverse-holo existence is only reliable from tcgplayer (see create_new_cards)
        has_reverse_holo = safe_get(tcgplayer, 'prices', 'reverseHolofoil') is not None

        #if data exists, extract the relevant fields, otherwise set them to None
        if cardmarket is not None:
            trend_price = safe_get(cardmarket, 'prices', 'trendPrice')
            avg30 = safe_get(cardmarket, 'prices', 'avg30')
            reverse_holo_avg30 = safe_get(cardmarket, 'prices', 'reverseHoloAvg30') if has_reverse_holo else None
            reverse_holo_trend = safe_get(cardmarket, 'prices', 'reverseHoloTrend') if has_reverse_holo else None
            updated_at = safe_get(cardmarket, 'updatedAt')
        elif tcgplayer is not None:
            trend_price = safe_get(tcgplayer, 'prices', 'normal', 'market') if safe_get(tcgplayer, 'prices', 'normal', 'market') is not None else safe_get(tcgplayer, 'prices', 'holofoil', 'market')
            avg30 = safe_get(tcgplayer, 'prices', 'normal', 'mid') if safe_get(tcgplayer, 'prices', 'normal', 'mid') is not None else safe_get(tcgplayer, 'prices', 'holofoil', 'mid')
            reverse_holo_avg30 = safe_get(tcgplayer, 'prices', 'reverseHolofoil', 'mid') if has_reverse_holo else None
            reverse_holo_trend = safe_get(tcgplayer, 'prices', 'reverseHolofoil', 'market') if has_reverse_holo else None
            updated_at = safe_get(tcgplayer, 'updatedAt')
        else:
            trend_price = None
            avg30 = None
            reverse_holo_avg30 = None
            reverse_holo_trend = None
            updated_at = None
            
        # refresh prices for normal variant
        normal_variant_id = cur.execute("SELECT id FROM cardVariants WHERE cardID = ? AND finish = ?", (card['id'], 'Regular')).fetchone()[0]
        cur.execute("INSERT INTO priceHistory (variantID, averageSellPrice, trendPrice, updatedAt,capturedAt) VALUES(?, ?, ?, ?, datetime('now'))", (normal_variant_id, avg30, trend_price, updated_at))
        counter += 1

        # if reverse holo exists, refresh prices
        if has_reverse_holo:
            reverse_holo_variant_id = cur.execute("SELECT id FROM cardVariants WHERE cardID = ? AND finish = ?", (card['id'], 'Reverse Holo')).fetchone()[0]
            cur.execute("INSERT INTO priceHistory (variantID, averageSellPrice, trendPrice, updatedAt,capturedAt) VALUES(?, ?, ?, ?, datetime('now'))", (reverse_holo_variant_id, reverse_holo_avg30, reverse_holo_trend, updated_at))
            counter += 1
    
    # feed back to the user how many new price records were added to the database
    print(f"Inserted {counter} new price records into the database.")

# merge latest prices with card variants
def show_latest_prices(variants: pd.DataFrame, price_history: pd.DataFrame) -> pd.DataFrame:

    # merge the two dataframes on the variantID
    merged =  variants.merge(price_history, left_on='id', right_on='variantID', how='left')

    # get most recent prices
    latest_prices = merged.loc[merged.groupby('variantID')['capturedAt'].idxmax(), ['variantID', 'cardID', 'finish', 'averageSellPrice', 'trendPrice', 'capturedAt']].reset_index(drop=True)
    return latest_prices

# derive inventory from purchases and sales
def create_inventory(con: sqlite3.Connection) -> pd.DataFrame:

    # sqlite query to calculate the total held quantities
    query = """
        SELECT variantID, condition, SUM(qty) AS quantityHeld
        FROM (
            SELECT variantID, purchaseCondition AS condition, purchaseQuantity AS qty
            FROM purchases
            UNION ALL
            SELECT variantID, saleCondition AS condition, -saleQuantity AS qty
            FROM sales
        )
        GROUP BY variantID, condition
    """

    #load tables in dataframes
    card_variants = pd.read_sql_query("SELECT * FROM cardVariants", con).set_index('id')
    all_cards = pd.read_sql_query("SELECT * FROM allCards", con).set_index('id')
    listed_prices = pd.read_sql_query("SELECT * FROM listedPrices", con).set_index('id')
    price_history = pd.read_sql_query("SELECT * FROM priceHistory", con).set_index('id')
    current_prices = show_latest_prices(card_variants, price_history)

    # merge all required fields into inventory
    base_df = pd.read_sql(query, con)
    base_df = pd.merge(base_df, card_variants, left_on='variantID', right_on='id', how='left').merge(all_cards, left_on='cardID', right_on='id', how='left').merge(listed_prices[['variantID', 'listPrice']], left_on='variantID', right_on='variantID', how='left').merge(current_prices[['variantID', 'averageSellPrice', 'trendPrice', 'capturedAt']], left_on='variantID', right_on='variantID', how='left')
    base_df['currentValue'] = base_df.quantityHeld * base_df.averageSellPrice
    base_df['listedValue'] = base_df.quantityHeld * base_df.listPrice
    #reordered_df = base_df[['cardID', 'variantID', 'finish', 'condition', 'quantityHeld', 'rarity', 'listPrice', 'averageSellPrice', 'trendPrice', 'currentValue', 'listedValue']]
    filtered_df = base_df[base_df['quantityHeld'] != 0]
    return filtered_df

# getter function to get variant ID from card ID and finish
def get_variant_id(cur: sqlite3.Cursor, card_id: str, finish: str) -> int:

    # try to select the appropriate variant
    result = cur.execute("SELECT id FROM cardVariants WHERE cardID = ? AND finish = ?", (card_id, finish)).fetchone()

    # check if attempt was unsuccessful
    if result is None:
        
        # if unsuccessful, call the api with the right params and only the card_id as the id
        params={"select": "id,name,set,number,cardmarket,rarity,images"}
        response = call_api(params, id=card_id)

        # if API returns an error raise an exception and ask the user to check ID and try again
        if response.status_code != 200:
            raise Exception(f"API error with status code {response.status_code}. Please check ID and try again")
        
        #parse the response, create new cards in the database and fetch prices
        response_json = response.json()
        create_new_cards(cur, response_json['data'])
        update_prices(cur, response_json['data'])

        #try to select the variant again
        result = cur.execute("SELECT id FROM cardVariants WHERE cardID = ? AND finish = ?", (card_id, finish)).fetchone()

        # if there is still no variant, raise an exception and ask the user to check the finish
        if result is None:
            raise Exception("Error with card variant. Please check finish and try again")

    #pull the integer from the result as variant ID
    variant_id = result[0]
    return variant_id

# function to add a row to the purchases table
def make_purchase(cur: sqlite3.Cursor, card_id: str, finish: str, quantity: int, condition: str, price: float, date, source: str) -> None:
    
    # get variant ID
    variant_id = get_variant_id(cur, card_id, finish)

    # insert row
    cur.execute("INSERT INTO purchases (variantID, purchaseQuantity, purchaseCondition, purchasePrice, purchaseDate, purchaseSource) VALUES (?, ?, ?, ?, ?, ?)", (variant_id, quantity, condition, price, date, source))

# function to add a row to the sales table
def make_sale(cur: sqlite3.Cursor, card_id: str, finish: str, quantity: int, condition: str, price: float, date) -> None:

    # get variant ID
    variant_id = get_variant_id(cur, card_id, finish)

    # insert row
    cur.execute("INSERT INTO sales (variantID, saleQuantity, saleCondition, salePrice, saleDate) VALUES (?, ?, ?, ?, ?)", (variant_id, quantity, condition, price, date))

def calc_fifo_cost(cur: sqlite3.Cursor, variant_id: int, condition: str) -> tuple[float, float]:

    purchases_oldest_first = cur.execute("SELECT purchasePrice, purchaseQuantity FROM purchases WHERE variantID = ? AND purchaseCondition = ? ORDER BY purchaseDate ASC", (variant_id, condition)).fetchall()
    sold_quantity = cur.execute("SELECT SUM(saleQuantity) FROM sales WHERE variantID = ? AND saleCondition = ?", (variant_id, condition)).fetchone()[0]
    total_cost = cur.execute("SELECT SUM(purchasePrice * purchaseQuantity) FROM purchases WHERE variantID = ? AND purchaseCondition = ?", (variant_id, condition)).fetchone()[0]

    if sold_quantity is None:
        sold_quantity = 0

    remaining_to_sell = sold_quantity
    realised_cost = 0


    for purchase in purchases_oldest_first:
        if remaining_to_sell <= 0:
            break
        
        consumed = min(remaining_to_sell, purchase[1])
        realised_cost += purchase[0] * consumed
        remaining_to_sell -= consumed
        
    remaining_cost = total_cost - realised_cost
    return (realised_cost, remaining_cost)

def calc_current_value(inventory: pd.DataFrame) -> int:
    return inventory.currentValue.sum(), inventory.listedValue.sum()


def reset_table(cur: sqlite3.Cursor, table: str):
    cur.execute(f"DELETE FROM {table}")
