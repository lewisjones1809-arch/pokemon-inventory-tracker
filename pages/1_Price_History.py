import streamlit as st
import pandas as pd
from datetime import timedelta
from functions import get_connection, get_inventory, get_variant_id

con = get_connection()

st.title('Price History')

inventory = get_inventory(con)
inventory['display'] = (
inventory['cardName'] + ' | ' +
inventory['setName'] + ' | CN ' +
inventory['setNumber'].astype(str) + ' | ' +
inventory['rarity'] + ' | ' +
inventory['finish']
)
options = inventory['display'].unique().tolist()

card = st.selectbox('Select Card', options=options)

chosen_row = inventory[inventory['display'] == card].iloc[0]

card_id = chosen_row['cardID']
finish = chosen_row['finish']
variant_id = get_variant_id(con.cursor(), card_id, finish)

price_chart = pd.read_sql_query(
    "SELECT capturedAt, averageSellPrice, trendPrice FROM priceHistory WHERE variantID = ? ORDER BY capturedAt",
    con,
    params=(int(variant_id),),
)
price_chart['capturedAt'] = pd.to_datetime(price_chart['capturedAt'])

latest_date = price_chart['capturedAt'].max()
seven_days_prior = latest_date - timedelta(days = 7)
thirty_days_prior = latest_date - timedelta(days = 30)

seven_prior = price_chart[price_chart['capturedAt'] <= seven_days_prior].sort_values(by='capturedAt', ascending=False)
value_seven_prior = seven_prior['averageSellPrice'].iloc[0]
seven_perc = 100*(chosen_row['averageSellPrice'] - value_seven_prior)/value_seven_prior
if seven_perc > 0:
    seven_sign = '+'
else:
    seven_sign = ''

thirty_prior = price_chart[price_chart['capturedAt'] <= thirty_days_prior].sort_values(by='capturedAt', ascending=False)
value_thirty_prior = thirty_prior['averageSellPrice'].iloc[0]
thirty_perc = 100*(chosen_row['averageSellPrice'] - value_thirty_prior)/value_thirty_prior
if thirty_perc > 0:
    thirty_sign = '+'
else:
    thirty_sign = ''

value, seven_change, thirty_change, peak = st.columns(4)

value.metric('Current Value', f'£{chosen_row['averageSellPrice']:.2f}')
seven_change.metric('7 day % Change', f'{seven_sign}{seven_perc:.2f}%')
thirty_change.metric('30 day % Change', f'{thirty_sign}{thirty_perc:.2f}%')
peak.metric('Peak value', f'£{price_chart['averageSellPrice'].max():.2f}')


st.line_chart(price_chart, x='capturedAt', y='averageSellPrice', x_label='Date', y_label='Average Sale Price')