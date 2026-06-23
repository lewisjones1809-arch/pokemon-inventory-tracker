import streamlit as st
import sqlite3
import pandas as pd
import math
from functions import get_inventory, calc_fifo_cost, calc_current_value, resolve_card
from st_keyup import st_keyup

# Create a connection to the database
con = sqlite3.connect('pokemon_tracker.db')

# Create a cursor object to execute SQL commands
cur = con.cursor()

# Create the inventory and get current value
inventory = get_inventory(con)
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

if total_sales is None:
    total_sales = 0

# Compute profit
realised_p_l = round(total_sales - total_realised_basis,2)

# Close connection
con.close()

st.set_page_config(layout='wide')
st.title("Card Tracker")

inv, sale, prof, unreal, listed = st.columns(5)

inv.metric('Inventory Value', f'£{current_value:.2f}')
sale.metric('Total Sales', f'£{total_sales:.2f}')
prof.metric('Lifetime Profit', f'£{realised_p_l:.2f}')
unreal.metric('Unrealised Margin', f'£{unrealised_margin:.2f}')
listed.metric('Total Listing Value', f'£{listed_value:.2f}')

top_filt_row = st.columns(3)
with top_filt_row[0]:
    name_filt = st_keyup('Card Name', key='name_input', placeholder='e.g Ekans', debounce=300)
set_filt = top_filt_row[1].selectbox('Set', sorted({resolve_card(s, cn)[0] for s, cn in zip(inventory['setName'], inventory['setNumber'])}), index=None, placeholder='e.g 151')
sort_by = top_filt_row[2].selectbox('Sort by', ['Name ASC', 'Name DESC', 'Set ASC', 'Set DESC', 'Price ASC', 'Price DESC', 'Number ASC', 'Number DESC'])
sort_column = ''
[split_sort, asc_desc] = sort_by.split()

current_filter = name_filt or ''

inventory = inventory[inventory['cardName'].str.contains(name_filt)]
if set_filt is not None:
    inventory = inventory[inventory['setName'] == set_filt]

if split_sort == 'Name':
    sort_column = 'cardName'
elif split_sort == 'Set':
    sort_column = 'setName'
elif split_sort == 'Price':
    sort_column = 'listPrice'
elif split_sort == 'Number':
    sort_column = 'setNumber'

if asc_desc == 'ASC':
    asc_desc = True
else:
    asc_desc = False

inventory = inventory.sort_values(by=[sort_column], ascending=asc_desc)

# Paginate the inventory grid
page_size = 40
total_pages = max(1, math.ceil(len(inventory) / page_size))
page = st.number_input('Page', min_value=1, max_value=total_pages, value=1, step=1)
start = (page - 1) * page_size
page_inventory = inventory.iloc[start:start + page_size]
st.caption(f'Showing {start + 1}-{min(start + page_size, len(inventory))} of {len(inventory)} cards')

with st.container(height = 650, ):
    cols = st.columns(4)
    for i, (_, card) in enumerate(page_inventory.iterrows()):
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
