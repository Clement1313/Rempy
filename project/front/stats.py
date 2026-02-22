import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# df = pd.DataFrame(
#     {
#         "size": [(100, 100), (200, 200), (300, 300)],
#         "time": [7, 8, 9],
#         "time_opti": [10, 11, 12],
#     },
#     index=["img1", "img2", "img3"],
# )

# df["size_val"] = df["size"].apply(lambda x: x[0] * x[1])

def time_vs_size(df):
    df_plot = (
        df.groupby("pixels")[["temps_fast_marching", "temps_fast_marching_numba"]]
        .mean()
        .reset_index()
        .sort_values("pixels")
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_plot["pixels"],
            y=df_plot["temps_fast_marching"],
            mode="lines+markers",
            name="time classic",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_plot["pixels"],
            y=df_plot["temps_fast_marching_numba"],
            mode="lines+markers",
            name="time numba",
        )
    )
    # AJOUT THOMAS
    fig.update_layout(
        xaxis_title="Size (number of pixel)",
        yaxis_title="Time",
        title="Time vs Size",
        legend_title="Courbes",
    )
    return fig


def bar_chart_time(df):
    last_row = df.tail(1)
    fig = go.Figure(
        [
            go.Bar(
                x=["Normal algo time (s)", "Numba algo time (s)"],
                y=last_row[
                    ["temps_fast_marching", "temps_fast_marching_numba"]
                ].values.flatten(),
            )
        ]
    )
    return fig


# def main():
#     fig = make_subplots(rows=1, cols=2)
#     fig1 = time_vs_size(df)
#     fig2 = bar_chart_time(df)
#     for trace in fig1.data:
#         fig.add_trace(trace, row=1, col=1)
#     for trace in fig2.data:
#         fig.add_trace(trace, row=1, col=2)

#     fig.show()


# main()
