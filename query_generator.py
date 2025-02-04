from anthropic import Anthropic
import pandas as pd
from typing import Dict

def get_database_schema(connection) -> str:
    try:
        cursor = connection.cursor()
        schema_info = []
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            schema_info.append(f"Table: {table_name}")
            schema_info.append("Columns: " + ", ".join(f"{col[0]} ({col[1]})" for col in columns))
        
        return "\n".join(schema_info)
    except Exception as e:
        raise Exception(f"Schema extraction error: {str(e)}")

def generate_sql_query(user_query: str, client: Anthropic, connection) -> str:
    try:
        db_schema = get_database_schema(connection)
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[
                {"role": "user", "content": f"""Given this database schema:
                {db_schema}
                
                Generate ONLY the SQL query (no explanations) for: {user_query}
                The response should contain only the SQL query itself, nothing else.
                """}
            ]
        )
        
        generated_query = response.content[0].text
        
        # Clean up the query
        if "```sql" in generated_query:
            generated_query = generated_query.split("```sql")[1].split("```")[0].strip()
        elif "```" in generated_query:
            generated_query = generated_query.split("```")[1].strip()
        
        return generated_query.strip()
        
    except Exception as e:
        raise Exception(f"Query generation error: {str(e)}")

def execute_query(sql_query: str, connection) -> pd.DataFrame:
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        cursor.close()
        
        if rows:
            return pd.DataFrame(rows)
        else:
            return pd.DataFrame()
            
    except Exception as e:
        raise Exception(f"Query execution error: {str(e)}")

def generate_summary(df: pd.DataFrame, client: Anthropic) -> str:
    try:
        if df.empty:
            return ""
            
        # Convert dataframe to string with a more robust method
        df_string = df.to_markdown()
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[
                {"role": "user", "content": f"""Please summarize the following query results:
                
                {df_string}
                
                Focus on the key insights and trends in the data. Be concise and highlight the most important findings."""}
            ]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        raise Exception(f"Summarization error: {str(e)}")