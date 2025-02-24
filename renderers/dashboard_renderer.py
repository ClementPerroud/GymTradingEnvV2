import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime

from .renderer import AbstractRenderer

class DashboardRenderer(AbstractRenderer):
    def __init__(self, 
            app_kwargs: dict = dict(host = "0.0.0.0", jupyter_mode="external", debug=True, port=8050, enable_host_checking = False)
        )-> None:
        super().__init__()

        # Store episode data in a dictionary keyed by episode_index
        # Each entry will have lists of 'dates', 'portfolio_expositions', etc.
        self.episodes_dict = {}
        self.current_episode = 0  # Will increment each time `reset` is called

        self.app = dash.Dash(__name__)

        # App Layout
        self.app.layout = html.Div([
            html.H1("Trading/Portfolio Dashboard", style={'text-align': 'center'}),

            # Episode Selection + Refresh
            html.Div([
                html.Button(
                    'Refresh', 
                    id='refresh-button', 
                    n_clicks=0, 
                    style={'marginRight': '20px'}
                ),
                dcc.Dropdown(
                    id='episode-selector',
                    placeholder="Select Episode",
                    style={'width': '200px', 'display': 'inline-block', 'verticalAlign': 'middle'}
                )
            ], style={'textAlign': 'center', 'margin': '20px'}),

            # Data Range Picker
            html.Div([
                html.Label("Select Date Range: ", style={'marginRight': '10px'}),
                dcc.DatePickerRange(
                    id='date-range',
                    display_format='DD/MM/YYYY',
                    start_date=datetime.datetime(2020, 1, 1),
                    end_date=datetime.datetime(2025, 12, 31),
                    style={'display': 'inline-block', 'verticalAlign': 'middle'}
                )
            ], style={'textAlign': 'center', 'margin': '20px'}),

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

        # Register callbacks
        self.callbacks(self.app)

        self.app.run(**app_kwargs)

    async def reset(self, seed=None, **kwargs):
        """
        Called every time a new RL episode is started.
        """
        await super().reset(seed=seed, **kwargs)

        self.infos_manager = self.get_trading_env().infos_manager
        self.time_manager = self.get_trading_env().time_manager

        # Increment current episode index
        self.current_episode += 1

        # Initialize new lists for storing data for this episode
        self.episodes_dict[self.current_episode] = {
            'dates': [],
            'portfolio_expositions': [],
            'portfolio_valuations': [],
            'prices': [],
            'rewards': [],
            'infos': {}
        }
    
    async def render_step(self, *args, **kwargs):
        """
        Called at each step of the simulation.
        We store each step's data in self.episodes_dict[current_episode].
        """
        date = await self.time_manager.get_current_datetime()
        infos = self.infos_manager.historical_infos[date]

        asset = infos['assets'][0]
        pair = infos['pairs'][0]

        self.episodes_dict[self.current_episode]['dates'].append(date)
        self.episodes_dict[self.current_episode]['portfolio_expositions'].append(
            infos[f'portfolio_exposition_{asset}']
        )
        self.episodes_dict[self.current_episode]['portfolio_valuations'].append(
            infos['portfolio_valuation']
        )
        self.episodes_dict[self.current_episode]['prices'].append(
            infos[f'price_{pair}']
        )
        self.episodes_dict[self.current_episode]['rewards'].append(infos['reward'])

        self.episodes_dict[self.current_episode]['infos'][date] = infos

    def callbacks(self, app):

        # 1) Update the Episode Selector Dropdown Options whenever 'Refresh' is clicked
        @app.callback(
            Output('episode-selector', 'options'),
            Output('episode-selector', 'value'),
            Input('refresh-button', 'n_clicks'),
            prevent_initial_call=False
        )
        def update_episode_dropdown(n_clicks):
            """
            Build the list of possible episodes from self.episodes_dict
            and pick the newest episode as default.
            """
            if not self.episodes_dict:
                # No episodes stored yet
                return [], None

            # Build options
            options = [
                {'label': f"Episode {ep}", 'value': ep}
                for ep in sorted(self.episodes_dict.keys())
            ]
            # Default to the most recent episode
            newest_episode = max(self.episodes_dict.keys())
            return options, newest_episode

        # 2) Update the Main Chart whenever 'Refresh' or selected Episode changes
        @app.callback(
            Output('main-chart', 'figure'),
            Input('refresh-button', 'n_clicks'),
            Input('episode-selector', 'value'),
            Input('date-range', 'start_date'),
            Input('date-range', 'end_date')
        )
        def update_graph(_, selected_episode, start_date, end_date):
            """
            Build the main chart using data from the selected episode.
            """
            if selected_episode is None or selected_episode not in self.episodes_dict:
                return go.Figure()

            data_dict = self.episodes_dict[selected_episode]

            # Unpack
            dates = data_dict['dates']
            valuations = data_dict['portfolio_valuations']
            expositions = data_dict['portfolio_expositions']
            prices = data_dict['prices']

            # Convert all data into a DataFrame for easier filtering
            df = pd.DataFrame({
                'date': dates,
                'valuation': valuations,
                'exposition': expositions,
                'price': prices
            })

            # Filter by date range if provided
            if start_date is not None:
                print(start_date, type(start_date))
                start_date = pd.to_datetime(start_date, format = "ISO8601", utc = True)
                df = df[df['date'] >= start_date]

            if end_date is not None:
                print(end_date, type(end_date))
                end_date = pd.to_datetime(end_date, format = "ISO8601", utc = True)
                df = df[df['date'] <= end_date]

            # Sort by date (just in case)
            df = df.sort_values('date')

            fig = go.Figure()

            # 1) Portfolio Valuation
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['valuation'], 
                    mode='lines+markers', 
                    name='Portfolio Valuation'
                )
            )
            # 2) Position Exposition
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['exposition'], 
                    mode='lines+markers', 
                    name='Position Exposition', 
                    yaxis='y2'
                )
            )
            # 3) Price
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['price'], 
                    mode='lines+markers', 
                    name='Price', 
                    yaxis='y3'
                )
            )

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
                    anchor="x", 
                    overlaying="y", 
                    side="right"
                ),
                yaxis3=dict(
                    title="Price",
                    title_font=dict(color="#2ca02c"),
                    tickfont=dict(color="#2ca02c"),
                    anchor="free", 
                    overlaying="y", 
                    side="right", 
                    position=0.90
                ),
                legend=dict(
                    x=0.02,
                    y=0.98,
                    bgcolor="rgba(255,255,255,0.6)"
                ),
                hovermode="x unified",
                title=f"Portfolio / Positions / Price - Episode {selected_episode}"
            )

            return fig

        # 3) Display the details of a clicked point
        @app.callback(
            Output('point-data', 'children'),
            Input('main-chart', 'clickData'),
            State('episode-selector', 'value')
        )
        def display_click_data(clickData, selected_episode):
            """
            Show the record details of the point the user clicked.
            If the user hasn't clicked anything, show a default message.
            """
            if clickData is None or selected_episode not in self.episodes_dict:
                return html.Div(["Click a point in the chart to see details."])

            point = clickData['points'][0]
            clicked_date = point['x']
            clicked_date = pd.to_datetime(clicked_date, utc = True)

            # Safely extract from the environment's stored infos

            # It's possible that the environment's date keys are actual datetime objects
            # or strings. We'll attempt the direct lookup or do a small fallback.
            row_dict = self.episodes_dict[selected_episode]['infos'].get(clicked_date, None)
            if row_dict is None: return html.Div([f"No data for this date: {clicked_date}"])

            # Build a nice HTML table
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
