import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Stock Portfolio Tracker"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Input(id='ticker-input', type='text', placeholder='Enter stock ticker (e.g. AAPL)'),
            dcc.Input(id='shares-input', type='number', placeholder='Number of shares'),
            dbc.Button('Add to Portfolio', id='add-button', n_clicks=0, color='primary')
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            html.H3("Your Portfolio"),
            html.Ul(id='portfolio-list')
        ], width=4),
        dbc.Col([
            dcc.Graph(id='portfolio-graph')
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            html.Label('Remove stock from portfolio:'),
            dcc.Dropdown(id='remove-dropdown'),
            dbc.Button('Remove', id='remove-button', n_clicks=0, color='danger')
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            html.Label('Select number of days to view:'),
            dcc.Slider(
                id='days-slider',
                min=1,
                max=365,
                step=1,
                value=30,
                marks={i: f'{i}d' for i in range(0, 366, 30)}
            ),
            html.Div(id='slider-output-container')
        ], width=8)
    ])
])

# Global variable to hold the portfolio
portfolio = {}

@app.callback(
    [Output('portfolio-list', 'children'),
     Output('portfolio-graph', 'figure'),
     Output('remove-dropdown', 'options'),
     Output('remove-dropdown', 'value'),
     Output('slider-output-container', 'children')],
    [Input('add-button', 'n_clicks'),
     Input('remove-button', 'n_clicks'),
     Input('days-slider', 'value')],
    [State('ticker-input', 'value'),
     State('shares-input', 'value'),
     State('remove-dropdown', 'value')]
)
def update_portfolio(add_clicks, remove_clicks, days, ticker, shares, remove_ticker):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    if ctx.triggered[0]['prop_id'] == 'add-button.n_clicks' and ticker and shares:
        if ticker not in portfolio:
            portfolio[ticker] = int(shares)
        else:
            portfolio[ticker] += int(shares)
    elif ctx.triggered[0]['prop_id'] == 'remove-button.n_clicks' and remove_ticker:
        portfolio.pop(remove_ticker, None)

    portfolio_items = [html.Li(f"{ticker}: {shares} shares") for ticker, shares in portfolio.items()]
    remove_options = [{'label': ticker, 'value': ticker} for ticker in portfolio.keys()]

    # Fetch data and create the plot
    if portfolio:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        combined_df = pd.DataFrame()

        for ticker, shares in portfolio.items():
            stock_data = yf.download(ticker, start=start_date, end=end_date)
            stock_data['Ticker'] = ticker
            stock_data['Shares'] = shares
            stock_data['Total Value'] = stock_data['Close'] * shares
            combined_df = pd.concat([combined_df, stock_data])

        combined_df = combined_df.reset_index()

        fig = go.Figure()

        # Plot each stock's value
        for ticker in combined_df['Ticker'].unique():
            ticker_df = combined_df[combined_df['Ticker'] == ticker]
            fig.add_trace(go.Scatter(x=ticker_df['Date'], y=ticker_df['Total Value'], mode='lines', name=ticker))

        # Calculate and plot the combined portfolio value
        combined_df['Date'] = pd.to_datetime(combined_df['Date'])
        combined_value_df = combined_df.groupby('Date').sum().reset_index()
        fig.add_trace(go.Scatter(x=combined_value_df['Date'], y=combined_value_df['Total Value'], mode='lines', name='Total Portfolio Value', line=dict(width=4, dash='dash')))

        fig.update_layout(title=f'Portfolio Value Over Last {days} Days', xaxis_title='Date', yaxis_title='Value (USD)')

    else:
        fig = go.Figure()

    return portfolio_items, fig, remove_options, None, f'Showing data for the last {days} days'

if __name__ == '__main__':
    app.run_server(debug=True)