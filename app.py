import streamlit as st
import pandas as pd
from pandasai import SmartDataframe
from pandasai import SmartDatalake
from langchain_openai import AzureChatOpenAI

# Page config
st.set_page_config(page_title="Excel Analyzer & Chat", layout="wide")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "df" not in st.session_state:
    st.session_state.df = None

# Initialize LLM
llm = AzureChatOpenAI(
    azure_deployment='',
    api_key='',
    api_version='2024-08-01-preview',
    azure_endpoint='',
    temperature=0.7
)

# File upload section
uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        st.session_state.df = pd.read_excel(uploaded_file)
        st.write("Data Preview:")
        st.dataframe(st.session_state.df.head())

        # Initialize SmartDataframe
        smart_df = SmartDataframe(st.session_state.df, config={'llm': llm})
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")

# Chat interface
st.sidebar.title("Chat with your Data")

if st.session_state.df is not None:
    user_input = st.sidebar.text_input("Ask about your data:")

    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        try:
            # Get response from SmartDataframe
            response = smart_df.chat(user_input)
            st.session_state.messages.append({"role": "assistant", "content": str(response)})
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")

# Display chat history
for message in st.session_state.messages:
    with st.sidebar.chat_message(message["role"]):
        st.write(message["content"])
