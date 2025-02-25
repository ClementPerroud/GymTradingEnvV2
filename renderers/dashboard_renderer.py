import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.subplots
import pandas as pd
import numpy as np
import datetime
import math
import copy

# For your environment code:
from .renderer import AbstractRenderer


# --------------------------------------------------------------------------------
# 1) The SHARED DASHBOARD
# --------------------------------------------------------------------------------

class MultiEnvDashboard:
    """
    Stores data for multiple environments, each with multiple episodes,
    and provides a multipage Dash interface:
      - Main Page: summary table
      - Detail Page: chart, date range, etc.
    """

    def __init__(self, app_kwargs=None):
        """
        app_kwargs: dict for the Dash server (e.g. host, port, debug, etc.)
        """
        self.app_kwargs = app_kwargs or {}

        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
            # needed if we do dynamic or multipage:
            suppress_callback_exceptions=True
        )

        # Data dictionary:  data[(env_name, ep_id)] = {
        #    "dates": [...],
        #    "portfolio_valuations": [...],
        #    "portfolio_expositions": [...],
        #    "prices": [...],
        #    "rewards": [...],
        #    "infos": { date: info_dict },
        #    "summary_metrics": {...}  # optional computed after each episode
        # }
        self.data = {}

        # Top-level layout: a dcc.Location + single container for pages
        self.app.layout = dbc.Container(
            fluid=True,
            children=[
                dcc.Location(id="url", refresh=False),
                html.Div(id="page-content")
            ]
        )

        self.register_callbacks()
        # Start Dash
        self.app.run(**self.app_kwargs)

    # ------------------------------------------------------------------
    # (A) Data Ingestion Methods
    # ------------------------------------------------------------------

    def start_new_episode(self, env_name: str, episode_number: int):
        """
        Called by environment-bound renderer in `reset()`.
        Initialize the data structure for (env_name, episode_number).
        """
        key = (env_name, episode_number)
        if key not in self.data:
            self.data[key] = {
                "dates": [],
                "portfolio_valuations": [],
                "portfolio_expositions": [],
                "prices": [],
                "rewards": [],
                "infos": {},
                "summary_metrics": {}
            }

    def store_step(self, env_name: str, episode_number: int, date, infos):
        """
        Called in `render_step()` to append data for (env_name, ep_number).
        """
        key = (env_name, episode_number)
        if key not in self.data:
            self.start_new_episode(env_name, episode_number)

        # Pull out the relevant fields
        asset = infos["assets"][0]
        pair = infos["pairs"][0]

        self.data[key]["dates"].append(date)
        self.data[key]["portfolio_valuations"].append(infos.get("portfolio_valuation", 0.0))
        self.data[key]["portfolio_expositions"].append(infos.get(f"portfolio_exposition_{asset}", 0.0))
        self.data[key]["prices"].append(infos.get(f"price_{pair}", 0.0))
        self.data[key]["rewards"].append(infos.get("reward", 0.0))
        self.data[key]["infos"][date] = infos

    def finalize_episode(self, env_name: str, episode_number: int):
        """
        Called at the end of an episode, to compute summary metrics (annual return, sharpe, etc.).
        """
        key = (env_name, episode_number)
        if key not in self.data:
            return

        entry = self.data[key]
        dates = entry["dates"]
        if len(dates) < 2:
            return

        # Convert to np arrays
        valuations = np.array(entry["portfolio_valuations"], dtype=float)
        prices     = np.array(entry["prices"], dtype=float)
        if valuations[0] <= 0:
            return

        # Basic time
        total_days = (dates[-1] - dates[0]).days or 1

        # 1) Basic annual return = (final / initial)^(365/days) - 1
        initial_v = valuations[0]
        final_v   = valuations[-1]
        ann_return = (final_v / initial_v)**(365 / total_days) - 1

        # 2) Market return
        initial_p = prices[0] if len(prices) else 0
        final_p   = prices[-1] if len(prices) else 0
        if initial_p > 0:
            ann_market_return = (final_p / initial_p)**(365 / total_days) - 1
        else:
            ann_market_return = 0.0

        # 3) Sharpe ratio
        daily_rets = valuations[1:] / valuations[:-1] - 1.0
        sharpe = 0.0
        if len(daily_rets) > 2:
            mean_r = np.mean(daily_rets)
            std_r  = np.std(daily_rets)
            if std_r > 1e-9:
                sharpe = (mean_r / std_r) * math.sqrt(365)

        # 4) Alpha
        alpha = ann_return - ann_market_return

        entry["summary_metrics"] = {
            "annual_return": ann_return,
            "annual_market_return": ann_market_return,
            "sharpe": sharpe,
            "alpha": alpha
        }

    # ------------------------------------------------------------------
    # (B) Page Layouts
    # ------------------------------------------------------------------
    def build_main_page_layout(self):
        """
        Page 1: Summaries of all (env_name, episode_number).
        A table with columns: EnvName, Episode, AnnualReturn, MarketReturn, Sharpe, Alpha, link to detail
        """
        if not self.data:
            return html.Div(
                [
                    html.H3("No episodes yet", className="text-center"),
                    html.Hr(),
                    dbc.Alert("Run some episodes first!", color="info", style={"textAlign": "center"})
                ],
                style={"marginTop": "50px"}
            )

        # Build table rows
        rows = []
        # Sort by env_name, then ep_number
        sorted_keys = sorted(self.data.keys(), key=lambda x: (x[0], x[1]))
        for (env_name, ep_id) in sorted_keys:
            entry = self.data[(env_name, ep_id)]
            sm = entry.get("summary_metrics", {})

            ann_ret   = sm.get("annual_return", float('nan'))
            mkt_ret   = sm.get("annual_market_return", float('nan'))
            sharpe    = sm.get("sharpe", float('nan'))
            alpha     = sm.get("alpha", float('nan'))

            ann_ret_str  = f"{ann_ret*100:.2f}%"   if not math.isnan(ann_ret) else "N/A"
            mkt_ret_str  = f"{mkt_ret*100:.2f}%"   if not math.isnan(mkt_ret) else "N/A"
            sharpe_str   = f"{sharpe:.2f}"         if not math.isnan(sharpe) else "N/A"
            alpha_str    = f"{alpha*100:.2f}%"     if not math.isnan(alpha) else "N/A"

            # Link to detail page: /episode-details?env=ENV_NAME&episode=EP_ID
            detail_link = dcc.Link(
                html.Button("View Details", className="btn btn-primary btn-sm"),
                href=f"/episode-details?env={env_name}&episode={ep_id}"
            )

            row = html.Tr([
                html.Td(str(env_name)),
                html.Td(str(ep_id)),
                html.Td(ann_ret_str),
                html.Td(mkt_ret_str),
                html.Td(sharpe_str),
                html.Td(alpha_str),
                html.Td(detail_link),
            ])
            rows.append(row)

        table = dbc.Table(
            [
                html.Thead(html.Tr([
                    html.Th("Environment"),
                    html.Th("Episode"),
                    html.Th("Annual Return"),
                    html.Th("Market Return"),
                    html.Th("Sharpe"),
                    html.Th("Alpha"),
                    html.Th(""),
                ])),
                html.Tbody(rows)
            ],
            bordered=True,
            hover=True,
            responsive=True,
            striped=True
        )

        layout = dbc.Container(
            fluid=True,
            children=[
                html.H2("All Episodes Summary", className="text-center", style={"marginTop": "20px"}),
                html.Hr(),
                table
            ]
        )
        return layout

    def build_detail_page_layout(self, env_name, ep_id):
        """
        Page 2: The detail chart, date range, metric cards, etc. 
        We parse env_name + ep_id from the query parameters.
        """
        card_style = {
            "marginBottom": "20px",
            "borderRadius": "8px",
            "boxShadow": "0 2px 10px rgba(0,0,0,0.08)"
        }

        # We'll store env/ep in hidden dcc.Store so the chart callback can load the data
        store_data = {"env_name": env_name, "ep_id": ep_id}

        layout = dbc.Container(
            fluid=True,
            children=[
                # Header
                dbc.Row([
                    dbc.Col(
                        html.H1(
                            f"Env {env_name} - Episode {ep_id} - Detail View",
                            className="text-center"
                        ),
                        width=12
                    )
                ], style={"marginTop": "20px"}),

                # Back button
                dbc.Row([
                    dbc.Col(
                        dbc.Button("Back to Main Page", href="/", color="secondary"),
                        width=12
                    )
                ], style={"marginBottom": "20px"}),

                # Date Range
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                style=card_style,
                                body=True,
                                children=[
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                html.Label("Date Range:", style={"fontWeight": "bold"}),
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
                            width=12, lg=6
                        )
                    ],
                    justify="center",
                    style={"marginBottom": "20px"}
                ),

                # Performance metric cards
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.H5("Annual Return", className="card-title"),
                                    html.H2(id="annual-return-card", className="card-text")
                                ]),
                                style=card_style
                            ),
                            width=3, xs=12, sm=6, md=3
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.H5("Market Return", className="card-title"),
                                    html.H2(id="annual-market-return-card", className="card-text")
                                ]),
                                style=card_style
                            ),
                            width=3, xs=12, sm=6, md=3
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.H5("Sharpe Ratio", className="card-title"),
                                    html.H2(id="sharpe-card", className="card-text")
                                ]),
                                style=card_style
                            ),
                            width=3, xs=12, sm=6, md=3
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.H5("Alpha", className="card-title"),
                                    html.H2(id="alpha-card", className="card-text")
                                ]),
                                style=card_style
                            ),
                            width=3, xs=12, sm=6, md=3
                        ),
                    ],
                    justify="center",
                    style={"marginBottom": "20px"}
                ),

                # Main chart
                dbc.Row([
                    dbc.Col(
                        dbc.Card(
                            body=True,
                            children=[
                                dcc.Graph(id="main-chart", figure={}, style={"height": "75vh"})
                            ],
                            style=card_style
                        ),
                        width=12
                    )
                ], justify="center"),

                # Point data
                dbc.Row([
                    dbc.Col(
                        dbc.Card(
                            body=True,
                            children=[
                                html.Div(
                                    "Click a point in the chart to see details.",
                                    id="point-data"
                                )
                            ],
                            style=card_style
                        ),
                        width=12
                    )
                ], style={"marginBottom": "50px"}),

                # Hidden store with (env, ep)
                dcc.Store(id="detail-store", data=store_data)
            ]
        )
        return layout

    # ------------------------------------------------------------------
    # (C) Callbacks
    # ------------------------------------------------------------------
    def register_callbacks(self):

        # 1) Routing: which page layout?
        @self.app.callback(
            Output("page-content", "children"),
            Input("url", "pathname"),
            State("url", "search")
        )
        def display_page(pathname, search):
            """
            - If pathname == "/", show the main summary page.
            - If pathname == "/episode-details", parse ?env=xxx&episode=yyy
              Then show detail page for that environment + episode.
            - Else 404
            """
            if pathname == "/":
                # Main page
                return self.build_main_page_layout()
            elif pathname == "/episode-details":
                # parse "?env=ENV_NAME&episode=EP_ID"
                env_name = None
                ep_id = None
                if search:
                    # e.g. search = "?env=env1&episode=2"
                    query_str = search.lstrip("?")
                    # parse by splitting "&"
                    items = query_str.split("&")
                    kv_dict = {}
                    for it in items:
                        if "=" in it:
                            k, v = it.split("=", 1)
                            kv_dict[k] = v
                    env_name = kv_dict.get("env", None)
                    ep_id_str = kv_dict.get("episode", None)
                    if ep_id_str is not None:
                        try:
                            ep_id = int(ep_id_str)
                        except:
                            ep_id = None

                # Validate
                key = (env_name, ep_id)
                if (env_name is not None) and (ep_id is not None) and (key in self.data):
                    return self.build_detail_page_layout(env_name, ep_id)
                return dbc.Alert(
                    f"Invalid or missing env/episode: {env_name}, {ep_id}",
                    color="danger",
                    style={"marginTop":"50px"}
                )
            else:
                # 404
                return dbc.Alert("404 - Page not found", color="danger", style={"marginTop":"50px"})


        # 2) Build the main chart + metrics
        @self.app.callback(
            [
                Output("main-chart", "figure"),
                Output("annual-return-card", "children"),
                Output("annual-market-return-card", "children"),
                Output("sharpe-card", "children"),
                Output("alpha-card", "children"),
            ],
            [
                Input("date-range", "start_date"),
                Input("date-range", "end_date"),
                Input("detail-store", "data")
            ]
        )
        def update_chart(start_date, end_date, detail_store):
            """
            This is triggered on the detail page. 
            We'll slice the data by date range and compute the metrics on that slice.
            """
            fig = go.Figure()
            ann_ret_str = "N/A"
            mkt_ret_str = "N/A"
            sharpe_str  = "N/A"
            alpha_str   = "N/A"

            if not detail_store:
                return fig, ann_ret_str, mkt_ret_str, sharpe_str, alpha_str

            env_name = detail_store.get("env_name", None)
            ep_id = detail_store.get("ep_id", None)
            if (env_name, ep_id) not in self.data:
                return fig, ann_ret_str, mkt_ret_str, sharpe_str, alpha_str

            entry = self.data[(env_name, ep_id)]
            dates = entry["dates"]
            if not dates:
                return fig, ann_ret_str, mkt_ret_str, sharpe_str, alpha_str

            # Convert
            valuations = np.array(entry["portfolio_valuations"], dtype=float)
            expositions= np.array(entry["portfolio_expositions"], dtype=float)
            prices     = np.array(entry["prices"], dtype=float)
            np_dates   = np.array(dates, dtype="datetime64[ns]")

            # Filter by date range
            index_start = 0
            if start_date:
                s = pd.to_datetime(start_date)
                index_start = np.searchsorted(np_dates, np.datetime64(s))
            index_end = len(dates)
            if end_date:
                e = pd.to_datetime(end_date)
                index_end = np.searchsorted(np_dates, np.datetime64(e))

            if index_end <= index_start:
                return fig, ann_ret_str, mkt_ret_str, sharpe_str, alpha_str

            # Slice
            dates_range = dates[index_start:index_end]
            vals_range  = valuations[index_start:index_end]
            expo_range  = expositions[index_start:index_end]
            prices_range= prices[index_start:index_end]

            if len(vals_range) > 1 and vals_range[0] != 0:
                initial_v = vals_range[0]
                final_v   = vals_range[-1]
                # approximate # of days
                days = (dates_range[-1] - dates_range[0]).days or 1
                ann_ret = (final_v / initial_v)**(365 / days) - 1
                ann_ret_str = f"{ann_ret*100:.2f}%"

                initial_p = prices_range[0]
                final_p   = prices_range[-1]
                if initial_p > 0:
                    ann_mkt = (final_p / initial_p)**(365 / days) - 1
                else:
                    ann_mkt = 0.0
                mkt_ret_str = f"{ann_mkt*100:.2f}%"

                daily_rets = vals_range[1:] / vals_range[:-1] - 1
                if len(daily_rets) > 1:
                    mean_r = np.mean(daily_rets)
                    std_r  = np.std(daily_rets)
                    if std_r > 1e-9:
                        sharpe = (mean_r / std_r)*np.sqrt(365)
                        sharpe_str = f"{sharpe:.2f}"
                    else:
                        sharpe_str = "∞"

                alpha = ann_ret - ann_mkt
                alpha_str = f"{alpha*100:.2f}%"

            # Build the chart
            # fig = plotly.subplots.make_subplots(
            #     rows=2, cols=1,
            #     shared_xaxes=True,
            #     vertical_spacing=0.05,
            #     row_heights=[0.7, 0.3],
            #     specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
            # )
            layout = dict(
                hoversubplots="axis",
                title=dict(text="Stock Price Changes"),
                hovermode="x",
                grid=dict(rows=2, columns=1)
                )
            data = []

            if len(dates_range) > 0:
                # Scale portfolio to match price shape
                scale_factor = 1.0
                if vals_range[0] != 0:
                    scale_factor = prices_range[0] / vals_range[0]

                # Plot scaled portfolio
                data.append(
                    go.Scattergl(
                        x=dates_range,
                        y=vals_range * scale_factor,
                        yaxis= "y",
                        customdata=vals_range,
                        hovertemplate="Portfolio: %{customdata:.2f}<extra></extra>",
                        mode="lines",
                        name="Portfolio (scaled)",
                        line=dict(color="#1f77b4", width=2),
                        
                    )#, row=1, col=1
                )
                # Plot price
                data.append(
                    go.Scattergl(
                        x=dates_range,
                        y=prices_range,
                        yaxis = "y",
                        mode="lines",
                        name="Price",
                        line=dict(color="#2ca02c", width=2),
                    )#, row=1, col=1
                )
                # Plot position exposition
                data.append(
                    go.Scattergl(
                        x=dates_range,
                        y=expo_range,
                        yaxis = "y2",
                        mode="lines",
                        name="Exposition",
                        line=dict(color="#ff7f0e", width=2),
                    )#, row=2, col=1
                )
            fig = go.Figure(data=data, layout=layout)

            fig.update_layout(
                yaxis1=dict(title="<b>Valuation & Price (log scale)</b>", type="log", domain=[0.2, 1]),
                yaxis2=dict(title="Portfolio Exposition", domain = [0, 0.2]),
                legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.6)"),
                hovermode="x unified",
                hoversubplots="axis",
                plot_bgcolor="white",
                paper_bgcolor="white"
            )

            return fig, ann_ret_str, mkt_ret_str, sharpe_str, alpha_str

        # 3) Display the point data table
        @self.app.callback(
            Output("point-data", "children"),
            Input("main-chart", "clickData"),
            State("detail-store", "data")
        )
        def display_click_data(clickData, detail_store):
            if not clickData:
                return "Click a point in the chart to see details."
            if not detail_store:
                return "No detail_store data."

            env_name = detail_store.get("env_name", None)
            ep_id = detail_store.get("ep_id", None)
            key = (env_name, ep_id)
            if key not in self.data:
                return "No data found."

            point = clickData["points"][0]
            x_val = point["x"]
            clicked_date = pd.to_datetime(x_val).to_pydatetime()
            row_dict = self.data[key]["infos"].get(clicked_date, None)

            if not row_dict:
                return f"No data for {clicked_date}"

            rows = []
            for k, v in row_dict.items():
                rows.append(html.Tr([html.Td(str(k)), html.Td(str(v))]))

            table = dbc.Table(
                [html.Thead(html.Tr([html.Th("Key"), html.Th("Value")]))] +
                [html.Tbody(rows)],
                bordered=True,
                hover=True,
                striped=True,
                responsive=True,
            )
            return html.Div([
                html.H5(f"Details for {clicked_date.strftime('%Y-%m-%d %H:%M:%S')}"),
                table
            ])


# --------------------------------------------------------------------------------
# 2) The PER-ENV RENDERER
# --------------------------------------------------------------------------------

class DashboardRenderer(AbstractRenderer):
    """
    Renderer attached to a single environment. 
    Delegates all data to MultiEnvDashboard for storage and display.
    """

    def __init__(self, dashboard_manager: MultiEnvDashboard, **kwargs):
        super().__init__(**kwargs)
        self.dashboard_manager = dashboard_manager
        self.env_name = None
        self.episode_id = 0

    async def reset(self, seed=None, **kwargs):
        await super().reset(seed=seed, **kwargs)

        env = self.get_trading_env()
        self.env_name = getattr(env, "name", "default_env")
        self.episode_id += 1

        # Start a new entry in the manager
        self.dashboard_manager.start_new_episode(self.env_name, self.episode_id)

        self.infos_manager = env.infos_manager
        self.time_manager  = env.time_manager

    async def render_step(self, action, obs, reward, terminated, truncated, infos):
        await super().render_step(action, obs, reward, terminated, truncated, infos)

        # current datetime from time_manager
        date_tz = await self.time_manager.get_current_datetime()
        date = date_tz.replace(tzinfo=None)

        # Optionally store extra fields
        new_infos = copy.copy(infos)
        new_infos["env_name"] = self.env_name
        new_infos["action"] = action
        new_infos["reward"] = reward
        new_infos["terminated"] = terminated
        new_infos["truncated"] = truncated
        new_infos["obs"] = obs

        # Store in the manager
        self.dashboard_manager.store_step(
            self.env_name, 
            self.episode_id, 
            date, 
            new_infos
        )

    async def render_episode(self):
        """
        Called at the end of an episode. We'll finalize metrics for this environment + episode.
        """
        self.dashboard_manager.finalize_episode(self.env_name, self.episode_id)

