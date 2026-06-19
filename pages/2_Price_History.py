import streamlit as st
import pandas as pd
from functions import get_connection

con = get_connection()

st.title('Price History')