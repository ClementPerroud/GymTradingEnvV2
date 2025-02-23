import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import datetime

from .renderer import AbstractRenderer
# --------------------------------------------------------------------------
# Sample DataFrame
# --------------------------------------------------------------------------

class DashboardRenderer(AbstractRenderer):
    def __init__(self) -> None:

        self.app = dash.Dash(__name__)
        self.app.layout = html.Div([
            html.H1("Trading/Portfolio Dashboard", style={'text-align': 'center'}),
            html.Button('Refresh', id='refresh-button', n_clicks=0, style={'margin': '20px auto', 'display': 'block'}),
            dcc.Graph(
                id='main-chart',
                figure={},
                style={'width': '90%', 'height': '70vh', 'margin': 'auto'}
            ),

            html.Div(
                id='point-data',
                style={
                    'width': '90%', 
                    'margin': 'auto', 
                    'padding': '20px', 
                    'border': '1px solid #ccc', 
                    'borderRadius': '5px'
                }
            )
        ])
        self.dates = []
        self.portfolio_expositions = []
        self.portfolio_valuations = []
        self.prices = []
        self.rewards = []
        self.callbacks(self.app)
        self.app.run(debug=True)
        
    async def reset(self, seed = None, **kwargs):
        await super().reset(seed = seed, **kwargs)
        self.infos_manager = self.get_trading_env().infos_manager
        self.time_manager  = self.get_trading_env().time_manager
        
        self.dates = []
        self.portfolio_expositions = []
        self.portfolio_valuations = []
        self.prices = []
        self.rewards = []

    async def render_step(self, *args, **kwargs):
        date = await self.time_manager.get_current_datetime()
        infos = self.infos_manager.historical_infos[date]
        
        asset = infos['assets'][0]
        pair = infos['pairs'][0]
        self.dates.append(infos['date'])
        self.portfolio_expositions.append(infos[f'portfolio_exposition_{asset}'])
        self.portfolio_valuations.append(infos['portfolio_valuation'])
        self.prices.append(infos[f'price_{pair}'])
        self.rewards.append(infos['reward'])


    def callbacks(self, app):
        @app.callback(
            Output('main-chart', 'figure'),
            Input('refresh-button', 'n_clicks')  # Just a dummy input to build the figure initially
        )
        def update_graph(_):

            fig = go.Figure()
            # 1) portfolio_valuation
            fig.add_trace(go.Scatter(x=self.dates,y=self.portfolio_valuations,mode='lines+markers',name='Portfolio Valuation'))
            # 2) position_exposition_BTC
            fig.add_trace(go.Scatter(x=self.dates,y=self.portfolio_expositions,mode='lines+markers',name='Position Exposition', yaxis='y2'))
            # 3) price_BTCUSDT
            fig.add_trace(go.Scatter(x=self.dates,y=self.prices,mode='lines+markers',name='Price',yaxis='y3'))

            # Create up to 3 y-axes for clarity:
            fig.update_layout(
                xaxis=dict(domain=[0, 0.85]),  # main x-axis
                yaxis=dict(
                    title="Portfolio Valuation",
                    title_font=dict(color="#1f77b4"),
                    tickfont=dict(color="#1f77b4"),
                ),
                yaxis2=dict(
                    title="Exposition",
                    title_font=dict(color="#ff7f0e"),
                    tickfont=dict(color="#ff7f0e"),
                    anchor="x", overlaying="y", side="right"
                ),
                yaxis3=dict(
                    title="Price",
                    title_font=dict(color="#2ca02c"),
                    tickfont=dict(color="#2ca02c"),
                    anchor="free", overlaying="y", side="right", position=0.90
                ),
                legend=dict(
                    x=0.02,
                    y=0.98,
                    bgcolor="rgba(255,255,255,0.6)"
                ),
                hovermode="x unified",
                title="Portfolio / Positions / Price"
            )

            return fig

        @app.callback(
            Output('point-data', 'children'),
            Input('main-chart', 'clickData')
        )
        def display_click_data(clickData):
            """
            Show the record details of the point the user clicked.
            If the user hasn't clicked anything, show a default message.
            """

            if clickData is None:
                return html.Div(["Click a point in the chart to see details."])

            # Extract the x-value (which will be the date in our figure)
            # The "points" list can contain multiple points if multiple traces share an x.
            # We'll just grab the first for demonstration.
            point = clickData['points'][0]
            clicked_date : datetime.datetime = point['x']

            # For safety, convert to pandas Timestamp if necessary
            # (Depending on how Dash returns date, it might be a str or datetime)
            clicked_date = pd.to_datetime(clicked_date)

            # Find the row in our df that matches the clicked date
            # You can customize how you match; for example, if you have multiple rows
            # with the same date, or times, you might want a more robust approach.
            row_dict = self.infos_manager.historical_infos[clicked_date]
            if len(row_dict) == 0:return html.Div(["No data for this date."])

            # Build a nice HTML table or list
            info_items = []
            for k, v in row_dict.items():
                info_items.append(html.Tr([html.Td(str(k)), html.Td(str(v))]))

            table = html.Table(
                # Table headings
                [html.Tr([html.Th("Key"), html.Th("Value")])] + info_items,
                style={
                    'borderCollapse': 'collapse',
                    'width': '100%'
                }
            )
            return html.Div([
                html.H3(f"Details for Date: {clicked_date}"),
                table
            ])

    