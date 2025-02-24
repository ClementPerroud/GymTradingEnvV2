import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly
import pandas as pd
import datetime
import numpy as np

import dash_bootstrap_components as dbc
import plotly.subplots

from .renderer import AbstractRenderer

class DashboardRenderer(AbstractRenderer):
    def __init__(
            self, 
            app_kwargs: dict = dict(
                host="0.0.0.0", 
                jupyter_mode="external", 
                debug=True, 
                port=8050, 
                enable_host_checking=False
            )
        ) -> None:
        super().__init__()

        # Store episode data in a dictionary keyed by episode_index
        # Each entry will have lists of 'dates', 'portfolio_expositions', etc.
        self.episodes_dict = {}
        self.current_episode = 0  # Will increment each time `reset` is called

        # Use a nice, minimal bootstrap theme
        self.app = dash.Dash(
            __name__, 
            external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]  # choose your favorite bootstrap theme
        )

        # ---------- Styles ----------
        # A few helper style dictionaries for easy re-use
        header_style = {
            "textAlign": "center", 
            "margin": "20px 0", 
            "color": "#333", 
            "fontWeight": "bold"
        }

        card_style = {
            "marginBottom": "20px",
            "borderRadius": "8px",
            "boxShadow": "0 2px 10px rgba(0,0,0,0.08)"
        }

        # ---------- Layout ----------
        self.app.layout = dbc.Container(
            fluid=True,
            children=[
                # ----- Header -----
                dbc.Row(
                    justify="center",
                    children=[
                        dbc.Col(
                            html.H1("Trading/Portfolio Dashboard", style=header_style),
                            width=12
                        )
                    ],
                ),

                # ----- Controls / Selections -----
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                style=card_style,
                                body=True,
                                children=[
                                    # Refresh + Episode Selector
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Button(
                                                    "Refresh",
                                                    id="refresh-button",
                                                    n_clicks=0,
                                                    color="primary",
                                                    style={"width": "100%"}
                                                ),
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id="episode-selector",
                                                    placeholder="Select Episode",
                                                    style={"width": "100%"}
                                                ),
                                                width=10
                                            ),
                                        ],
                                        align="center"
                                    ),
                                    html.Hr(),
                                    # Date Range
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                html.Label("Select Date Range:", 
                                                    style={"fontWeight": "bold"}
                                                ),
                                                width="auto",
                                                style={"marginRight": "10px"}
                                            ),
                                            dbc.Col(
                                                dcc.DatePickerRange(
                                                    id="date-range",
                                                    display_format="DD/MM/YYYY",
                                                    start_date=datetime.datetime(2020, 1, 1),
                                                    end_date=datetime.datetime(2025, 12, 31),
                                                    style={"width": "100%"}
                                                ),
                                                width=8
                                            )
                                        ],
                                        align="center"
                                    )
                                ]
                            ),
                            width=12,
                            lg=6
                        )
                    ],
                    justify="center",
                    style={"marginBottom": "20px"}
                ),
                # ----- Main Charts -----
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                style=card_style,
                                body=True,
                                children=[
                                    dcc.Graph(
                                        id="main-chart",
                                        figure={},
                                        style={"height": "75vh"}
                                    ),
                                ]
                            ),
                            width=12
                        )
                    ],
                    justify="center"
                ),
                # ----- Point Data Table -----
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                style=card_style,
                                body=True,
                                children=[
                                    html.Div(
                                        id="point-data",
                                        children=["Click a point in the chart to see details."],
                                        style={"margin": "0 auto"}
                                    )
                                ]
                            ),
                            width=12
                        )
                    ],
                    justify="center",
                    style={"marginBottom": "50px"}
                )
            ]
        )

        # Register callbacks
        self.callbacks(self.app)

        # Run the server
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
            "dates": [],
            "portfolio_expositions": [],
            "portfolio_valuations": [],
            "prices": [],
            "rewards": [],
            "infos": {}
        }

    async def render_step(self, *args, **kwargs):
        """
        Called at each step of the simulation.
        We store each step's data in self.episodes_dict[current_episode].
        """
        date_tz = await self.time_manager.get_current_datetime()
        infos = self.infos_manager.historical_infos[date_tz]
        date = date_tz.replace(tzinfo=None)

        asset = infos["assets"][0]
        pair = infos["pairs"][0]

        self.episodes_dict[self.current_episode]["dates"].append(date)
        self.episodes_dict[self.current_episode]["portfolio_expositions"].append(
            infos[f"portfolio_exposition_{asset}"]
        )
        self.episodes_dict[self.current_episode]["portfolio_valuations"].append(
            infos["portfolio_valuation"]
        )
        self.episodes_dict[self.current_episode]["prices"].append(
            infos[f"price_{pair}"]
        )
        self.episodes_dict[self.current_episode]["rewards"].append(infos["reward"])

        self.episodes_dict[self.current_episode]["infos"][date] = infos

    def callbacks(self, app):
        # 1) Update the Episode Selector Dropdown Options
        @app.callback(
            Output("episode-selector", "options"),
            Output("episode-selector", "value"),
            Input("refresh-button", "n_clicks"),
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

            options = [
                {"label": f"Episode {ep}", "value": ep}
                for ep in sorted(self.episodes_dict.keys())
            ]
            newest_episode = max(self.episodes_dict.keys())
            return options, newest_episode

        # 2) Update the Main Chart whenever 'Refresh' or selected Episode changes
        @app.callback(
            Output("main-chart", "figure"),
            # Output("exposition-chart", "figure"),
            Input("refresh-button", "n_clicks"),
            Input("episode-selector", "value"),
            Input("date-range", "start_date"),
            Input("date-range", "end_date")
        )
        def update_graph(_, selected_episode, start_date, end_date):
            """
            Build the main charts using data from the selected episode.
            """
            if selected_episode is None or selected_episode not in self.episodes_dict:
                return go.Figure()

            data_dict = self.episodes_dict[selected_episode]

            # Unpack
            dates = data_dict["dates"]
            valuations = np.array(data_dict["portfolio_valuations"])
            expositions = np.array(data_dict["portfolio_expositions"])
            prices = np.array(data_dict["prices"])

            # Filter by date range if provided
            index_start = 0
            np_dates = np.array(dates, dtype="datetime64[ns]")
            if start_date is not None:
                start_date = pd.to_datetime(start_date, format="ISO8601")
                index_start = np.searchsorted(np_dates, np.datetime64(start_date))

            index_end = len(dates)
            if end_date is not None:
                end_date = pd.to_datetime(end_date, format="ISO8601")
                index_end = np.searchsorted(np_dates, np.datetime64(end_date))

            # Create the first figure for Portfolio Valuation and Price
            fig = plotly.subplots.make_subplots(
                rows=2, cols=1,
                shared_xaxes=True, 
                vertical_spacing=0.05, row_heights=[0.7, 0.3],
                specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
            )

            # Add Valuation
            fig.add_trace(
                go.Scattergl(
                    x=dates[index_start:index_end],
                    y= valuations[index_start:index_end] * (prices[index_start] / valuations[index_start]),
                    customdata= valuations[index_start:index_end],
                    hovertemplate="Portfolio: %{customdata}<extra></extra>",
                    mode="lines",
                    name="Portfolio Valuation",
                    line=dict(color="#1f77b4", width=2)
                ), row = 1, col = 1
            )


            fig.update_layout(
                yaxis1=dict(
                    title="<b>Portfolio Valuation</b> vs <b>Price</b>",
                    title_font=dict(color="#1f77b4"),
                    tickfont=dict(color="#1f77b4"),
                    type="log",
                )
            )

            # Add Price
            fig.add_trace(
                go.Scattergl(
                    x=dates[index_start:index_end],
                    y=prices[index_start:index_end],
                    mode="lines",
                    name="Price",
                    line=dict(color="#2ca02c", width=2),
                ), row = 1, col = 1
            )


            # fig.update_layout(
            #     yaxis2=dict(
            #         title="Price evolution",
            #         title_font=dict(color="#1f77b4"),
            #         tickfont=dict(color="#1f77b4"),
            #         type="log",
            #         range = (range_min_price, range_max_price),
            #     )
            # )

            

            # Add Position Exposition
            fig.add_trace(
                go.Scattergl(
                    x=dates[index_start:index_end],
                    y=expositions[index_start:index_end],
                    mode="lines",
                    name="Position Exposition",
                    line=dict(color="#ff7f0e", width=2)
                ), row = 2, col = 1
            )

            # fig.update_yaxes(type="linear", row=2, col=1)
            fig.update_layout(
                yaxis2= dict(
                    title = "Portfolio Exposition",
                ),
                legend=dict(
                    x=0.02,
                    y=0.98,
                    bgcolor="rgba(255,255,255,0.6)"
                ),
                hovermode="x unified",
                plot_bgcolor='white',  # Set the plot background color to white
                paper_bgcolor='white'  # Set the paper (overall figure) background color to white

            )

            return fig

        # 3) Display the details of a clicked point
        @app.callback(
            Output("point-data", "children"),
            Input("main-chart", "clickData"),
            State("episode-selector", "value")
        )
        def display_click_data(clickData, selected_episode):
            """
            Show the record details of the point the user clicked.
            If the user hasn't clicked anything, show a default message.
            """
            if clickData is None or selected_episode not in self.episodes_dict:
                return html.Div(["Click a point in the chart to see details."])

            point = clickData["points"][0]
            clicked_date = point["x"]
            clicked_date = pd.to_datetime(clicked_date).to_pydatetime()

            row_dict = self.episodes_dict[selected_episode]["infos"].get(clicked_date, None)
            if row_dict is None:
                return html.Div([f"No data for this date: {clicked_date}"])

            # Build a nice HTML table
            info_items = []
            for k, v in row_dict.items():
                info_items.append(html.Tr([html.Td(str(k)), html.Td(str(v))]))

            table = dbc.Table(
                # Table headings
                [html.Thead(html.Tr([html.Th("Key"), html.Th("Value")]))] +
                [html.Tbody(info_items)],
                bordered=True,
                hover=True,
                striped=True,
                responsive=True,
            )

            return html.Div([
                html.H5(f"Details for Date: {clicked_date.strftime('%Y-%m-%d %H:%M:%S')}"),
                table
            ])
