"""Asset Fit Wizard page implementation."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, State, callback, ctx, dcc, html, no_update
from dash import dash_table

from aker_gui.data.assets import get_default_form_inputs, get_guardrails, get_product_default
from aker_gui.services.asset_fit import evaluate_fit, save_fit_report

STEP_ORDER = [
    {"key": "product", "label": "Product"},
    {"key": "units", "label": "Units"},
    {"key": "physical", "label": "Physical"},
    {"key": "parking", "label": "Parking/Transit"},
    {"key": "amenities", "label": "Amenities"},
    {"key": "summary", "label": "Summary"},
]


def create_layout() -> html.Div:
    return html.Div(
        [
            dcc.Location(id="asset-fit-location", refresh=False),
            dcc.Store(id="asset-fit-query-store"),
            dcc.Store(id="asset-fit-defaults-store"),
            dcc.Store(id="asset-fit-guardrails-store"),
            dcc.Store(id="asset-fit-form-store"),
            dcc.Store(id="asset-fit-status-store", data={"dirty": False, "last_saved": None}),
            dcc.Store(id="asset-fit-highlight-store"),
            dcc.Store(id="asset-fit-local-store", storage_type="local"),
            dbc.Container(
                [
                    dbc.Breadcrumb(
                        items=[
                            {"label": "Assets", "href": "/app/portfolio"},
                            {"label": "Fit Wizard", "active": True},
                        ]
                    ),
                    html.Div(
                        [
                            html.H2("Asset Fit Wizard", className="mb-1"),
                            html.Small(
                                id="asset-fit-subtitle",
                                className="text-muted",
                            ),
                            dbc.Badge(
                                "Unsaved changes",
                                id="asset-fit-unsaved-pill",
                                color="warning",
                                pill=True,
                                className="ms-2",
                                style={"display": "none"},
                            ),
                        ],
                        className="d-flex align-items-center mb-3",
                    ),
                    dbc.Alert(
                        id="asset-fit-guardrail-alert",
                        color="danger",
                        is_open=False,
                    ),
                    create_stepper(),
                    dbc.Row(
                        [
                            dbc.Col(create_wizard_body(), md=7, lg=7),
                            dbc.Col(create_summary_panel(), md=5, lg=5),
                        ],
                        className="mt-3",
                    ),
                ],
                fluid=True,
                id="asset-fit-wizard-container",
            ),
        ]
    )


def create_stepper() -> html.Div:
    buttons = []
    for index, step in enumerate(STEP_ORDER, start=1):
        buttons.append(
            dbc.Button(
                [
                    html.Span(str(index), className="me-1"),
                    html.Span(step["label"]),
                ],
                id={"type": "asset-fit-step-button", "step": step["key"]},
                color="secondary",
                outline=True,
                className="me-1 mb-1 step-button",
            )
        )
    return html.Div(
        [
            html.Div(buttons, className="mb-2"),
            html.Small(id="asset-fit-stepper-progress", className="text-muted"),
        ]
    )


def create_wizard_body() -> html.Div:
    return html.Div(
        [
            dcc.Tabs(
                id="asset-fit-step-tabs",
                value="product",
                children=[
                    dcc.Tab(label="Product", value="product", children=create_product_step()),
                    dcc.Tab(label="Units", value="units", children=create_units_step()),
                    dcc.Tab(label="Physical", value="physical", children=create_physical_step()),
                    dcc.Tab(label="Parking/Transit", value="parking", children=create_parking_step()),
                    dcc.Tab(label="Amenities", value="amenities", children=create_amenities_step()),
                    dcc.Tab(label="Summary", value="summary", children=create_summary_step()),
                ],
            ),
            dbc.Stack(
                [
                    dbc.Button("Previous", id="asset-fit-prev-btn", color="secondary"),
                    dbc.Button("Next", id="asset-fit-next-btn", color="primary"),
                    dbc.Button(
                        "Reset to product standards",
                        id="asset-fit-reset-btn",
                        color="link",
                        className="text-decoration-none",
                    ),
                ],
                gap=2,
                direction="horizontal",
                className="mt-3",
            ),
        ]
    )


def create_product_step() -> html.Div:
    return html.Div(
        [
            html.Div(id="field-product-type", children=[
                html.Label("Product Type"),
                dcc.Dropdown(id="asset-fit-input-product-type", options=[]),
            ]),
            html.Div(id="field-year-built", className="mt-3", children=[
                html.Label("Vintage Year"),
                dcc.Input(id="asset-fit-input-year-built", type="number", debounce=True, min=1900, max=datetime.now().year),
            ]),
            html.Div(id="field-total-units", className="mt-3", children=[
                html.Label("Total Units"),
                dcc.Input(id="asset-fit-input-total-units", type="number", debounce=True, min=1),
            ]),
        ],
        className="p-3",
    )


def create_units_step() -> html.Div:
    table = dash_table.DataTable(
        id="asset-fit-unit-mix-table",
        columns=[
            {"name": "Unit Type", "id": "type", "editable": False},
            {"name": "Share %", "id": "pct", "type": "numeric"},
            {"name": "Avg SF", "id": "size_sqft", "type": "numeric"},
        ],
        editable=True,
        row_deletable=False,
        style_table={"overflowX": "auto"},
    )
    return html.Div(
        [
            html.P("Define the unit mix for the asset."),
            table,
        ],
        className="p-3",
    )


def create_physical_step() -> html.Div:
    return html.Div(
        [
            html.Div(id="field-ceiling", children=[
                html.Label("Minimum Ceiling Height (ft)"),
                dcc.Input(id="asset-fit-input-ceiling", type="number", debounce=True, min=7, step=0.1),
            ]),
            html.Div(className="mt-3", id="field-wd", children=[
                html.Label("In-unit Washer/Dryer"),
                dbc.Checkbox(id="asset-fit-toggle-wd", switch=True, label="Required"),
            ]),
        ],
        className="p-3",
    )


def create_parking_step() -> html.Div:
    return html.Div(
        [
            html.Div(id="field-parking-ratio", children=[
                html.Label("Observed Parking Ratio"),
                dcc.Input(id="asset-fit-input-parking-ratio", type="number", debounce=True, min=0, step=0.05),
            ]),
            html.Div(className="mt-3", id="field-parking-context", children=[
                html.Label("Parking Context"),
                dcc.Dropdown(
                    id="asset-fit-input-parking-context",
                    options=[
                        {"label": "Surface", "value": "surface"},
                        {"label": "Structured", "value": "structured"},
                        {"label": "Shared", "value": "shared"},
                        {"label": "Transit-oriented", "value": "transit"},
                    ],
                ),
            ]),
        ],
        className="p-3",
    )


def create_amenities_step() -> html.Div:
    toggles = [
        ("balconies", "Balconies"),
        ("gear_nook", "Gear Nook / Mudroom"),
        ("bike_storage", "Secure Bike Storage"),
        ("dog_wash", "Dog Wash"),
        ("ev_ready", "EV-ready Parking"),
    ]
    return html.Div(
        [
            html.P("Toggle amenities present at the asset."),
            *(
                html.Div(
                    dbc.Checkbox(
                        id={"type": "asset-fit-toggle-amenity", "amenity": key},
                        switch=True,
                        label=label,
                    ),
                    className="mb-2",
                )
                for key, label in toggles
            ),
        ],
        className="p-3",
    )


def create_summary_step() -> html.Div:
    return html.Div(
        [
            html.H5("Review & Save"),
            html.P("Confirm scoring details before saving a fit report."),
            dbc.Button("Save report", id="asset-fit-save-btn", color="success"),
            html.Div(id="asset-fit-save-feedback", className="mt-2 text-muted"),
        ],
        className="p-3",
    )


def create_summary_panel() -> html.Div:
    return html.Div(
        [
            dbc.Card(
                [
                    dbc.CardHeader("Fit Score"),
                    dbc.CardBody(
                        [
                            html.H2("--", id="asset-fit-score-number", className="display-4 text-center"),
                            dcc.Graph(id="asset-fit-score-gauge", figure=gauge_figure(0)),
                            html.Div(id="asset-fit-score-updated", className="text-muted small mt-2 text-center"),
                        ]
                    ),
                ]
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Flags"),
                    dbc.CardBody(
                        [
                            html.Div(
                                id="asset-fit-flags-container",
                                children=html.Div("No flags raised", className="text-muted"),
                            ),
                        ]
                    ),
                ],
                className="mt-3",
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Mandate Guardrails"),
                    dbc.CardBody(
                        [
                            html.Div(id="asset-fit-guardrail-summary", className="small text-muted"),
                        ]
                    ),
                ],
                className="mt-3",
            ),
        ]
    )


def gauge_figure(score: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#2563eb"},
                "steps": [
                    {"range": [0, 50], "color": "#fee2e2"},
                    {"range": [50, 75], "color": "#fef9c3"},
                    {"range": [75, 100], "color": "#dcfce7"},
                ],
            },
            number={"suffix": " /100"},
        )
    )
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20))
    return fig


# Callbacks


@callback(
    Output("asset-fit-query-store", "data"),
    Input("asset-fit-location", "search"),
    prevent_initial_call=False,
)
def parse_query(search: str | None) -> Dict[str, str]:
    if not search:
        return {"asset_id": "AKR-123", "msa_id": None}
    params = parse_qs(search.lstrip("?"))
    asset_id = params.get("asset_id", ["AKR-123"])[0]
    msa_id = params.get("msa_id", [None])[0]
    return {"asset_id": asset_id, "msa_id": msa_id}


@callback(
    Output("asset-fit-defaults-store", "data"),
    Output("asset-fit-guardrails-store", "data"),
    Output("asset-fit-guardrail-alert", "is_open"),
    Output("asset-fit-guardrail-alert", "children"),
    Output("asset-fit-subtitle", "children"),
    Input("asset-fit-query-store", "data"),
)
def load_defaults(query: Dict[str, str]):
    asset_id = (query or {}).get("asset_id") or "AKR-123"
    defaults = get_default_form_inputs(asset_id)
    if not defaults:
        return {}, {}, True, "Unable to load asset context", ""
    msa_id = (query or {}).get("msa_id") or defaults.get("msa_id")
    guardrails = get_guardrails(msa_id) if msa_id else None
    if not guardrails:
        return defaults, {}, True, "Unable to load guardrails; Fit Score disabled", f"Asset {asset_id}"
    subtitle = f"Asset {asset_id} · MSA {msa_id}"
    return defaults, guardrails, False, "", subtitle


@callback(
    Output("asset-fit-form-store", "data"),
    Output("asset-fit-step-tabs", "value"),
    Output("asset-fit-local-store", "data"),
    Input("asset-fit-defaults-store", "data"),
    Input("asset-fit-local-store", "data"),
    State("asset-fit-query-store", "data"),
    prevent_initial_call=False,
)
def initialise_form(defaults, local_store, query):
    asset_id = (query or {}).get("asset_id") or "AKR-123"
    persisted_forms = local_store or {}
    form_data = persisted_forms.get(asset_id) if isinstance(persisted_forms, dict) else None
    if not form_data:
        form_data = get_default_form_inputs(asset_id)
    persisted_forms[asset_id] = form_data
    return form_data, "product", persisted_forms


@callback(
    Output("asset-fit-input-product-type", "options"),
    Output("asset-fit-input-product-type", "value"),
    Output("asset-fit-input-year-built", "value"),
    Output("asset-fit-input-total-units", "value"),
    Output("asset-fit-unit-mix-table", "data"),
    Output("asset-fit-input-ceiling", "value"),
    Output("asset-fit-toggle-wd", "value"),
    Output("asset-fit-input-parking-ratio", "value"),
    Output("asset-fit-input-parking-context", "value"),
    Output("asset-fit-guardrail-summary", "children"),
    Output("asset-fit-stepper-progress", "children"),
    Input("asset-fit-form-store", "data"),
    State("asset-fit-guardrails-store", "data"),
)
def populate_inputs(form_data, guardrails):
    if not form_data:
        return [], None, None, None, [], None, False, None, None, "", ""
    guardrail_summary = ""
    if guardrails:
        guardrail_summary = (
            f"Mandate: {guardrails.get('label','')} · Min year {guardrails.get('min_year_built','N/A')} ·"
            f" Parking ≥ {guardrails.get('parking_ratio_required','N/A')}"
        )
    options = [
        {"label": opt.title().replace("_", " "), "value": opt}
        for opt in guardrails.get("allowed_product_types", [])
    ] if guardrails else []
    unit_mix = form_data.get("unit_mix") or []
    return (
        options,
        form_data.get("product_type"),
        form_data.get("year_built"),
        form_data.get("total_units"),
        unit_mix,
        form_data.get("ceiling_min_ft"),
        form_data.get("wd_in_unit", False),
        form_data.get("parking_ratio_observed"),
        form_data.get("parking_context"),
        guardrail_summary,
        " · ".join(step["label"] for step in STEP_ORDER),
    )


@callback(
    Output("asset-fit-form-store", "data", allow_duplicate=True),
    Output("asset-fit-unsaved-pill", "style"),
    Input("asset-fit-input-product-type", "value"),
    Input("asset-fit-input-year-built", "value"),
    Input("asset-fit-input-total-units", "value"),
    Input("asset-fit-unit-mix-table", "data"),
    Input("asset-fit-input-ceiling", "value"),
    Input("asset-fit-toggle-wd", "value"),
    Input("asset-fit-input-parking-ratio", "value"),
    Input("asset-fit-input-parking-context", "value"),
    Input({"type": "asset-fit-toggle-amenity", "amenity": ALL}, "value"),
    State("asset-fit-form-store", "data"),
    State("asset-fit-query-store", "data"),
    prevent_initial_call=True,
)
def update_form_store(product, year, total_units, unit_mix, ceiling, wd_value, parking_ratio, parking_context, amenity_values, current_form, query):
    if current_form is None:
        current_form = {}
    updated = dict(current_form)
    triggered = ctx.triggered_id
    if triggered == "asset-fit-input-product-type":
        updated["product_type"] = product
    elif triggered == "asset-fit-input-year-built":
        updated["year_built"] = year
    elif triggered == "asset-fit-input-total-units":
        updated["total_units"] = total_units
    elif triggered == "asset-fit-unit-mix-table":
        updated["unit_mix"] = unit_mix or []
    elif triggered == "asset-fit-input-ceiling":
        updated["ceiling_min_ft"] = ceiling
    elif triggered == "asset-fit-toggle-wd":
        updated["wd_in_unit"] = bool(wd_value)
    elif triggered == "asset-fit-input-parking-ratio":
        updated["parking_ratio_observed"] = parking_ratio
    elif triggered == "asset-fit-input-parking-context":
        updated["parking_context"] = parking_context
    elif isinstance(triggered, dict) and triggered.get("type") == "asset-fit-toggle-amenity":
        amenity_key = triggered.get("amenity")
        value = bool(ctx.triggered[0]["value"])
        amenities = dict(updated.get("amenities", {}))
        amenities[amenity_key] = value
        updated["amenities"] = amenities
    return updated, {"display": "inline-block"}


@callback(
    Output("asset-fit-local-store", "data", allow_duplicate=True),
    Input("asset-fit-form-store", "data"),
    State("asset-fit-query-store", "data"),
    State("asset-fit-local-store", "data"),
    prevent_initial_call=True,
)
def persist_local(form_data, query, local_store):
    asset_id = (query or {}).get("asset_id") or "AKR-123"
    store = local_store or {}
    store[asset_id] = form_data
    return store


@callback(
    Output("asset-fit-score-number", "children"),
    Output("asset-fit-score-updated", "children"),
    Output("asset-fit-score-gauge", "figure"),
    Output("asset-fit-flags-container", "children"),
    Output("asset-fit-status-store", "data"),
    Input("asset-fit-form-store", "data"),
    State("asset-fit-defaults-store", "data"),
    State("asset-fit-guardrails-store", "data"),
    State("asset-fit-status-store", "data"),
    prevent_initial_call=True,
)
def update_scorecard(form_data, defaults, guardrails, status_store):
    if not form_data or not guardrails:
        return (
            "--",
            "",
            gauge_figure(0),
            html.Div("No guardrail flags", className="text-muted"),
            status_store or {"dirty": False},
        )
    evaluation = evaluate_fit(defaults=defaults, inputs=form_data, guardrails=guardrails)
    score = evaluation["fit_score"]
    flags = evaluation["flags"]
    status = status_store or {"dirty": False}
    status.update({
        "dirty": True,
        "last_result": evaluation,
        "timestamp": datetime.utcnow().isoformat(),
    })
    flag_items = []
    if flags:
        for flag in flags:
            severity = flag["severity"].lower()
            color = "success" if severity == "info" else "warning" if severity == "warn" else "danger"
            flag_items.append(
                dbc.Button(
                    [
                        dbc.Badge(flag["severity"].upper(), color=color, className="me-2"),
                        html.Span(flag["message"]),
                    ],
                    id={"type": "asset-fit-flag-button", "code": flag["code"]},
                    color="link",
                    className="d-block text-start mb-1",
                )
            )
    else:
        flag_items = [html.Div("No guardrail flags", className="text-muted")]

    updated_text = f"Last updated {datetime.utcnow().strftime('%H:%M:%S')} UTC"
    return f"{score:.1f}", updated_text, gauge_figure(score), flag_items, status


@callback(
    Output("asset-fit-step-tabs", "value", allow_duplicate=True),
    Input("asset-fit-next-btn", "n_clicks"),
    Input("asset-fit-prev-btn", "n_clicks"),
    State("asset-fit-step-tabs", "value"),
    prevent_initial_call=True,
)
def change_step(next_clicks, prev_clicks, current_step):
    triggered = ctx.triggered_id
    index = next((i for i, step in enumerate(STEP_ORDER) if step["key"] == current_step), 0)
    if triggered == "asset-fit-next-btn" and index < len(STEP_ORDER) - 1:
        return STEP_ORDER[index + 1]["key"]
    if triggered == "asset-fit-prev-btn" and index > 0:
        return STEP_ORDER[index - 1]["key"]
    return no_update


@callback(
    Output("asset-fit-step-tabs", "value", allow_duplicate=True),
    Input({"type": "asset-fit-step-button", "step": dash.ALL}, "n_clicks"),
    State("asset-fit-step-tabs", "value"),
    prevent_initial_call=True,
)
def click_step_button(step_clicks, current):
    triggered = ctx.triggered_id
    if isinstance(triggered, dict) and triggered.get("type") == "asset-fit-step-button":
        return triggered.get("step")
    return current


@callback(
    Output("asset-fit-form-store", "data", allow_duplicate=True),
    Input("asset-fit-reset-btn", "n_clicks"),
    State("asset-fit-defaults-store", "data"),
    State("asset-fit-form-store", "data"),
    State("asset-fit-query-store", "data"),
    prevent_initial_call=True,
)
def reset_to_defaults(n_clicks, defaults, form_data, query):
    if not n_clicks:
        return no_update
    baseline = dict(defaults or {})
    asset_id = (query or {}).get("asset_id") or baseline.get("asset_id") or "AKR-123"
    product_type = (form_data or {}).get("product_type") or baseline.get("product_type")
    if product_type:
        product_defaults = get_product_default(asset_id, product_type)
        if product_defaults:
            baseline["ceiling_min_ft"] = product_defaults.get("ceiling_min_ft", baseline.get("ceiling_min_ft"))
            baseline["parking_ratio_observed"] = product_defaults.get("parking_ratio", baseline.get("parking_ratio_observed"))
            baseline["wd_in_unit"] = product_defaults.get("amenities", {}).get("wd_in_unit", baseline.get("wd_in_unit", True))
            baseline["amenities"] = product_defaults.get("amenities", baseline.get("amenities", {}))
    return baseline


@callback(
    Output("asset-fit-save-feedback", "children"),
    Output("asset-fit-unsaved-pill", "style", allow_duplicate=True),
    Output("asset-fit-status-store", "data", allow_duplicate=True),
    Input("asset-fit-save-btn", "n_clicks"),
    State("asset-fit-status-store", "data"),
    State("asset-fit-query-store", "data"),
    State("asset-fit-defaults-store", "data"),
    State("asset-fit-guardrails-store", "data"),
    prevent_initial_call=True,
)
def save_report(n_clicks, status_store, query, defaults, guardrails):
    if not n_clicks:
        return no_update, no_update, no_update
    status = status_store or {}
    last_result = status.get("last_result")
    if not last_result:
        return "No calculation available to save", {"display": "inline-block"}, status
    try:
        report_id = save_fit_report(
            asset_id=(query or {}).get("asset_id", "AKR-123"),
            msa_id=(query or {}).get("msa_id"),
            evaluation=last_result,
            context=guardrails or {},
            role="analyst",
        )
    except PermissionError:
        return "Insufficient permissions to save", {"display": "inline-block"}, status
    status["dirty"] = False
    status["last_saved"] = datetime.utcnow().isoformat()
    status["report_id"] = report_id
    return f"Fit report saved ({report_id})", {"display": "none"}, status


@callback(
    Output("asset-fit-highlight-store", "data"),
    Input({"type": "asset-fit-flag-button", "code": dash.ALL}, "n_clicks"),
    State("asset-fit-highlight-store", "data"),
    prevent_initial_call=True,
)
def handle_flag_click(flag_clicks, current):
    triggered = ctx.triggered_id
    if isinstance(triggered, dict) and triggered.get("type") == "asset-fit-flag-button":
        return {"target": triggered.get("code"), "ts": datetime.utcnow().isoformat()}
    return current


@callback(
    Output("asset-fit-input-product-type", "style", allow_duplicate=True),
    Output("asset-fit-input-parking-ratio", "style", allow_duplicate=True),
    Input("asset-fit-highlight-store", "data"),
    prevent_initial_call=True,
)
def highlight_fields(target_data):
    default_style = {}
    highlight_style = {"boxShadow": "0 0 0 0.2rem rgba(59,130,246,.5)"}
    target = (target_data or {}).get("target")
    style_product = highlight_style if target in {"PRODUCT_TYPE_DISALLOWED"} else default_style
    style_parking = highlight_style if target in {"PARKING_SHORTFALL"} else default_style
    return style_product, style_parking


# Register to Dash app via register_callbacks in dash_app.py

def register_callbacks(app: Dash) -> None:
    pass
