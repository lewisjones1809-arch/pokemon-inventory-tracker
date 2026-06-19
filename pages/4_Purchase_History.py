import streamlit as st
import pandas as pd
from functions import get_connection

con = get_connection()
purchases = pd.read_sql("SELECT * FROM purchases", con)

st.title('Purchase History')

st.dataframe(purchases)