import streamlit as st
from dotenv import load_dotenv
from anthropic import Anthropic
import httpx
from database import get_database_connection
from query_generator import generate_sql_query, execute_query, generate_summary
from visualization import create_visualization

# Load environment variables
load_dotenv()

# Initialize Anthropic client
@st.cache_resource
def get_anthropic_client():
    return Anthropic(
        api_key=st.secrets["ANTHROPIC_API_KEY"],
        http_client=httpx.Client(verify=False)
    )

# Get database connection
@st.cache_resource
def get_db_connection(database):
    connection_params = {
        'host': st.secrets["MYSQL_HOST"],
        'user': st.secrets["MYSQL_USER"],
        'password': st.secrets["MYSQL_PASSWORD"],
        'database': database
    }
    return get_database_connection(connection_params)


def main():
    st.set_page_config(page_title="SQL Data Analysis with AI", page_icon="📊")
    st.title("📊 SQL Data Analysis with AI")
    
    # radio_opt=["Use SQLLite 3 Database","Connect to MySQL Database"]
    radio_opt=["Analyze iTunes data (chinook)","Analyze sales data (sales_data_sample)"]

    # Sidebar for database selection
    with st.sidebar:
        st.header("Database Selection")
        selected_opt=st.radio(label="Choose the database you want to analyze",options=radio_opt)
        if radio_opt.index(selected_opt)==0:
            database="chinook"
        else:
            database="training"

    try:
        # Initialize connections
        client = get_anthropic_client()
        connection = get_db_connection(database)
        
        # User input
        user_query = st.text_input(
            "Enter your question:",
            placeholder="e.g., Who are top 3 artists based on number of tracks?"
        )
        
        if st.button("Analyze"):
            if user_query:
                # Create tabs for organized output
                query_tab, results_tab, summary_tab, viz_tab = st.tabs([
                    "SQL Query", "Results", "Summary", "Visualization"
                ])
                
                with st.spinner("Generating SQL query..."):
                    sql_query = generate_sql_query(user_query, client, connection)
                    with query_tab:
                        st.subheader("Generated SQL Query")
                        st.code(sql_query, language="sql")
                
                with st.spinner("Executing query..."):
                    df = execute_query(sql_query, connection)
                    if not df.empty:
                        with results_tab:
                            st.subheader("Query Results")
                            st.dataframe(df)
                        
                        with st.spinner("Generating summary..."):
                            summary = generate_summary(df, client)
                            with summary_tab:
                                st.subheader("Analysis Summary")
                                st.write(summary)
                        
                        with st.spinner("Creating visualization..."):
                            fig = create_visualization(df, title=user_query)
                            if fig:
                                with viz_tab:
                                    st.subheader("Visualization")
                                    st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No data returned from the query.")
            else:
                st.warning("Please enter a question to analyze.")
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Details:", exception=e)  # This will show the full error traceback

if __name__ == "__main__":
    main()