import sqlite3

# add new card to allCards table
def create_new_card(cur: sqlite3.Cursor, item: dict) -> None:
    # check if cardmarket data exists for the card
    cardmarket = item.get('cardmarket')

    #if data exists, extract url, otherwise set them to None
    if cardmarket is not None:
        url = cardmarket.get('url')
    else:
        url = None

    # insert card into allCards
    cur.execute("INSERT INTO allCards (id, cardName, setName, setNumber, url, rarity) VALUES (?,?, ?, ?, ?, ?)", (item['id'], item['name'], item['set']['name'], item['number'], url, item.get('rarity', 'Unknown')))

# update price history
def update_prices(cur: sqlite3.Cursor, item: dict) -> None:
        
        # check if cardmarket data exists for the card
        cardmarket = item.get('cardmarket')

        #if data exists, extract the relevant fields, otherwise set them to None
        if cardmarket is not None:
            has_reverse_holo = (cardmarket.get('prices').get('reverseHoloAvg30') != 0)
            trend_price = cardmarket.get('prices').get('trendPrice')
            avg30 = cardmarket.get('prices').get('avg30')
            reverse_holo_avg30 = cardmarket.get('prices').get('reverseHoloAvg30')
            reverse_holo_trend = cardmarket.get('prices').get('reverseHoloTrend')
            updated_at = cardmarket.get('updatedAt')
        else:
            has_reverse_holo = False
            trend_price = None
            avg30 = None
            reverse_holo_avg30 = None
            reverse_holo_trend = None
            updated_at = None   
        
        # add normal variant and price history
        cur.execute("INSERT INTO cardVariants (cardID, finish) VALUES (?, ?)", (item['id'], 'Normal'))
        cur.execute("INSERT INTO priceHistory (variantID, averageSellPrice, trendPrice, updatedAt,capturedAt) VALUES(?, ?, ?, ?, datetime('now'))", (cur.lastrowid, avg30, trend_price, updated_at))

        # if reverse holo exists, add reverse holo variant and price history
        if has_reverse_holo:
            cur.execute("INSERT INTO cardVariants (cardID, finish) VALUES (?, ?)", (item['id'], 'Reverse Holo'))
            cur.execute("INSERT INTO priceHistory (variantID, averageSellPrice, trendPrice, updatedAt,capturedAt) VALUES(?, ?, ?, ?, datetime('now'))", (cur.lastrowid, reverse_holo_avg30, reverse_holo_trend, updated_at))

