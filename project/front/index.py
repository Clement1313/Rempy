from dash import Dash, dcc, html, Input, Output, State, callback
import compute
import base64
import os
import pandas as pd
from dash import dash_table
import stats
import time

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.H1(
            "Fast Marching Algorithms Benchmarks",
            style={
                "textAlign": "center",
                "marginBottom": "40px",
                "marginTop": "30px",
            },
        ),

        html.Div(
            dcc.Upload(
                id="upload-image",
                children=html.Button("Upload PNG Image"),
                multiple=False,
            ),
            style={"textAlign": "center", "marginBottom": "30px"},
        ),

        html.Div(
            id="image-section",
            style={"display": "none"},
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                html.H5("Original Image"),
                                html.Img(
                                    id="display-image",
                                    style={
                                        "maxWidth": "100%",
                                        "borderRadius": "8px",
                                        "boxShadow": "0px 4px 12px rgba(0,0,0,0.1)",
                                    },
                                ),
                            ],
                            style={"width": "48%"},
                        ),
                        html.Div(
                            [
                                html.H5("Mask"),
                                html.Img(
                                    id="mask-image",
                                    style={
                                        "maxWidth": "100%",
                                        "borderRadius": "8px",
                                        "boxShadow": "0px 4px 12px rgba(0,0,0,0.1)",
                                        "marginBottom": "15px",
                                    },
                                ),
                                dcc.Slider(
                                    0,
                                    100,
                                    5,
                                    value=50,
                                    id="threshold-slider",
                                ),
                            ],
                            style={"width": "48%"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "marginBottom": "20px",
                    },
                ),
                html.Div(
                    html.Button(
                        "Compute",
                        id="compute-btn",
                        n_clicks=0,
                        style={
                            "padding": "10px 30px",
                            "fontSize": "16px",
                        },
                    ),
                    style={"textAlign": "center", "marginTop": "10px"},
                ),
            ],
        ),

        html.Div(
            id="compute-output",
            style={"textAlign": "center", "marginTop": "30px"},
        ),

        dcc.Store(id="image-history", data=[]),
        dcc.Store(id="current-image-name", data=""),
        dcc.Store(id="current-mask-url", data=""),
        dcc.Store(id="benchmark-data", data=[]),

        html.Div(
            [
                dash_table.DataTable(
                    id="benchmark-table",
                    columns=[],
                    data=[],
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "textAlign": "left",
                        "padding": "8px",
                    },
                    page_size=10,
                    sort_action="native",
                    filter_action="native",
                    style_header={
                        "fontWeight": "bold",
                        "backgroundColor": "#f4f4f4",
                    },
                )
            ],
            style={"marginTop": "40px"},
        ),

        html.Div(
            id="graphs-section",
            style={"display": "none", "marginTop": "40px"},
            children=[
                html.Div(
                    dcc.Graph(id="scatter-plot"),
                    style={"width": "48%"},
                ),
                html.Div(
                    dcc.Graph(id="sbar-graph"),
                    style={"width": "48%"},
                ),
            ],
            className="row",
        ),
    ],
    style={"width": "85%", "margin": "auto"},
)


@callback(
    Output("image-section", "style"),
    Input("upload-image", "contents"),
)
def show_image_section(contents):
    if contents:
        return {"display": "block"}
    return {"display": "none"}


@callback(
    Output("display-image", "src"),
    Output("mask-image", "src"),
    Output("current-image-name", "data"),
    Output("current-mask-url", "data"),
    Input("upload-image", "contents"),
    Input("threshold-slider", "value"),
    State("upload-image", "filename"),
)
def update_image(contents, threshold, filename):

    if contents is None:
        return None, None, "", ""

    upload_dir = "media/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(decoded)

    threshold_normalized = threshold / 100.0
    mask_resp = compute.compute_mask(file_path, threshold_normalized)

    if isinstance(mask_resp, str):
        return contents, None, file_path, ""

    mask_url = mask_resp.get("mask_url")
    if not mask_url:
        return contents, None, file_path, ""

    full_mask_url = (
        f"http://localhost:8000{mask_url}?t={int(time.time() * 1000)}"
    )

    return contents, full_mask_url, file_path, mask_url


@callback(
    Output("compute-output", "children"),
    Output("benchmark-data", "data"),
    Output("graphs-section", "style"),
    Input("compute-btn", "n_clicks"),
    State("current-image-name", "data"),
    State("current-mask-url", "data"),
    State("benchmark-data", "data"),
    State("threshold-slider", "value"),
)
def on_compute(n_clicks, image_name, mask_url, stored_data, threshold):

    if not n_clicks or n_clicks <= 0:
        return "", stored_data, {"display": "none"}

    result = compute.run_benchmark(image_name, mask_url, threshold)

    if not isinstance(result, dict):
        return str(result), stored_data, {"display": "none"}

    raw_entries = result.get("raw", [])
    children = []

    if raw_entries:
        first_entry = raw_entries[0]
        url = first_entry.get("output_image")

        if url:
            full_url = f"http://localhost:8000{url}"
            children.append(
                html.Img(
                    src=full_url,
                    style={
                        "height": "250px",
                        "marginTop": "20px",
                        "borderRadius": "8px",
                    },
                )
            )

    row = compute.raw_to_single_row(raw_entries)

    if stored_data is None:
        stored_data = []

    stored_data.append(row)

    return children, stored_data, {"display": "flex", "justifyContent": "space-between"}


@callback(
    Output("benchmark-table", "columns"),
    Output("benchmark-table", "data"),
    Input("benchmark-data", "data"),
)
def update_table(data):
    if not data:
        return [], []
    df = pd.DataFrame(data)
    columns = [{"name": col, "id": col} for col in df.columns]
    return columns, df.to_dict("records")


@callback(Output("scatter-plot", "figure"), Input("benchmark-data", "data"))
def compute_scatter_plot(benchmark_data):
    if not benchmark_data:
        return {}
    df = pd.DataFrame(benchmark_data)
    return stats.time_vs_size(df)


@callback(Output("sbar-graph", "figure"), Input("benchmark-data", "data"))
def compute_bar_graph(benchmark_data):
    if not benchmark_data:
        return {}
    df = pd.DataFrame(benchmark_data)
    return stats.bar_chart_time(df)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)