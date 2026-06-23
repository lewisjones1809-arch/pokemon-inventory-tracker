import streamlit as st
import pandas as pd
from functions import get_connection

con = get_connection()
sales = pd.read_sql("SELECT * FROM sales", con)

st.title('Sales History')

st.dataframe(sales)