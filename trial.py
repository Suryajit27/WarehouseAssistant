import streamlit as st
from langchain_helper import get_few_shot_db_chain
import mysql.connector
import pandas as pd
# Initialize connection.
conn=mysql.connector.connect(
    host = "viaduct.proxy.rlwy.net",
    user = "root",
    password = "wgpsZHvTauJxpgyTOLsyWGPFVqvCwxGl",
    database = "railway",
    port = 35019
)

st.title("AtliQ T Shirts: Database Q&A 👕")

question = st.text_input("Question: ")

if question:
    chain = get_few_shot_db_chain()
    response = chain.invoke({
        "question": question
    })
    st.header("Answer")
    st.text(response)
    cursor=conn.cursor()
    cursor.execute(response)
    if "SELECT" not in response:
        conn.commit()
        if "supplier" in response:
            cursor.execute("SELECT * FROM supplier;")
            data=cursor.fetchall()
            df=pd.DataFrame(data,columns=cursor.column_names)
            st.dataframe(df)
        if "orders" in response:
            cursor.execute("SELECT * FROM orders;")
            data=cursor.fetchall()
            df=pd.DataFrame(data,columns=cursor.column_names)
            st.dataframe(df)
        if "inventory" in response:
            cursor.execute("SELECT * FROM inventory;")
            data=cursor.fetchall()
            df=pd.DataFrame(data,columns=cursor.column_names)
            st.dataframe(df)
    else:

        data=cursor.fetchall()
        df=pd.DataFrame(data,columns=cursor.column_names)
        st.dataframe(df)
