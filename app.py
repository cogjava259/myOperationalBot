import streamlit as st
import pandas as pd
from pandasai import SmartDataframe
from pandasai import SmartDatalake
from langchain_openai import AzureChatOpenAI
import os

# Define system messages for different report types
SYSTEM_MESSAGES = {
    "Allocation Report": """You are an allocation report analysis assistant. You are a helpful operational assistant who is an expert in handling datasets. 
    If a user asks to get the utilization percentage then calculate the ratio of sum of allocation percentage where associate billability is any of BTM, BFD, BTB and sum of allocation percentage for all associate billability types.
    If a user asks to get the on off ratio or onsite offshore ratio then calculate the ratio of sum of allocation percentage 
    where OffShoreOnsite is ON and sum of allocation percentage for all OffShoreOnsite types.
    """,

    "Per Report": """You are a performance report analyst. Focus on:
- Individual performance metrics
- Time-based trends
- KPI analysis
- Growth patterns
- Performance comparisons""",

    "Others": """You are a general data analysis assistant. Focus on:
- Data insights
- Pattern recognition
- Statistical analysis
- Trend identification"""
}

# Add predefined prompts
PREDEFINED_PROMPTS = {
    "Calculate Utilization %": "What is the utilization percentage?",
    "Calculate Onsite/Offshore Ratio": "What is the on off ratio?",
    "Calculate PA Minus Ratio": "Consider  if GradeDescription has value as either Existing - P & e or  Existing - PA & e or Existing - PAT & e or Existing - PT & e  understand as ""PA-"" or ""PA minus"". Consider the sum of AllocationPercentage of ""PA-"" as ""PA Minus up ratio"". Consider the sum of all valules of AllocationPercentage column as Total Allocation Percentage.  Consider ""PA Minus Ratio"" is the value of ""PA Minus up ratio"" divided by Total Allocation Percentage. what is ""PA   Minus Ratio"" showing upto 4 decimal points.",
    "Calculate Span": "Consider GradeDescription has value as either Business Associate 35 or Business Associate 50 or Business Associate 60 or Existing - AVP & e or Existing - D & e or Existing - SA & e or Existing - Sr. Director & e or Existing - VP & e or Existing-AD&e or Existing-M&e or Existing-SM&e or New-SM&e understand as ""SA+"" and Business Associate 65 or Existing - A & e or Existing - P & e or Existing - PA & e or Existing - PAT & e or Existing - PT & e understand as ""A-"". Consider Span Calculation as sum of AllocationPercentage of ""A-"" divided by sum of AllocationPercentage of ""SA+"". What is span Calulcation.",
    "Calculate M+": "Consider GradeDescription has value as either Business Associate 35 or Business Associate 50 or Existing - AVP & e or Existing - D & e or Existing - Sr. Director & e or Existing - VP & e or Existing-AD&e or Existing-M&e or Existing-SM&e or New-SM&e understand as ""M+"".Consider the sum of all valules of AllocationPercentage column as Total Allocation Percentage. Consider M+ Calculation as sum of AllocationPercentage of ""M+"" divided by Total Allocation Percentage. What is M+ Calculation.",
    "Custom Query": "Type your own query..."
}

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
if "file_types" not in st.session_state:
    st.session_state.file_types = {}

# Initialize session state for report type
if "report_type" not in st.session_state:
    st.session_state.report_type = "Others"

# In the sidebar
with st.sidebar:
    st.header("Upload Excel Files")

    # Report type selection
    selected_report_type = st.selectbox(
        "Select Report Type:",
        ["Allocation Report", "BPO Report", "Others"],
        key="report_type_selector"
    )
    st.session_state.report_type = selected_report_type
    # Initialize LLM
    llm = AzureChatOpenAI(
        azure_deployment='',
        api_key='',
        api_version='',  ### get it from Target URL instead of from screen
        azure_endpoint='',
        temperature=0.7
    )
    # File upload section
    uploaded_files = st.file_uploader(
        f"Upload {selected_report_type} files (xlsx/xls)",
        type=['xlsx', 'xls'],
        accept_multiple_files=True
    )
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


        def get_user_query():
            st.header("Query Options")
            selected_prompt = st.selectbox(
                "Select your query:",
                options=list(PREDEFINED_PROMPTS.keys())
            )

            if selected_prompt == "Custom Query":
                user_input = st.text_area("Ask about your data:", height=100)
            else:
                user_input = PREDEFINED_PROMPTS[selected_prompt]
                st.info(f"Prompt for the Selected Options: \n {user_input}")

            return user_input

        # Initialize SmartDataframe with report-specific context
        if st.session_state.current_df is not None:
            try:
                # Initialize SmartDataframe with context-aware LLM
                smart_df = SmartDataframe(
                    st.session_state.current_df,
                    config={
                        'llm': llm,
                        'conversational': True,
                        'custom_prompts': {
                            'system': SYSTEM_MESSAGES[st.session_state.report_type],
                            'user': lambda query: f"""
                        Context: {SYSTEM_MESSAGES[st.session_state.report_type]}
                        Question: {query}
                        Please analyze the data based on this context.
                    """
                        }
                    }
                )
                # Create two columns for chat input and button
                # col1, col2 = st.columns([4, 1])

                # with col1:

                # user_input = st.text_area("Ask about your data:", height=100)
                user_input = get_user_query()
                # with col2:
                # Add button aligned with text area
                if st.button("Send", key="chat_button"):
                    if user_input:
                        try:
                            response = smart_df.chat(user_input)

                            if isinstance(response, pd.DataFrame):
                                st.table(response)
                            else:
                                st.write(response)

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

# After the file preview section, add dashboard components
if st.session_state.dfs and selected_file:
    st.markdown("---")
    st.header("📊 Interactive Dashboard")

    # Get current dataframe
    df = st.session_state.dfs[selected_file]

    # Create two columns for metrics and charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Data Overview")
        # Display key metrics
        total_rows = len(df)
        total_cols = len(df.columns)
        st.metric("Total Records", total_rows)
        st.metric("Total Columns", total_cols)

        # Column statistics
        st.subheader("Column Statistics")
        selected_column = st.selectbox(
            "Select column for statistics:",
            options=df.select_dtypes(include=['int64', 'float64']).columns
        )
        if selected_column:
            stats = df[selected_column].describe()
            st.dataframe(stats)

    with col2:
        st.subheader("Data Visualization")
        # Chart type selector
        chart_type = st.selectbox(
            "Select chart type:",
            ["Bar Chart", "Line Chart", "Scatter Plot"]
        )

        # Get columns for X and Y axis
        x_col = st.selectbox("Select X-axis:", options=df.columns, key="x_axis")
        y_col = st.selectbox("Select Y-axis:",
                             options=df.select_dtypes(include=['int64', 'float64']).columns,
                             key="y_axis")

        # Create charts based on selection
        if chart_type == "Bar Chart":
            st.bar_chart(data=df, x=x_col, y=y_col)
        elif chart_type == "Line Chart":
            st.line_chart(data=df, x=x_col, y=y_col)
        elif chart_type == "Scatter Plot":
            st.scatter_chart(data=df, x=x_col, y=y_col)

    # Add data filtering options
    st.subheader("Data Filters")
    with st.expander("Filter Data"):
        filter_col = st.selectbox("Select column to filter:", options=df.columns)
        if df[filter_col].dtype in ['int64', 'float64']:
            min_val = float(df[filter_col].min())
            max_val = float(df[filter_col].max())
            filter_range = st.slider(
                f"Select range for {filter_col}",
                min_val, max_val,
                (min_val, max_val)
            )
            filtered_df = df[
                (df[filter_col] >= filter_range[0]) &
                (df[filter_col] <= filter_range[1])
                ]
        else:
            unique_vals = df[filter_col].unique()
            selected_vals = st.multiselect(
                f"Select values for {filter_col}",
                options=unique_vals,
                default=unique_vals
            )
            filtered_df = df[df[filter_col].isin(selected_vals)]

        st.dataframe(filtered_df)
