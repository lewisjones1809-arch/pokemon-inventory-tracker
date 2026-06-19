import streamlit as st
from functions import make_purchase, make_sale, get_connection

con = get_connection()
cur = con.cursor()

st.title('Manage Cards')

st.write('Log a purchase')
with st.form("purchase_form", clear_on_submit=True, enter_to_submit=False):
    card_id = st.text_input('Card ID')

    row1 = st.columns([1,1,1])
    finish = row1[0].selectbox('Finish', ['Normal', 'Reverse Holo'])
    quantity = row1[1].number_input('Quantity Purchased', min_value=1, step=1)
    condition = row1[2].selectbox('Condition', ['Mint', 'Near Mint', 'Excellent', 'Lightly Played', 'Moderately Played', 'Heavily Played', 'Poor'])
    
    row2 = st.columns([1,1,1])
    price_paid = row2[0].number_input('Price Paid per Card', min_value=0.0, step=0.5)
    purchase_date = row2[1].date_input('Purchase Date', max_value='today', format='DD/MM/YYYY')
    source = row2[2].selectbox('Source', ['eBay', 'WhatNot', 'CardMarket', 'In-store', 'Other'])

    purchase_submit = st.form_submit_button('Make Purchase', use_container_width=True)

if purchase_submit:
    make_purchase(cur, card_id, finish, quantity, condition, price_paid, purchase_date, source)
    con.commit()
    st.success('Purchase Logged!')

st.write('Log a sale')
with st.form("sale_form", clear_on_submit=True, enter_to_submit=False):
    card_id = st.text_input('Card ID')

    row1 = st.columns([1,1,1])
    finish = row1[0].selectbox('Finish', ['Normal', 'Reverse Holo'])
    quantity = row1[1].number_input('Quantity Sold', min_value=1, step=1)
    condition = row1[2].selectbox('Condition', ['Mint', 'Near Mint', 'Excellent', 'Lightly Played', 'Moderately Played', 'Heavily Played', 'Poor'])
    
    row2 = st.columns([1,1])
    price_sold = row2[0].number_input('Price Sold per Card', min_value=0.0, step=0.5)
    sale_date = row2[1].date_input('Sale Date', max_value='today', format='DD/MM/YYYY')

    sale_submit = st.form_submit_button('Make Sale', use_container_width=True)

if sale_submit:
    make_sale(cur, card_id, finish, quantity, condition, price_sold, sale_date)
    con.commit()
    st.success('Sale Logged!')