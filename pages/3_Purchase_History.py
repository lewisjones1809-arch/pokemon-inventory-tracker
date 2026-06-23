import streamlit as st
import pandas as pd
from functions import get_connection, resolve_card, create_purchase_tiles
from st_keyup import st_keyup
import math

con = get_connection()
purchases = create_purchase_tiles(con)

st.title('Purchase History')

top_filt_row = st.columns(3)
with top_filt_row[0]:
    name_filt = st_keyup('Card Name', key='name_input', placeholder='e.g Ekans', debounce=300)
set_filt = top_filt_row[1].selectbox('Set', sorted({resolve_card(s, cn)[0] for s, cn in zip(purchases['setName'], purchases['setNumber'])}), index=None, placeholder='e.g 151')
sort_by = top_filt_row[2].selectbox('Sort by', ['Name ASC', 'Name DESC', 'Set ASC', 'Set DESC', 'Price ASC', 'Price DESC', 'Number ASC', 'Number DESC'])
sort_column = ''
[split_sort, asc_desc] = sort_by.split()

current_filter = name_filt or ''

purchases= purchases[purchases['cardName'].str.contains(current_filter, case=False)]
if set_filt is not None:
    purchases = purchases[purchases['setName'] == set_filt]

if split_sort == 'Name':
    sort_column = 'cardName'
elif split_sort == 'Set':
    sort_column = 'setName'
elif split_sort == 'Price':
    sort_column = 'pricerice'
elif split_sort == 'Number':
    sort_column = 'setNumber'

if asc_desc == 'ASC':
    asc_desc = True
else:
    asc_desc = False

purchases = purchases.sort_values(by=[sort_column], ascending=asc_desc)

# Paginate the purchases grid
page_size = 40
total_pages = max(1, math.ceil(len(purchases) / page_size))
page = st.number_input('Page', min_value=1, max_value=total_pages, value=1, step=1)
start = (page - 1) * page_size
page_purchases = purchases.iloc[start:start + page_size]
st.caption(f'Showing {start + 1}-{min(start + page_size, len(purchases))} of {len(purchases)} cards')

with st.container(height = 650, ):
    cols = st.columns(4)
    for i, (_, card) in enumerate(page_purchases.iterrows()):
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
        left_list.write(f'Cost per card: £{card['price']:.2f}')
        right_list.write(f'Quantity: {card['quantity']}')