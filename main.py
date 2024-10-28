import os
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime, timedelta
import numpy as np
import io


# Import the data processing functions from provided files
from data_process import process_data, process_and_store_data, get_todays_data

from get_data import fetch_data_from_api

# Constants
PARAMETERS = {
    'pH': {'name': 'pH Level', 'unit': '', 'color': '#1f77b4', 'range': [6, 9]},
    'TDS': {'name': 'TDS', 'unit': 'ppm', 'color': '#ff7f0e', 'range': [0, 500]},
    'Depth': {'name': 'Water Level', 'unit': 'm', 'color': '#2ca02c', 'range': [0, 10]},
    'FlowInd': {'name': 'Flow Rate', 'unit': 'kL/10min', 'color': '#d62728', 'range': [0, 100]}
}

TIME_RANGES = {
    '1H': '1 Hour',
    '6H': '6 Hours',
    '12H': '12 Hours',
    '1D': '1 Day',
    '1W': '1 Week',
    'Custom': 'Custom Range'
}

AGGREGATIONS = {
    '10 Min': '10T',  # Raw data interval
    '30 Min': '30T',
    '1 Hour': 'H',
    '4 Hour': '4H',
    'Daily': 'D'
}

# API URL Configuration
API_URL = "https://mongodb-api-hmeu.onrender.com"
# Initialize Flask
server = Flask(__name__)
server.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

# Initialize Dash app
app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css'
    ]
)
app.title = 'Water Quality Monitoring'


# Add a basic Flask route for the root URL
@server.route('/')
def index():
    return '''
    <h1>Water Quality Monitoring System</h1>
    <p>Please visit the <a href="/dashboard/">dashboard</a> to view the monitoring system.</p>
    '''
def create_metric_card(title, icon_class, param_key):
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon_class} text-primary", style={'fontSize': '24px'}),
                html.H5(title, className="mb-0 ms-2")
            ], className="d-flex align-items-center mb-2"),
            html.Div([
                html.H3(id=f"{param_key}-value", children="--", className="mb-0"),
                html.Small(PARAMETERS[param_key]['unit'], className="text-muted ms-1")
            ], className="d-flex align-items-baseline")
        ])
    ], className="h-100")

app.layout = dbc.Container([
    # Header
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H2("Water Quality Monitoring System", className="mb-0"),
                    html.P("Real-time monitoring and analysis", className="text-muted mb-0")
                ], width=8),
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-clock me-2"),
                        html.Span(id="live-timestamp", className="h5")
                    ], className="text-end")
                ], width=4)
            ])
        ])
    ], className="mb-4"),
    
    # Main Content
    dbc.Row([
        # Left Sidebar - Filters
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Data Filters", className="mb-0")),
                dbc.CardBody([
                    html.Label("Select Parameters"),
                    dcc.Dropdown(
                        id='parameter-select',
                        options=[{'label': params['name'], 'value': param} 
                                for param, params in PARAMETERS.items()],
                        value=list(PARAMETERS.keys())[0],
                        multi=True,
                        className="mb-3"
                    ),
                    
                    html.Label("Time Range"),
                    dcc.Dropdown(
                        id='time-range-select',
                        options=[{'label': v, 'value': k} for k, v in TIME_RANGES.items()],
                        value='6H',
                        className="mb-3"
                    ),
                    
                    html.Div(
                        id='custom-date-container',
                        children=[
                            html.Label("Custom Date Range"),
                            dcc.DatePickerRange(
                                id='date-picker-range',
                                className="mb-3"
                            )
                        ],
                        style={'display': 'none'}
                    ),
                    
                    html.Label("Data Aggregation"),
                    dcc.Dropdown(
                        id='aggregation-select',
                        options=[{'label': k, 'value': v} for k, v in AGGREGATIONS.items()],
                        value='10T',
                        className="mb-3"
                    ),
                    
                    dbc.Button(
                        "Export Data",
                        id="export-btn",
                        color="success",
                        className="w-100"
                    )
                ])
            ])
        ], width=3),
        
        # Right Content
        dbc.Col([
            # Metrics Cards
            dbc.Row([
                dbc.Col(create_metric_card("pH Level", "fas fa-vial", "pH"), width=3),
                dbc.Col(create_metric_card("TDS Level", "fas fa-water", "TDS"), width=3),
                dbc.Col(create_metric_card("Flow Rate", "fas fa-gauge-high", "FlowInd"), width=3),
                dbc.Col(create_metric_card("Water Level", "fas fa-arrow-down-wide-short", "Depth"), width=3),
            ], className="mb-4"),
            
            # Time Series Chart
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Time Series Analysis", className="mb-0")),
                        dbc.Col(
                            dbc.Badge(
                                "Live Data Updates Every 10 Minutes",
                                color="primary",
                                className="float-end"
                            )
                        )
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(id='time-series-plot', style={'height': '50vh'})
                ])
            ], className="mb-4"),
            
            # Data Table
            dbc.Card([
                dbc.CardHeader(html.H5("Historical Data", className="mb-0")),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='data-table',
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'fontFamily': 'Arial'
                        },
                        style_header={
                            'backgroundColor': '#f8f9fa',
                            'fontWeight': 'bold'
                        },
                        page_size=10,
                        sort_action='native',
                        filter_action='native'
                    )
                ])
            ])
        ], width=9)
    ]),
    
    dcc.Download(id="download-data"),
    dcc.Interval(id='update-interval', interval=600000, n_intervals=0),  # 10 minutes
    dcc.Interval(id='clock-interval', interval=1000, n_intervals=0),  # 1 second
    dcc.Store(id='data-store'),
    
], fluid=True, className="px-4 py-3")

@app.callback(
    Output('custom-date-container', 'style'),
    Input('time-range-select', 'value')
)
def toggle_custom_date(selected_range):
    if selected_range == 'Custom':
        return {'display': 'block'}
    return {'display': 'none'}

@app.callback(
    Output('live-timestamp', 'children'),
    Input('clock-interval', 'n_intervals')
)
def update_timestamp(n):
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.callback(
    [Output('time-series-plot', 'figure'),
     Output('data-table', 'data'),
     Output('data-table', 'columns'),
     Output('data-store', 'data')] +
    [Output(f"{param}-value", 'children') for param in PARAMETERS.keys()],
    [Input('parameter-select', 'value'),
     Input('time-range-select', 'value'),
     Input('aggregation-select', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('update-interval', 'n_intervals')]
)
def update_dashboard(selected_params, time_range, aggregation, custom_start, custom_end, n_intervals):
    # Fetch and process new data using imported functions
    process_and_store_data(API_URL)
    df = get_todays_data()
    
    if df.empty:
        return px.line(), [], [], {}, *['--' for _ in PARAMETERS]
    


    
    # Ensure selected_params is a list
    if isinstance(selected_params, str):
        selected_params = [selected_params]
    
    # Time range filtering
    end_time = df['timestamp'].max()
    if time_range == 'Custom' and custom_start and custom_end:
        start_time = pd.to_datetime(custom_start)
        end_time = pd.to_datetime(custom_end)
    else:
        hours_delta = {
            '1H': 1, '6H': 6, '12H': 12,
            '1D': 24, '1W': 168
        }
        start_time = end_time - pd.Timedelta(hours=hours_delta.get(time_range, 6))
    
    df_filtered = df[df['timestamp'].between(start_time, end_time)]
    
    # Aggregation
    df_agg = df_filtered.resample(aggregation, on='timestamp').agg({
        param: 'mean' for param in PARAMETERS.keys()
    }).reset_index()
    
    # Create time series plot
    fig = go.Figure()
    for param in selected_params:
        param_config = PARAMETERS[param]
        fig.add_trace(go.Scatter(
            x=df_agg['timestamp'],
            y=df_agg[param],
            name=f"{param_config['name']} ({param_config['unit']})" if param_config['unit'] else param_config['name'],
            line=dict(color=param_config['color'])
        ))
    
    fig.update_layout(
        margin=dict(l=50, r=20, t=20, b=50),
        xaxis_title="Time",
        yaxis_title="Value",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white"
    )
    
    # Prepare table data
    table_data = df_agg.to_dict('records')
    columns = [{"name": i, "id": i} for i in df_agg.columns]
    
    # Get latest values for metric cards
    latest_values = []
    latest_row = df.iloc[-1]
    for param in PARAMETERS.keys():
        latest_values.append(f"{latest_row[param]:.2f}")
    
    # Store data for export
    stored_data = df_agg.to_json(date_format='iso', orient='split')
    
    return fig, table_data, columns, stored_data, *latest_values

@app.callback(
    Output("download-data", "data"),
    Input("export-btn", "n_clicks"),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def export_data(n_clicks, stored_data):
    if not n_clicks or not stored_data:
        return None
    
    df = pd.read_json(stored_data, orient='split')
    return dcc.send_data_frame(
        df.to_excel,
        f"water_quality_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        sheet_name="Data",
        index=False
    )

if __name__ == '__main__':
    # Initial data fetch
    process_and_store_data(API_URL)
    
    # Get deployment configuration from environment variables
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Run the Flask server
    server.run(host='0.0.0.0', port=port, debug=debug)


    
