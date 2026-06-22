import pandas as pd
import sqlite3
from functions import call_api, create_new_cards, update_prices, get_variant_id, create_inventory, get_set_id_from_name
import time
import csv

con = sqlite3.connect('pokemon_tracker.db')
cur = con.cursor()
purchases_table = pd.read_sql_query('SELECT * FROM purchases', con)

existing_inventory = pd.read_csv('inventory.csv')
english = existing_inventory[existing_inventory['language'] == 'English']
sets = english['set'].unique()
loaded_inventory = create_inventory(con)

# sets already fully imported on a previous run - skip these so a re-run
# after a failure doesn't re-call the API for work that's already done
imported_sets = {row[0] for row in cur.execute("SELECT setName FROM importedSets")}

page_size = 250

for set in sets:
    if set in imported_sets:
        print(f'Skipping {set} (already imported)')
        continue

    print(f'Now Importing {set}...')
    page = 1

    while True:
        params = {
            'q': f'set.name:"{set}"',
            'select': 'id,name,set,number,cardmarket,tcgplayer,rarity,images',
            'page': page,
            'pageSize': page_size,
        }
        time.sleep(0.1)
        response = call_api(params)
        response_data = response.json()
        cards = response_data['data']

        create_new_cards(cur, cards)
        update_prices(cur, cards)

        # a short page means we've reached the end of this set
        if len(cards) < page_size:
            break
        page += 1

    # mark the set as done in the SAME commit as its card data, so it's only
    # recorded as imported if all its pages were written successfully
    cur.execute("INSERT INTO importedSets (setName) VALUES (?)", (set,))
    con.commit()
    print(f'{set} imported!')
    

counter = 0
skipped = 0
failed = 0

seen = {}
failed_cards = []

for index, card in existing_inventory.iterrows():
    try:
        if card['language'] != 'English':
            skipped += 1
            continue

        card_name = card['name']
        set_name = card['set']
        collector_number = card['cn'].lstrip('0')
        finish = card['finishType']

        if finish == 'ReverseHolo':
            finish = 'Reverse Holo'

        condition = card['condition']
        quantity = card['quantity']
        list_price = card['price']

        key = (set_name, collector_number)
        if key in seen:
            card_id = seen[key]
        else:
            # look the card up locally - the top loop already loaded every
            # card in these sets into allCards, so no API call is needed here.
            result = cur.execute(
                "SELECT id FROM allCards WHERE setName = ? AND setNumber = ?",
                (set_name, collector_number)
            ).fetchone()

            if result is None:
                raise Exception(f"No card found in allCards for {set_name} #{collector_number}")

            card_id = result[0]
            seen[key] = card_id

        variant_id = get_variant_id(cur, card_id, finish)
        cur.execute("INSERT INTO purchases (variantID, purchaseQuantity, purchaseCondition, purchasePrice, purchaseDate, purchaseSource) VALUES (?, ?, ?, ?, datetime('now'), ?)", (variant_id, quantity, condition, None, 'Initial Inventory'))
        cur.execute("INSERT INTO listedPrices (variantID, listPrice, condition) VALUES (?, ?, ?)", (variant_id, list_price, condition))
        counter += 1
        con.commit()
    except Exception as e:
        failed += 1
        failed_cards.append({'Card' : card_name, 'Exception' : e})
        print(f'Failed: {card_name} - {e}')

with open('failures.csv', 'w') as out:
            csv_out = csv.DictWriter(out, fieldnames=['Card', 'Exception'])
            csv_out.writeheader()
            csv_out.writerows(failed_cards)

print(f'Successfully migrated {counter} English cards. {skipped} cards in other languages skipped. {failed} cards failed to import')
con.close()

#existing_inventory.to_sql(purchases_table, con, if_exists='append')