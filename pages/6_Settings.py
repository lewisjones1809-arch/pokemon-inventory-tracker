import streamlit as st
from functions import reset_table, get_connection

con = get_connection()

st.title('Settings')

table = st.selectbox('Reset Table:', ['allCards', 'cardVariants', 'purchases', 'sales', 'listedPrices', 'priceHistory', 'importedSets'])
st.button('Reset Table', on_click=reset_table(con.cursor(), table))