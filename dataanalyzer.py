import streamlit as st
import mysql.connector
import pandas as pd
from pathlib import Path
import plotly.express as px
from langchain_groq import ChatGroq
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.callbacks import StreamlitCallbackHandler
from langchain.tools import Tool
from typing import List, Dict, Any
import sqlite3
import os

# Initialize session state variables
def init_session_state():
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'conversation' not in st.session_state:
        st.session_state.conversation = None
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'chart_type' not in st.session_state:
        st.session_state.chart_type = 'line'

init_session_state()

LOCALDB="USE_LOCALDB"
MYSQL="USE_MYSQL"

# Custom tool for data visualization
class DataVisualizationTool:
    def __init__(self):
        self.name = "data_visualization"
        self.description = """Useful for creating visualizations from dataframes. 
        Input should be a dictionary with 'data' (pandas DataFrame), 'chart_type' (str), 
        'x' (str), 'y' (str), and optional 'title' (str)."""

    def _create_plot(self, data: pd.DataFrame, chart_type: str, x: str, y: str, title: str = None) -> None:
        if chart_type.lower() == "bar":
            fig = px.bar(data, x=x, y=y, title=title)
        elif chart_type.lower() == "line":
            fig = px.line(data, x=x, y=y, title=title)
        elif chart_type.lower() == "scatter":
            fig = px.scatter(data, x=x, y=y, title=title)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        st.plotly_chart(fig)

    def run(self, query: Dict[str, Any]) -> str:
        try:
            self._create_plot(
                data=query['data'],
                chart_type=query['chart_type'],
                x=query['x'],
                y=query['y'],
                title=query.get('title', '')
            )
            return "Visualization created successfully"
        except Exception as e:
            return f"Error creating visualization: {str(e)}"

# Custom tool for data summarization
class DataSummarizationTool:
    def __init__(self, llm):
        self.name = "data_summarization"
        self.description = "Useful for summarizing data analysis findings in bullet points"
        self.llm = llm

    def run(self, query: str) -> str:
        prompt = f"""
        Based on the following data analysis results, provide a clear summary in bullet points:
        {query}
        Please format the response as markdown bullet points.
        """
        return self.llm.invoke(prompt).content

def main():
    st.set_page_config(page_title="LangChain: Chat with SQL DB", page_icon="📊")
    st.title("📊 LangChain: Chat with SQL DB")
    
    radio_opt=["Use SQLLite 3 Database","Connect to MySQL Database"]

    # Sidebar for database credentials
    with st.sidebar:
        st.header("Database Connection")
        selected_opt=st.radio(label="Choose the DB which you want to chat",options=radio_opt)
        if radio_opt.index(selected_opt)==1:
            db_uri=MYSQL
            mysql_host=st.sidebar.text_input("Provide MySQL Host",st.secrets["host"])
            mysql_user=st.sidebar.text_input("MYSQL User", st.secrets["user"])
            mysql_password=st.sidebar.text_input("MYSQL password",st.secrets["password"], type="password")
            mysql_db=st.sidebar.text_input("MySQL database", st.secrets["database"])
        else:
            db_uri=LOCALDB

    # Connect to database
    if db_uri==MYSQL:
        db = SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"))

    else:
        dbfilepath=(Path(__file__).parent/"chinook.db").absolute()
        print(dbfilepath)
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        db = SQLDatabase(create_engine("sqlite:///", creator=creator))

    # Initialize LLM
    llm = ChatGroq(
        api_key=st.secrets["GROQ_API_KEY"],
        model_name="Llama3-8b-8192",
        streaming=True
        )

    sql_toolkit = SQLDatabaseToolkit(db=db, llm=llm)
            
    visualization_tool = Tool(
                name="data_visualization",
                func=DataVisualizationTool().run,
                description="Use this tool to create visualizations from data"
            )
            
    summarization_tool = Tool(
                name="data_summarization",
                func=DataSummarizationTool(llm).run,
                description="Use this tool to summarize findings in bullet points"
            )

    # Create and initialize agent
    agent = create_sql_agent(
                llm=llm,
                toolkit=sql_toolkit,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                additional_tools=[visualization_tool, summarization_tool]
            )

    # Initialize or clear message history
    if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    # Display message history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    user_query=st.chat_input(placeholder="Ask anything from the database")

    # Handle user input
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        with st.chat_message("assistant"):
            streamlit_callback=StreamlitCallbackHandler(st.container())
            try:
                response=agent.run(user_query,callbacks=[streamlit_callback])
                st.session_state.messages.append({"role":"assistant","content":response})
                st.write(response)
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
                
if __name__ == "__main__":
    main()
