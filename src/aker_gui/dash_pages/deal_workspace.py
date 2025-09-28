"""Deal Workspace dashboard page for analysts to configure deal scopes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, callback, dcc, html
from dash import dash_table
from fastapi import HTTPException
from urllib.parse import parse_qs

from aker_core.logging import get_logger

from ..api import deals as deals_api
from ..api.deals import RankRequest, ScenarioPayload
from ..api.deals import ScopeOverride
from ..api import state_packs as state_pack_api

LOGGER = get_logger(__name__)
PAYBACK_THRESHOLD = 36


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------


def _summary_card(asset: Dict[str, Any], compute_time_ms: Optional[int]) -> dbc.Card:
    badge = None
    if asset.get("is_admin") and compute_time_ms is not None:
        badge = dbc.Badge(
            f"debug: rank {compute_time_ms} ms",
            color="info",
            className="ms-2",
        )

    return dbc.Card(
        dbc.CardBody(
            [
                html.H4([
                    html.Span(asset.get("name", "")),
                    html.Small(
                        f" ({asset.get('asset_id', '')})",
                        className="text-muted ms-2",
                    ),
                    badge if badge else "",
                ], className="d-flex align-items-center"),
                dbc.Row(
                    [
                        dbc.Col(html.Div([html.Small("MSA"), html.H5(asset.get("msa_name", ""))]), md=2),
                        dbc.Col(html.Div([html.Small("Units"), html.H5(asset.get("units", ""))]), md=2),
                        dbc.Col(
                            html.Div([
                                html.Small("Vintage"),
                                html.H5(asset.get("year_built", "")),
                            ]),
                            md=2,
                        ),
                        dbc.Col(
                            html.Div([
                                html.Small("Product Type"),
                                html.H5(asset.get("product_type", ""))
                            ]),
                            md=3,
                        ),
                        dbc.Col(
                            html.Div([
                                html.Small("Market Score"),
                                html.H5(f"{asset.get('market_score', 0):.1f}")
                            ]),
                            md=3,
                        ),
                    ],
                    className="g-3",
                ),
            ]
        ),
        className="mb-3",
    )


def create_layout() -> html.Div:
    """Create the Deal Workspace page layout."""
    return html.Div(
        [
            dcc.Location(id="deal-workspace-location"),
            dcc.Store(id="deal-workspace-init-data"),
            dcc.Store(id="deal-workspace-state"),
            dcc.Store(id="deal-workspace-results"),
            dcc.Store(id="deal-workspace-scenarios"),
            dcc.Interval(id="deal-workspace-save-timer", interval=1500, n_intervals=0, disabled=True, max_intervals=1),
            html.Div(id="deal-workspace-error-banner"),
            html.Nav(
                [
                    dbc.Breadcrumb(
                        items=[
                            {"label": "Deals", "href": "/app/deal"},
                            {"label": "Workspace", "active": True},
                        ],
                        className="mb-2",
                    )
                ]
            ),
            html.Div(id="deal-workspace-summary"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Scope Selection"),
                            html.P("Choose scopes and adjust overrides to reflect the proposed stack."),
                            dcc.Loading(
                                html.Div(
                                    [
                                        dcc.Checklist(
                                            id="deal-scope-selector",
                                            options=[],
                                            value=[],
                                            labelStyle={"display": "block"},
                                        ),
                                        dash_table.DataTable(
                                            id="deal-scope-overrides",
                                            columns=[
                                                {"name": "Scope", "id": "scope_name", "editable": False},
                                                {"name": "Cost / Door", "id": "cost_per_door", "type": "numeric", "editable": True},
                                                {"name": "Expected Lift ($/mo)", "id": "expected_lift", "type": "numeric", "editable": True},
                                                {"name": "Downtime (wk)", "id": "downtime_wk", "type": "numeric", "editable": True},
                                            ],
                                            data=[],
                                            editable=True,
                                            row_deletable=False,
                                            style_cell={"padding": "0.5rem"},
                                            style_table={"marginTop": "1rem"},
                                        ),
                                        dbc.ButtonGroup(
                                            [
                                                dbc.Button("Reset overrides", id="deal-reset-overrides-btn", color="secondary"),
                                                dbc.Button("Apply state pack adders", id="deal-apply-state-pack-btn", color="info"),
                                            ],
                                            className="mt-2",
                                        ),
                                    ]
                                )
                            ),
                            html.Hr(),
                            html.Div(
                                [
                                    html.H6("Scenario"),
                                    dbc.Input(id="deal-workspace-scenario-name", placeholder="Scenario name"),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button("Save", id="deal-save-btn", color="success"),
                                            dbc.Button("Save As", id="deal-save-as-btn", color="primary"),
                                        ],
                                        className="mt-2",
                                    ),
                                    html.Div(id="deal-scenario-list", className="mt-3"),
                                ]
                            ),
                        ],
                        md=5,
                        className="pe-md-4",
                    ),
                    dbc.Col(
                        [
                            html.H5("Results"),
                            dash_table.DataTable(
                                id="deal-roi-ladder-table",
                                columns=[
                                    {"name": "Rank", "id": "roi_rank"},
                                    {"name": "Scope", "id": "scope_name"},
                                    {"name": "NPV", "id": "npv", "type": "numeric", "format": dash_table.Format(nully="")},
                                    {"name": "IRR %", "id": "irr", "type": "numeric", "format": dash_table.Format(precision=1)},
                                    {"name": "Payback (mo)", "id": "payback_mo", "type": "numeric", "format": dash_table.Format(precision=1)},
                                    {"name": "Notes", "id": "notes"},
                                ],
                                data=[],
                                style_cell={"padding": "0.4rem", "whiteSpace": "normal"},
                                style_header={"fontWeight": "bold"},
                                row_selectable="single",
                                sort_action="native",
                                selected_rows=[],
                            ),
                            html.Div(id="deal-warning-messages", className="text-warning mt-2"),
                            dcc.Graph(id="deal-downtime-chart", className="mt-3"),
                            dbc.Row(
                                [
                                    dbc.Col(_metric_card("Capex", "$0", "deal-total-capex"), md=3),
                                    dbc.Col(_metric_card("Expected Lift", "$0/mo", "deal-total-lift"), md=3),
                                    dbc.Col(_metric_card("Retention", "0 bps", "deal-total-retention"), md=3),
                                    dbc.Col(_metric_card("Payback", "0 mo", "deal-total-payback"), md=3),
                                ],
                                className="mt-3",
                            ),
                        ],
                        md=7,
                    ),
                ],
                className="g-4",
            ),
        ]
    )


def _metric_card(title: str, value: str, element_id: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.Small(title, className="text-muted"),
                html.H4(value, id=element_id),
            ]
        )
    )


# ---------------------------------------------------------------------------
# Callback registration helper
# ---------------------------------------------------------------------------


def register_callbacks(app: Dash) -> None:
    """Register callbacks for the deal workspace page."""

    @app.callback(
        [
            Output("deal-workspace-init-data", "data"),
            Output("deal-workspace-state", "data"),
            Output("deal-workspace-results", "data"),
            Output("deal-workspace-scenarios", "data"),
            Output("deal-scope-selector", "options"),
            Output("deal-scope-selector", "value"),
            Output("deal-scope-overrides", "data"),
            Output("deal-workspace-summary", "children"),
            Output("deal-workspace-error-banner", "children"),
        ],
        Input("deal-workspace-location", "search"),
    )
    def initialize_workspace(search: str):
        params = dash.ctx.inputs.get("deal-workspace-location.search") or search
        parsed = parse_qs((params or "").lstrip("?"))
        asset_id = parsed.get("asset_id", ["AKR-123"])[0]
        as_of = parsed.get("as_of", [None])[0]

        try:
            asset = deals_api.get_asset_details(asset_id)
        except HTTPException as exc:  # type: ignore[name-defined]
            return [dash.no_update] * 8 + [
                dbc.Alert(f"Unable to load asset: {exc.detail}", color="danger")
            ]

        scope_catalog = deals_api.get_scope_catalog_cached()
        options = _build_scope_options(scope_catalog, highlighted=None)
        selected = [scope["scope_id"] for scope in scope_catalog if scope.get("default_on")]
        overrides = {
            scope["scope_id"]: {
                "scope_id": scope["scope_id"],
                "scope_name": scope["name"],
                "cost_per_door": scope["cost_per_door"],
                "expected_lift": scope["expected_lift"],
                "downtime_wk": scope["downtime_wk"],
            }
            for scope in scope_catalog
        }

        rank_request = RankRequest(asset_id=asset_id, selected_scopes=selected, overrides={})
        rank_response = deals_api.rank_deal(rank_request)
        summary = _summary_card(asset, rank_response.compute_time_ms)

        state = {
            "asset_id": asset_id,
            "msa_id": asset.get("msa_id"),
            "as_of": as_of,
            "selected_scopes": selected,
            "overrides": {sid: ScopeOverride().dict(exclude_none=True) for sid in overrides},
            "highlighted_scope": None,
            "scenario_id": None,
            "pending_autosave": False,
        }

        scenarios = [item.dict() for item in deals_api.list_recent_scenarios(asset_id)]

        overrides_table = [overrides[sid] for sid in selected]

        init_data = {
            "asset": asset,
            "scope_catalog": scope_catalog,
            "is_admin": asset.get("is_admin", False),
            "vacancy_cap": 0.08,
        }

        results = rank_response.dict()

        return (
            init_data,
            state,
            results,
            scenarios,
            options,
            selected,
            overrides_table,
            summary,
            None,
        )

    @app.callback(
        [
            Output("deal-workspace-state", "data"),
            Output("deal-workspace-results", "data"),
            Output("deal-scope-overrides", "data"),
            Output("deal-workspace-error-banner", "children"),
            Output("deal-workspace-save-timer", "disabled"),
        ],
        [
            Input("deal-scope-selector", "value"),
            Input("deal-scope-overrides", "data"),
            Input("deal-reset-overrides-btn", "n_clicks"),
            Input("deal-apply-state-pack-btn", "n_clicks"),
        ],
        [
            State("deal-workspace-state", "data"),
            State("deal-workspace-init-data", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_selection(
        selected_scopes,
        overrides_table,
        reset_clicks,
        apply_clicks,
        state,
        init_data,
    ):
        if not state or not init_data:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True

        trigger = dash.ctx.triggered_id
        catalog_map = {scope["scope_id"]: scope for scope in init_data.get("scope_catalog", [])}
        overrides = {row["scope_id"]: row for row in overrides_table} if overrides_table else {}
        error = None

        if trigger == "deal-reset-overrides-btn":
            overrides = {
                sid: {
                    "scope_id": sid,
                    "scope_name": catalog_map[sid]["name"],
                    "cost_per_door": catalog_map[sid]["cost_per_door"],
                    "expected_lift": catalog_map[sid]["expected_lift"],
                    "downtime_wk": catalog_map[sid]["downtime_wk"],
                }
                for sid in selected_scopes
                if sid in catalog_map
            }
        elif trigger == "deal-apply-state-pack-btn":
            state_id = state.get("msa_id", "")[:2] or "CO"
            adjustments = state_pack_api.STATE_PACK_ADJUSTMENTS.get(state_id.upper(), {})
            for scope_id in selected_scopes:
                if scope_id not in catalog_map:
                    continue
                base = catalog_map[scope_id]
                factor = adjustments.get(scope_id, 0.0)
                overrides.setdefault(
                    scope_id,
                    {
                        "scope_id": scope_id,
                        "scope_name": base["name"],
                        "cost_per_door": base["cost_per_door"],
                        "expected_lift": base["expected_lift"],
                        "downtime_wk": base["downtime_wk"],
                    },
                )
                overrides[scope_id]["cost_per_door"] = round(
                    overrides[scope_id]["cost_per_door"] * (1 + factor), 2
                )
        else:
            # keep overrides as edited but ensure structure
            fixed = {}
            for sid in selected_scopes:
                data = overrides.get(sid) or {}
                base = catalog_map.get(sid)
                if not base:
                    continue
                fixed[sid] = {
                    "scope_id": sid,
                    "scope_name": base["name"],
                    "cost_per_door": data.get("cost_per_door", base["cost_per_door"]),
                    "expected_lift": data.get("expected_lift", base["expected_lift"]),
                    "downtime_wk": data.get("downtime_wk", base["downtime_wk"]),
                }
            overrides = fixed

        # Validate overrides
        for row in overrides.values():
            if any(value < 0 for key, value in row.items() if key in {"cost_per_door", "expected_lift", "downtime_wk"}):
                error = dbc.Alert(
                    "Overrides cannot be negative. Please correct the values before ranking.",
                    color="danger",
                    duration=4000,
                )
                return state, dash.no_update, list(overrides.values()), error, True

        state["selected_scopes"] = selected_scopes
        state["overrides"] = {
            sid: ScopeOverride(
                cost_per_door=row.get("cost_per_door"),
                expected_lift=row.get("expected_lift"),
                downtime_wk=row.get("downtime_wk"),
            ).dict(exclude_none=True)
            for sid, row in overrides.items()
        }
        state["pending_autosave"] = True

        rank_request = RankRequest(
            asset_id=state["asset_id"],
            selected_scopes=selected_scopes,
            overrides={sid: ScopeOverride(**ov) for sid, ov in state["overrides"].items()},
        )
        results = deals_api.rank_deal(rank_request).dict()

        LOGGER.info(
            "deal_workspace_rank",
            asset_id=state["asset_id"],
            scopes=len(selected_scopes),
            overrides=len(state["overrides"]),
        )

        return state, results, list(overrides.values()), error, False

    @app.callback(
        Output("deal-workspace-save-timer", "disabled"),
        Output("deal-workspace-scenarios", "data"),
        Output("deal-workspace-state", "data"),
        Input("deal-workspace-save-timer", "n_intervals"),
        State("deal-workspace-state", "data"),
        State("deal-workspace-results", "data"),
        State("deal-workspace-scenarios", "data"),
        prevent_initial_call=True,
    )
    def autosave_scenario(_, state, results, scenarios):
        if not state or not state.get("pending_autosave"):
            return True, dash.no_update, state
        if not state.get("scenario_id"):
            state["pending_autosave"] = False
            return True, dash.no_update, state

        payload = ScenarioPayload(
            asset_id=state["asset_id"],
            scenario_name=None,
            selected_scopes=state["selected_scopes"],
            overrides={sid: ScopeOverride(**ov) for sid, ov in state["overrides"].items()},
            scenario_id=state["scenario_id"],
        )
        response = deals_api.save_deal_scenario(payload)
        state["pending_autosave"] = False
        state["last_saved_at"] = response.saved_at.isoformat()
        updated = [item.dict() for item in deals_api.list_recent_scenarios(state["asset_id"])]
        return True, updated, state

    @app.callback(
        Output("deal-workspace-scenarios", "data"),
        Output("deal-workspace-state", "data"),
        Output("deal-workspace-error-banner", "children"),
        [Input("deal-save-btn", "n_clicks"), Input("deal-save-as-btn", "n_clicks")],
        [
            State("deal-workspace-state", "data"),
            State("deal-workspace-results", "data"),
            State("deal-workspace-scenario-name", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_scenario(save_clicks, save_as_clicks, state, results, name):
        trigger = dash.ctx.triggered_id
        if not state:
            return dash.no_update, dash.no_update, None

        scenario_name = name or "Untitled Scenario"
        scenario_id = state.get("scenario_id") if trigger == "deal-save-btn" else None
        payload = ScenarioPayload(
            asset_id=state["asset_id"],
            scenario_name=scenario_name,
            selected_scopes=state.get("selected_scopes", []),
            overrides={sid: ScopeOverride(**ov) for sid, ov in state.get("overrides", {}).items()},
            scenario_id=scenario_id,
        )
        response = deals_api.save_deal_scenario(payload)
        state["scenario_id"] = response.scenario_id
        state["pending_autosave"] = False
        state["last_saved_at"] = response.saved_at.isoformat()

        scenarios = [item.dict() for item in deals_api.list_recent_scenarios(state["asset_id"])]
        message = dbc.Alert("Scenario saved", color="success", duration=2000)
        LOGGER.info("deal_workspace_save", asset_id=state["asset_id"], scenario_id=response.scenario_id)
        return scenarios, state, message

    @app.callback(
        [
            Output("deal-scope-selector", "options"),
            Output("deal-roi-ladder-table", "data"),
            Output("deal-roi-ladder-table", "selected_rows"),
            Output("deal-downtime-chart", "figure"),
            Output("deal-total-capex", "children"),
            Output("deal-total-lift", "children"),
            Output("deal-total-retention", "children"),
            Output("deal-total-payback", "children"),
            Output("deal-warning-messages", "children"),
        ],
        Input("deal-workspace-results", "data"),
        State("deal-workspace-state", "data"),
        State("deal-workspace-init-data", "data"),
    )
    def refresh_results(results, state, init_data):
        if not results or not state:
            empty_fig = go.Figure()
            empty_fig.update_layout(template="plotly_white")
            return dash.no_update, [], [], empty_fig, "$0", "$0/mo", "0 bps", "0 mo", None

        catalog = init_data.get("scope_catalog", []) if init_data else []
        highlighted = state.get("highlighted_scope")
        options = _build_scope_options(catalog, highlighted)

        ladder = results.get("ladder", [])
        data = [entry for entry in ladder]
        figure = _downtime_figure(results.get("downtime_schedule", []))
        totals = results.get("totals", {})
        warnings = results.get("warnings", [])
        warning_component = [html.Div(warning) for warning in warnings] if warnings else None

        return (
            options,
            data,
            [],
            figure,
            _currency(totals.get("total_cost", 0)),
            _currency(totals.get("total_lift", 0)) + "/mo",
            f"{totals.get('total_retention_bps', 0):.0f} bps",
            f"{totals.get('avg_payback_mo', 0):.1f} mo",
            warning_component,
        )

    @app.callback(
        Output("deal-workspace-state", "data"),
        Input("deal-roi-ladder-table", "selected_rows"),
        State("deal-roi-ladder-table", "data"),
        State("deal-workspace-state", "data"),
        prevent_initial_call=True,
    )
    def select_ladder_row(selected_rows, data, state):
        if not state or not data or not selected_rows:
            return state
        try:
            scope_id = data[selected_rows[0]]["scope_id"]
        except (IndexError, KeyError):
            return state
        state["highlighted_scope"] = scope_id
        return state

    @app.callback(
        Output("deal-scenario-list", "children"),
        Input("deal-workspace-scenarios", "data"),
        State("deal-workspace-state", "data"),
    )
    def render_scenario_list(scenarios, state):
        if not scenarios:
            return html.Small("No saved scenarios yet.", className="text-muted")

        items = []
        for scenario in scenarios:
            active = state and scenario["scenario_id"] == state.get("scenario_id")
            items.append(
                dbc.ListGroupItem(
                    [
                        html.Strong(scenario["scenario_name"]),
                        html.Br(),
                        html.Small(
                            datetime.fromisoformat(str(scenario["saved_at"])).strftime("%Y-%m-%d %H:%M:%S"),
                            className="text-muted",
                        ),
                    ],
                    active=active,
                )
            )
        return dbc.ListGroup(items)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def _build_scope_options(catalog: List[Dict[str, Any]], highlighted: Optional[str]) -> List[Dict[str, Any]]:
    options = []
    for scope in catalog:
        style = {"display": "block", "padding": "0.25rem 0"}
        if highlighted and scope["scope_id"] == highlighted:
            style.update({"fontWeight": "bold", "color": "#0d6efd"})
        label = html.Span(
            [
                html.Span(scope["name"], className="me-2"),
                html.Small(f"{scope['category'].title()} • ${scope['cost_per_door']:,}"),
            ]
        )
        options.append({"label": label, "value": scope["scope_id"], "labelStyle": style})
    return options


def _downtime_figure(schedule: List[Dict[str, Any]]) -> go.Figure:
    fig = go.Figure()
    if schedule:
        weeks = [point["week"] for point in schedule]
        units = [point["units_offline"] for point in schedule]
        vacancy_line = [point.get("vacancy_cap", 0) for point in schedule]

        fig.add_trace(
            go.Scatter(x=weeks, y=units, mode="lines+markers", name="Units offline")
        )
        fig.add_trace(
            go.Scatter(x=weeks, y=vacancy_line, mode="lines", name="Vacancy cap", line=dict(dash="dash"))
        )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=30, r=20, t=20, b=30),
        xaxis_title="Week",
        yaxis_title="Units offline",
    )
    return fig


def _currency(value: float) -> str:
    return f"${value:,.0f}"
