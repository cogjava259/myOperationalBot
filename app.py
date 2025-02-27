import os
import pandas as pd
from pandasai import SmartDataframe
from pandasai import SmartDatalake
from langchain_openai import AzureChatOpenAI
import datetime
import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="Data Analysis Assistant",
    page_icon="📊",
    layout="wide"
)

# Initialize LLM
llm = AzureChatOpenAI(
    azure_deployment='dep',
    api_key='key',
    api_version='2024-08-01-preview',
    azure_endpoint='',
    temperature=0.7
)

# File paths for production
DATA_DIR = os.path.join(os.getcwd(), 'data')
filename1 = os.path.join(DATA_DIR, 'file1.xlsx')
filename2 = os.path.join(DATA_DIR, 'file2.xlsx')

# Load and merge dataframes
@st.cache_data
def load_data():
    df1 = pd.read_excel(filename1)
    df1['ReportDate'] = report_date1
    df2 = pd.read_excel(filename2)
    df2['ReportDate'] = report_date2
    return pd.concat([df1, df2], ignore_index=True)


# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Load data and create SmartDataframe
merged_df = load_data()
sdframe = SmartDataframe(
    merged_df,
    config={
        "llm": llm,
        "save_charts": True,
        "save_charts_path": user_defined_path,
    }
)

# Create UI elements
st.title("Data Analysis Assistant")
st.write("Ask questions about your data!")

# Chat interface
user_input = st.text_input("Enter your question:", key="user_input")

if st.button("Send"):
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Get response from PandasAI
        response = sdframe.chat(user_input)

        # Handle different types of responses
        if isinstance(response, pd.DataFrame):
            st.dataframe(response)
        elif isinstance(response, str):
            st.write(response)

        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": str(response)})

# Display chat history
st.subheader("Chat History")
for message in st.session_state.chat_history:
    role = message["role"]
    content = message["content"]

    if role == "user":
        st.info(f"You: {content}")
    else:
        st.success(f"Assistant: {content}")