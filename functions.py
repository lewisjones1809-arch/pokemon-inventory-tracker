import sqlite3
import requests
from dotenv import load_dotenv
import os
import re
import random
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# The marketplace export names some sets differently from the pokemontcg.io API.
# These are confirmed one-to-one renames (set name only; numbers already match).
SET_ALIASES = {
    'Base Set': 'Base',
    "McDonald's Collection 25th Anniversary": "McDonald's Collection 2021",
    'Standard Series Promos': 'Surging Sparks',
    'SV Black Star Promos': 'Scarlet & Violet Black Star Promos',
}


def resolve_card(set_name: str, cn: str) -> tuple[str, str]:
    """Translate an inventory (set, collector number) into the (setName, setNumber)
    the pokemontcg.io API actually uses, so the local allCards lookup can match.

    Returns a (api_set_name, api_set_number) tuple. Cards the export labels with a
    set/number the API doesn't share (genuinely bad or foreign data) are returned
    largely unchanged and will simply fail the downstream lookup as before.
    """
    cn = str(cn).strip()

    # normalise the set name: curly -> straight apostrophe, drop the marketplace
    # ": Additionals" suffix (secret rares that live in the base API set), alias
    name = set_name.replace('’', "'")
    if name.endswith(': Additionals'):
        name = name[:-len(': Additionals')]
    name = SET_ALIASES.get(name, name)

    # gallery / shiny-vault cards live in a SEPARATE API set, flagged by the
    # collector-number prefix. Numbers are padded to the API's width.
    m = re.match(r'^(TG|GG|SV)0*(\d+)$', cn, re.IGNORECASE)
    if m:
        prefix, digits = m.group(1).upper(), m.group(2)
        if prefix == 'TG':
            return f'{name} Trainer Gallery', f'TG{digits.zfill(2)}'
        if prefix == 'GG':
            return f'{name} Galarian Gallery', f'GG{digits.zfill(2)}'
        if prefix == 'SV':
            return f'{name} Shiny Vault', f'SV{digits.zfill(3)}'

    # SWSH promos: the export uses a bare number, the API uses SWSH### (zero-padded)
    if name == 'SWSH Black Star Promos':
        return name, 'SWSH' + re.sub(r'\D', '', cn).zfill(3)

    # default: API stores numbers without leading zeros
    return name, cn.lstrip('0')

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

def create_purchase_tiles(con: sqlite3.Connection) -> pd.DataFrame:
    # sqlite query to calculate the total held quantities
    query = """
        SELECT variantID, purchasePrice AS price, purchaseCondition AS condition, purchaseQuantity AS quantity, purchaseDate as date
        FROM purchases
    """

    #load tables in dataframes
    card_variants = pd.read_sql_query("SELECT * FROM cardVariants", con).set_index('id')
    all_cards = pd.read_sql_query("SELECT * FROM allCards", con).set_index('id')
    listed_prices = pd.read_sql_query("SELECT * FROM listedPrices", con).set_index('id')
    price_history = pd.read_sql_query("SELECT * FROM priceHistory", con).set_index('id')
    current_prices = show_latest_prices(card_variants, price_history)

    # merge all required fields into purchases
    base_df = pd.read_sql(query, con)
    base_df = pd.merge(base_df, card_variants, left_on='variantID', right_on='id', how='left').merge(all_cards, left_on='cardID', right_on='id', how='left').merge(listed_prices[['variantID', 'listPrice']], left_on='variantID', right_on='variantID', how='left').merge(current_prices[['variantID', 'averageSellPrice', 'trendPrice', 'capturedAt']], left_on='variantID', right_on='variantID', how='left')
    return base_df

def create_sale_tiles(con: sqlite3.Connection) -> pd.DataFrame:
    # sqlite query to calculate the total held quantities
    query = """
        SELECT variantID, salePrice AS price, saleCondition AS condition, saleQuantity AS quantity, saleDate AS date
        FROM sales
    """

    #load tables in dataframes
    card_variants = pd.read_sql_query("SELECT * FROM cardVariants", con).set_index('id')
    all_cards = pd.read_sql_query("SELECT * FROM allCards", con).set_index('id')
    listed_prices = pd.read_sql_query("SELECT * FROM listedPrices", con).set_index('id')
    price_history = pd.read_sql_query("SELECT * FROM priceHistory", con).set_index('id')
    current_prices = show_latest_prices(card_variants, price_history)

    # merge all required fields into sales
    base_df = pd.read_sql(query, con)
    base_df = pd.merge(base_df, card_variants, left_on='variantID', right_on='id', how='left').merge(all_cards, left_on='cardID', right_on='id', how='left').merge(listed_prices[['variantID', 'listPrice']], left_on='variantID', right_on='variantID', how='left').merge(current_prices[['variantID', 'averageSellPrice', 'trendPrice', 'capturedAt']], left_on='variantID', right_on='variantID', how='left')
    return base_df

# getter function to get variant ID from card ID and finish
def get_variant_id(cur: sqlite3.Cursor, card_id: str, finish: str, create_if_missing: bool = False) -> int:

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

        # if there is still no variant, the API doesn't list this finish for the card.
        # When loading owned inventory the row IS ground truth (we physically hold the
        # card), so create the variant on demand rather than dropping it; its prices
        # just stay null. Other callers keep the original strict behaviour.
        if result is None:
            if create_if_missing:
                cur.execute("INSERT INTO cardVariants (cardID, finish) VALUES (?, ?)", (card_id, finish))
                return cur.lastrowid
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

    if total_cost is None:
        total_cost = 0

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


def reset_table(con: sqlite3.Connection, table: str):
    cur = con.cursor()
    cur.execute(f"DELETE FROM {table}")
    con.commit()

@st.cache_data
def get_inventory(_con):
    return create_inventory(_con)

@st.cache_data
def get_purchases(_con):
    return create_purchase_tiles(_con)

@st.cache_data
def get_sales(_con):
    return create_sale_tiles(_con)

def insert_dummy(con):
    """Populate the database with a realistic sample inventory so users without an
    existing inventory CSV can explore the tool's features.

    A fresh install starts empty, so we first import a recognizable set ("151")
    from the pokemontcg.io API (real cards + prices), then log ~100 purchases with
    varying quantities, conditions, dates and prices, plus a subset of sales. The
    purchases/sales/listedPrices tables are wiped first so the button is repeatable.

    Requires POKEMON_API_KEY and internet access.
    """
    SET_NAME = "151"
    CONDITIONS = ['MT', 'NM', 'EX', 'GD', 'LP', 'PL', 'PO']
    CONDITION_WEIGHTS = [1, 5, 2, 1, 4, 2, 1]  # weighted toward NM / LP
    SOURCES = ['eBay', 'Local Store', 'Online Marketplace', 'Card Fair', 'Bundle']

    rng = random.Random(42)  # fixed seed -> reproducible dummy data

    # 1. clean slate (leave allCards/cardVariants/priceHistory intact - we add to them)
    reset_table(con, 'purchases')
    reset_table(con, 'sales')
    reset_table(con, 'listedPrices')

    cur = con.cursor()

    # 2. import the set from the API - one page (pageSize 250) covers the whole set
    params = {
        'q': f'set.name:"{SET_NAME}"',
        'select': 'id,name,set,number,cardmarket,tcgplayer,rarity,images',
        'page': 1,
        'pageSize': 250,
    }
    response = call_api(params)
    if response.status_code != 200:
        raise Exception(f"API error with status code {response.status_code}. Check POKEMON_API_KEY / connection and try again.")

    cards = response.json()['data']
    create_new_cards(cur, cards)
    update_prices(cur, cards)

    if cur.execute("SELECT setName FROM importedSets WHERE setName = ?", (SET_NAME,)).fetchone() is None:
        cur.execute("INSERT INTO importedSets (setName) VALUES (?)", (SET_NAME,))
    con.commit()

    # 3. pick ~100 variants spanning the set, with each one's latest market price
    variant_rows = cur.execute(
        """
        SELECT v.cardID, v.finish,
               (SELECT ph.trendPrice FROM priceHistory ph
                WHERE ph.variantID = v.id ORDER BY ph.capturedAt DESC LIMIT 1) AS trendPrice,
               (SELECT ph.averageSellPrice FROM priceHistory ph
                WHERE ph.variantID = v.id ORDER BY ph.capturedAt DESC LIMIT 1) AS avgPrice
        FROM cardVariants v
        JOIN allCards c ON c.id = v.cardID
        WHERE c.setName = ?
        ORDER BY v.cardID, v.finish
        """,
        (SET_NAME,),
    ).fetchall()

    if not variant_rows:
        raise Exception(f'No cards found for set "{SET_NAME}" after import.')

    # take ~100 evenly across the set so prices span commons -> chase cards
    target = min(100, len(variant_rows))
    step = max(1, len(variant_rows) // target)
    chosen = variant_rows[::step][:target]

    def market_price(trend, avg):
        for price in (trend, avg):
            if price is not None and price > 0:
                return price
        return 0.25  # floor for cards the API has no price for

    today = datetime.now()

    # 4. log purchases (varying quantity, condition, date, price and source)
    held = []  # [card_id, finish, condition, qty, market, purchase_date] for sales/listings
    for card_id, finish, trend, avg in chosen:
        market = market_price(trend, avg)
        condition = rng.choices(CONDITIONS, weights=CONDITION_WEIGHTS)[0]
        qty = rng.randint(1, 8)
        purchase_date = (today - timedelta(days=rng.randint(30, 365))).strftime('%Y-%m-%d')
        price = round(market * rng.uniform(0.5, 0.9), 2)
        make_purchase(cur, card_id, finish, qty, condition, price, purchase_date, rng.choice(SOURCES))
        held.append([card_id, finish, condition, qty, market, purchase_date])

        # a handful get a second purchase lot (different date/price/condition) for FIFO
        if rng.random() < 0.15:
            condition2 = rng.choices(CONDITIONS, weights=CONDITION_WEIGHTS)[0]
            qty2 = rng.randint(1, 5)
            date2 = (today - timedelta(days=rng.randint(30, 365))).strftime('%Y-%m-%d')
            price2 = round(market * rng.uniform(0.5, 0.9), 2)
            make_purchase(cur, card_id, finish, qty2, condition2, price2, date2, rng.choice(SOURCES))
            held.append([card_id, finish, condition2, qty2, market, date2])

    # 5. log sales over a ~35% subset - sell part of a lot so inventory stays non-empty
    for card_id, finish, condition, qty, market, purchase_date in held:
        if qty < 2 or rng.random() >= 0.35:
            continue
        purchased_on = datetime.strptime(purchase_date, '%Y-%m-%d')
        span = (today - purchased_on).days
        if span < 1:
            continue
        sell_qty = rng.randint(1, qty - 1)
        sale_date = (purchased_on + timedelta(days=rng.randint(1, span))).strftime('%Y-%m-%d')
        sale_price = round(market * rng.uniform(0.9, 1.3), 2)  # some profit, some loss
        make_sale(cur, card_id, finish, sell_qty, condition, sale_price, sale_date)

    # 6. listed prices (near market) so listedValue populates, one per variant+condition
    listed_seen = set()
    for card_id, finish, condition, qty, market, purchase_date in held:
        variant_id = get_variant_id(cur, card_id, finish)
        if (variant_id, condition) in listed_seen:
            continue
        listed_seen.add((variant_id, condition))
        list_price = round(market * rng.uniform(1.0, 1.2), 2)
        cur.execute("INSERT INTO listedPrices (variantID, listPrice, condition) VALUES (?, ?, ?)", (variant_id, list_price, condition))

    con.commit()
