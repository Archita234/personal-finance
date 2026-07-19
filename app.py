import streamlit as st
import pandas as pd

st.title("Personal Finance Dashboard")

data = pd.read_csv("bank_transactions.csv")

st.dataframe(data.head())