import streamlit as st
import pandas as pd
from pandasai import SmartDataframe
from pandasai import SmartDatalake
from langchain_openai import AzureChatOpenAI
import os


# Page config
st.set_page_config(page_title="Multi-File Excel Analyzer & Chat", layout="wide")

# Add main header
st.header("The Hartford Operational Chatbot")
st.markdown("---")  # Add separator line

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "dfs" not in st.session_state:
    st.session_state.dfs = {}
if "merged_df" not in st.session_state:
    st.session_state.merged_df = None
if "current_df" not in st.session_state:
    st.session_state.current_df = None

# Initialize LLM
llm = AzureChatOpenAI(
    azure_deployment='',
    api_key='',
    api_version='',
    azure_endpoint='',
    temperature=0.7
)

# In the sidebar
with st.sidebar:
    st.header("Upload Excel Files")

    # File upload section
    uploaded_files = st.file_uploader("Supported files format - xlsx and xls", type=['xlsx', 'xls'], accept_multiple_files=True)

    if uploaded_files:
        for file in uploaded_files:
            try:
                st.session_state.dfs[file.name] = pd.read_excel(file)
                st.success(f"Loaded: {file.name}")
            except Exception as e:
                st.error(f"Error loading {file.name}: {str(e)}")

    # File selection and preview
    if st.session_state.dfs:
        selected_file = st.selectbox(
            "Select file to analyze:",
            options=list(st.session_state.dfs.keys())
        )
        # Show preview
        if selected_file:
            st.subheader(f"Preview: {selected_file}")
            st.dataframe(st.session_state.dfs[selected_file].head())

        # Merge option
        if len(st.session_state.dfs) > 1 and st.button("Merge All Files"):
            try:
                st.session_state.merged_df = pd.concat(st.session_state.dfs.values(), ignore_index=True)
                st.success("Files merged successfully!")
                st.dataframe(st.session_state.merged_df.head())
            except Exception as e:
                st.error(f"Merge error: {str(e)}")

# Main chat area
st.header("Chat with your Data")

if st.session_state.dfs:
        chat_source = st.radio(
            "Choose data source:",
            ["Selected File", "Merged Data"] if st.session_state.merged_df is not None else ["Selected File"]
        )

        try:
            # Set current dataframe based on selection
            if chat_source == "Selected File":
                st.session_state.current_df = st.session_state.dfs[selected_file]
            else:
                st.session_state.current_df = st.session_state.merged_df

            # Initialize SmartDataframe with current data
            if st.session_state.current_df is not None:
                try:
                    smart_df = SmartDataframe(st.session_state.current_df, config={'llm': llm})

                    # Chat input
                    user_input = st.text_area("Ask about your data:", height=100)
                    if user_input:  # Remove last_input check
                        try:
                            response = smart_df.chat(user_input)
                            # Check if response is a DataFrame
                            if isinstance(response, pd.DataFrame):
                                st.table(response)  # Display as table
                            else:
                                st.write(response)  # Display as regular text

                            st.session_state.messages.append({"role": "user", "content": user_input})
                            st.session_state.messages.append({"role": "assistant", "content": str(response)})
                        except Exception as e:
                            st.error(f"Chat error: {str(e)}")

                    # Display chat history
                    chat_container = st.container()
                    with chat_container:
                        for message in reversed(st.session_state.messages):
                            with st.chat_message(message["role"]):
                                st.write(message["content"])

                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
