import streamlit as st
import sqlite3
import pandas as pd
import math
from functions import create_inventory, calc_fifo_cost, calc_current_value

# Create a connection to the database
con = sqlite3.connect('pokemon_tracker.db')

# Create a cursor object to execute SQL commands
cur = con.cursor()

# Create the inventory and get current value
inventory = create_inventory(con)
current_value, listed_value = calc_current_value(inventory)

# Initalise running totals
total_remaining_cost = 0
total_realised_basis = 0

# Compute realised cost and remaining cost
for index, card in inventory.iterrows():
    fifo = calc_fifo_cost(cur, card['variantID'], card['condition'])
    total_remaining_cost += fifo[1]
    total_realised_basis += fifo[0]

# Compute unrealised margin
unrealised_margin = round(current_value - total_remaining_cost, 2)

# Compute total sales
total_sales = cur.execute("SELECT SUM(salePrice * saleQuantity) FROM sales").fetchone()[0]

# Compute profit
realised_p_l = round(total_sales - total_realised_basis,2)

# Close connection
con.close()

st.title("Card Tracker")
st.set_page_config(layout='wide')

inv, sale, prof, unreal, listed = st.columns(5)

inv.metric('Inventory Value', f'£{current_value:.2f}')
sale.metric('Total Sales', f'£{total_sales:.2f}')
prof.metric('Lifetime Profit', f'£{realised_p_l:.2f}')
unreal.metric('Unrealised Margin', f'£{unrealised_margin:.2f}')
listed.metric('Total Listing Value', f'£{listed_value:.2f}')

with st.container(height = 650, ):
    cols = st.columns(4)
    for i, (_, card) in enumerate(inventory.iterrows()):
        col = cols[i % 4]
        if i % 4 == 0 and i != 0:
            cols = st.columns(4)
            col = cols[0]
        tile = col.container(height = 310, border=True)
        left_title, right_title = tile.columns([9,1])
        left_title.markdown(f'{card['cardName']} | {card['setName']} {card['setNumber']}  \nCondition: {card['condition']}')
        if card['finish'] == 'Reverse Holo':
            right_title.write('🌟')
        _, mid, _ = tile.columns([1,2,1])
        mid.image(card['imageURL'])
        left_list, right_list = tile.columns([2,1])
        left_list.write(f'Listed for: £{card['listPrice']:.2f}')
        right_list.write(f'Quantity: {card['quantityHeld']}')
