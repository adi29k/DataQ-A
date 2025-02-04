import plotly.graph_objects as go
import pandas as pd

def create_visualization(df: pd.DataFrame, title: str = "Data Visualization"):
    try:
        if df.empty:
            return None
            
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        
        if len(numeric_columns) == 0:
            return None
            
        x_column = df.columns[0]
        y_column = numeric_columns[0]
        
        fig = go.Figure(data=[
            go.Bar(
                x=df[x_column],
                y=df[y_column],
                marker_color='rgb(55, 83, 109)',
                marker_line_color='rgb(8,48,107)',
                marker_line_width=1.5
            )
        ])
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title=x_column,
            yaxis_title=y_column,
            plot_bgcolor='white',
            width=800,
            height=500,
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        raise Exception(f"Visualization error: {str(e)}")