# author: Gwydion Daskalakis <daskalakis@uni-heidelberg.de>
# license: CC0


import numpy as np
from dash import dcc, html, Input, Output, Dash, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

# change this if dash complains about the port being in use.
dash_port = 8053

# These can be freely changed. The order of the dict determines the order in the graph. (only inverted)
activities_explanations = {
    "RSE Network": "Activities that bring RSEs together to share knowledge, identify synergies and support RSEs. Examples: Organizing workshops, code reviews, …",
    "Partner Network": "Activities to network with organizational stakeholders that require software management. Examples: Coordinate offers by and needs from computing center, library, legal services and large grant structures.",
    "RSE Teaching": "Similar to consultations but larger in scale. Examples: Software Carpentry courses.",
    "RSE Consultation": "Advising research (projects) by sharing knowledge. Examples: (Software) Project Management, grant proposal requirements, SMPs, licensing.",
    "SW Development": "Writing software as a (bookable) service for research projects. Examples: UI or App development",
    "SW Maintenance": "Keeping research software usable is an ongoing task. Examples: ",
    "RSE Infrastructure": "Collaborative or centralized provisioning of IT platforms that support RSEngineering. Examples: Coordinating access to JupyterHUB.",
    "RSE Research": "Community building outside the organization. Examples: Lobbying.",
    "RSE Outreach": "Investigating current issues in RSEngineering. Examples: Security of research software.",
}


def create_settings_card(name, explanation):
    # create a settings card for a given name and include the explanation below.
    # Also add two input fields for the weight and width of the activity.
    # Any change in input field will trigger the update_graph callback.

    settings_card = dbc.Card(
        dbc.CardBody(
            children=[
                html.H3(name, id={"type": "activity-name", "index": name}),
                html.P(
                    explanation,
                    style={
                        "font-size": "10px",
                    },
                ),
                html.Div(
                    [
                        dbc.Row(
                            [
                                # labels
                                dbc.Col(
                                    [
                                        html.P("Weight", style={"font-size": "10px"}),
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        html.P(
                                            "Centralization",
                                            style={"font-size": "10px"},
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        dbc.Row(
                            [
                                # height scale input
                                dbc.Col(
                                    [
                                        dcc.Input(
                                            value=1,
                                            min=0,
                                            type="number",
                                            id={
                                                "type": "activity-weight",
                                                "index": name,
                                            },
                                            style={"width": "50%"},
                                        ),
                                    ],
                                    style={"font-size": "10px"},
                                ),
                                dbc.Col(
                                    [
                                        # width scale input
                                        dcc.Input(
                                            value=0.5,
                                            min=0,
                                            max=1,
                                            step=0.1,
                                            type="number",
                                            id={
                                                "type": "activity-width",
                                                "index": name,
                                            },
                                            style={"width": "50%"},
                                        ),
                                    ],
                                    style={"font-size": "10px"},
                                ),
                            ],
                        ),
                    ]
                ),
            ],
        ),
        id=f"{name}-settings-box",
    )
    return settings_card


def create_accordion_settings():
    acc_items = []
    for name, explanation in activities_explanations.items():
        acc_items.append(
            dbc.AccordionItem(
                children=[create_settings_card(name, explanation)],
                title=name,
            )
        )

    accordion = dbc.Accordion(acc_items)
    return accordion


# Callback function to draw a new graph based on the input widgets.
def update_graph(names, heights, widths):
    # end points for the different plot regions
    proportions = [0.2, 0.3, 1]

    # norm heights to 1
    heights = heights / np.sum(heights)

    # calculate the total height of each section
    total_height = []
    for i in np.arange(len(heights)):
        total_height.append(np.sum(heights[: i + 1]))

    # create the figure
    fig = go.Figure(
        layout={
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
            "xaxis": {"title": "x-label", "visible": False, "showticklabels": False},
            "yaxis": {"title": "y-label", "visible": False, "showticklabels": False},
        },
    )

    ## setup the left side
    # this does not change when we change the height widgets.
    y_left = np.arange(1, len(heights) + 1) / len(heights)

    # here we draw the parallel lines based only on the amount of categories to display.
    for y, name in zip(y_left, names):
        fig.add_scatter(
            x=[0, proportions[0]],
            y=[y, y],
            mode="lines",
            line=dict(color="black", width=1),
            showlegend=False,
            hoverinfo="skip",
        )
        # add the names as labels on the left

        fig.add_annotation(
            x=0.1,
            y=(y) - (1 / len(names) / 2),
            text=name,
            align="left",  # doesn't work
            showarrow=False,
            font=dict(size=14),
        )

    # add bounding box on the left
    fig.add_shape(
        type="rect",
        x0=0,
        y0=0,
        x1=proportions[0],
        y1=1,
        line=dict(color="black", width=1),
    )

    ## setup the middle section
    # we transition from the previous lines to the new weighted distribution
    for y_start, y_end, name in zip(y_left, total_height, names):
        fig.add_scatter(
            x=[proportions[0], proportions[1]],
            y=[y_start, y_end],
            mode="lines",
            line=dict(color="black", width=1),
            showlegend=False,
            hoverinfo="skip",
        )

    fig.add_shape(
        type="rect",
        x0=proportions[0],
        y0=0,
        x1=proportions[1],
        y1=1,
        line=dict(color="black", width=1),
    )

    ## setup the right side

    # bounding box
    fig.add_shape(
        type="rect",
        x0=proportions[1],
        y0=0,
        x1=proportions[2],
        y1=1,
        line=dict(color="black", width=1),
    )

    # here we need to do a split according to the set widths
    x_length = proportions[2] - proportions[1]

    y_prev = 0

    # we draw two boxes, each based on the weighted distribution.
    # one for the amount of centralized and one for decentralized percentage.
    for y, x_split, name in zip(total_height, widths, names):
        # add pre split region
        fig.add_scatter(
            # we basically draw a rectangle including the starting point as end point and fill in the center
            x=[
                proportions[1],
                proportions[1],
                proportions[1] + x_split * x_length,
                proportions[1] + x_split * x_length,
                proportions[1],
            ],
            y=[y, y_prev, y_prev, y, y],
            mode="lines",
            fill="toself",
            line=dict(color="black", width=1),
            fillpattern=go.scatter.Fillpattern(
                shape="/", bgcolor="white", fillmode="overlay"
            ),
            showlegend=False,
            hoverinfo="skip",
        )
        # add post split region
        fig.add_scatter(
            # we basically draw a rectangle including the starting point as end point and fill in the center
            x=[
                proportions[1] + x_split * x_length,
                proportions[1] + x_split * x_length,
                proportions[2],
                proportions[2],
                proportions[1] + x_split * x_length,
            ],
            y=[y, y_prev, y_prev, y, y],
            mode="lines",
            fill="toself",
            line=dict(color="black", width=1),
            fillpattern=go.scatter.Fillpattern(
                shape="\\", bgcolor="white", fillmode="overlay"
            ),
            showlegend=False,
            hoverinfo="skip",
        )

        # set the y_prev values for the next iteration
        y_prev = y

    return fig


if __name__ == "__main__":
    app = Dash("RSE Overview", external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = dbc.Row(
        [
            dbc.Col(create_accordion_settings(), width=3),
            dbc.Col(dcc.Graph(id="RSE_graph", style={"height": "80%"}), width=9),
        ]
    )
    # add update_graph as app callback. This is triggered by any value change of the inputs.
    app.callback(
        Output("RSE_graph", "figure"),
        Input(
            {
                "type": "activity-name",
                "index": ALL,
            },
            "children",
        ),
        Input(
            {
                "type": "activity-weight",
                "index": ALL,
            },
            "value",
        ),
        Input(
            {
                "type": "activity-width",
                "index": ALL,
            },
            "value",
        ),
    )(update_graph)

    app.run_server(debug=True, port=dash_port)
