import pandas as pd
import sqlite3
from functions import call_api, create_new_cards, update_prices, get_variant_id, create_inventory, get_set_id_from_name, resolve_card
import time
import csv

def load_inventory_from_pd(con: sqlite3.Connection, existing_inventory, page_size=250, set_status=None, row_progress=None):

    cur = con.cursor()

    english = existing_inventory[existing_inventory['language'] == 'English']
    sets = sorted({resolve_card(s, cn)[0] for s, cn in zip(english['set'], english['cn'])})
    imported_sets = {row[0] for row in cur.execute("SELECT setName FROM importedSets")}

    for i, set in enumerate(sets):
        if set in imported_sets:
            continue

        if set_status:
            set_status(f"Loading set {i+1} of {len(sets)}: {set}")

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

            if response.status_code != 200:
                time.sleep(5)
                continue

            cards = response.json()['data']

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
        

    counter = skipped = failed = 0
    seen, failed_cards = {}, []
    total = len(existing_inventory)

    for index, card in existing_inventory.iterrows():
        try:
            if card['language'] != 'English':
                skipped += 1
                continue

            card_name = card['name']
            # translate the export's set name + collector number into what the API uses
            set_name, collector_number = resolve_card(card['set'], card['cn'])
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

            variant_id = get_variant_id(cur, card_id, finish, create_if_missing=True)
            cur.execute("INSERT INTO purchases (variantID, purchaseQuantity, purchaseCondition, purchasePrice, purchaseDate, purchaseSource) VALUES (?, ?, ?, ?, datetime('now'), ?)", (variant_id, quantity, condition, None, 'Initial Inventory'))
            cur.execute("INSERT INTO listedPrices (variantID, listPrice, condition) VALUES (?, ?, ?)", (variant_id, list_price, condition))
            counter += 1
            con.commit()
        except Exception as e:
            failed += 1
            failed_cards.append({'Card' : card_name, 'Exception' : e})
        
        if row_progress:
             row_progress((index+1)/total)

    return counter, skipped, failed, failed_cards