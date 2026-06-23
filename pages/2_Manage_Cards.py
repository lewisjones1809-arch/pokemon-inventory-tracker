import streamlit as st
from natsort import natsorted
from functions import make_purchase, make_sale, get_connection, get_inventory, get_all_cards

con = get_connection()
cur = con.cursor()

def _txt(df, col):
    return df[col].astype('string[python]').fillna('')

st.title('Manage Cards')

all_cards = get_all_cards(con)

all_cards['display'] = (
_txt(all_cards, 'cardName') + ' | ' +
_txt(all_cards, 'setName') + ' | CN ' +
_txt(all_cards, 'setNumber') + ' | ' +
_txt(all_cards, 'rarity') + ' | ' +
_txt(all_cards, 'finish')
)
purchase_options = natsorted(all_cards['display'].unique().tolist())

purchase_card = st.selectbox('Select Card', options=purchase_options)

purchase_matches = all_cards[all_cards['display'] == purchase_card]
if purchase_matches.empty:
    st.warning('No cards found')
    st.stop()
chosen_purchase = purchase_matches.iloc[0]

card_id_purchase = chosen_purchase['cardID']
finish_purchase = chosen_purchase['finish']

st.write('Log a purchase')
with st.form("purchase_form", clear_on_submit=True, enter_to_submit=False):

    row1 = st.columns([1,1])
    quantity_purchase = row1[0].number_input('Quantity Purchased', min_value=1, step=1)
    condition_purchase = row1[1].selectbox('Condition', ['MT', 'NM', 'EX', 'GD', 'LP', 'PL', 'PO'])
    
    row2 = st.columns([1,1,1])
    price_paid = row2[0].number_input('Price Paid per Card', min_value=0.0, step=0.5)
    purchase_date = row2[1].date_input('Purchase Date', max_value='today', format='DD/MM/YYYY')
    source = row2[2].selectbox('Source', ['eBay', 'WhatNot', 'CardMarket', 'In-store', 'Other'])

    purchase_submit = st.form_submit_button('Make Purchase', use_container_width=True)

if purchase_submit:
    try:
        make_purchase(cur, card_id_purchase, finish_purchase, quantity_purchase, condition_purchase, price_paid, purchase_date, source)
        con.commit()
        st.success('Purchase Logged!')
    except Exception as e:
        st.error(f'Could not log purchase: {e}')




st.write('Log a sale')

inventory = get_inventory(con)

inventory['display'] = (
_txt(inventory, 'cardName') + ' | ' +
_txt(inventory, 'setName') + ' | CN ' +
_txt(inventory, 'setNumber') + ' | ' +
_txt(inventory, 'rarity') + ' | ' +
_txt(inventory, 'finish') + ' | ' +
_txt(inventory, 'condition') + ' | Qty: ' +
_txt(inventory, 'quantityHeld')
)
sale_options = natsorted(inventory['display'].unique().tolist())

sale_card = st.selectbox('Select Card', options=sale_options)

sale_matches = inventory[inventory['display'] == sale_card]
if sale_matches.empty:
    st.warning('No inventory found')
    st.stop()
chosen_sale = sale_matches.iloc[0]

card_id_sale = chosen_sale['cardID']
finish_sale = chosen_sale['finish']
condition_sale = chosen_sale['condition']

with st.form("sale_form", clear_on_submit=True, enter_to_submit=False):

    row1 = st.columns([1,1,1])
    price_sold = row1[0].number_input('Price Sold per Card', min_value=0.0, step=0.5)
    quantity_sale = row1[1].number_input('Quantity Sold', min_value=1, step=1, max_value=int(chosen_sale['quantityHeld']))
    sale_date = row1[2].date_input('Sale Date', max_value='today', format='DD/MM/YYYY')

    sale_submit = st.form_submit_button('Make Sale', use_container_width=True)

if sale_submit:
    try: 
        make_sale(cur, card_id_sale, finish_sale, quantity_sale, condition_sale, price_sold, sale_date)
        con.commit()
        st.success('Sale Logged!')
    except Exception as e:
        st.error(f'Could not log sale: {e}')