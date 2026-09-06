# from dash import Dash, dcc, html
import psycopg2
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output



connection = psycopg2.connect(
    host="localhost",
    database="scraper_db",
    user="postgres",
    password="password123",
    port="5432"
)

query = """
SELECT
    p.name,
    p.mpn,
    MAX(CASE WHEN w.name = 'Links' THEN o.price END) AS links_price,
    MAX(CASE WHEN w.name = 'Instar' THEN o.price END) AS instar_price,
    MAX(CASE WHEN w.name = 'Racunala' THEN o.price END) AS racunala_price
FROM products p
JOIN offers o ON p.id = o.product_id
JOIN webshops w ON o.webshop_id = w.id
GROUP BY p.id, p.name, p.mpn
HAVING COUNT(DISTINCT o.webshop_id) = 3
ORDER BY p.mpn;
"""

df = pd.read_sql(query, connection)

connection.close()

df["links_difference"] = df["links_price"] - df["instar_price"]
df["instar_difference"] = df["instar_price"] - df["links_price"]
df["racunala_difference"] = df["racunala_price"] - df["links_price"]

df["links_difference_percent"] = (df["links_difference"] / df["instar_price"] * 100)
df["instar_difference_percent"] = (df["instar_difference"] / df["instar_price"] * 100)
df["racunala_difference_percent"] = (df["racunala_difference"] / df["instar_price"] * 100)

df["links_difference_percent_display"] = (" " + df["links_difference_percent"].round(2).astype(str) + "%")
df["instar_difference_percent_display"] = (" " + df["instar_difference_percent"].round(2).astype(str) + "%")
df["racunala_difference_percent_display"] = (" " + df["racunala_difference_percent"].round(2).astype(str) + "%")
# df["difference_eur"] = df["difference"].round(2)

df["cheaper"] = df.apply(
    lambda row: "Links" if row["links_price"] < row["instar_price"] and row["links_price"] < row["racunala_price"]
    else "Instar" if row["instar_price"] < row["links_price"] and row["instar_price"] < row["racunala_price"]
    else "Racunala" if row["racunala_price"] < row["links_price"] and row["racunala_price"] < row["instar_price"]
    else "Same price",
    axis=1
)

links_cheaper = (df["cheaper"] == "Links").sum()
instar_cheaper = (df["cheaper"] == "Instar").sum()
racunala_cheaper = (df["cheaper"] == "Racunala").sum()
same_price = (df["cheaper"] == "Same price").sum()


# graph ----------------------------------------------------------------------------------------------------------------

fig = px.bar(
    df,
    x="mpn",
    y=["links_price", "instar_price", "racunala_price"],
    barmode="group",
    title="Price Comparison: Links vs Instar",
    hover_data={
        "name": True,
        "links_price": ":.2f",
        "instar_price": ":.2f",
        "racunala_price": ":.2f",
        "links_difference": ":.2f \u20ac",
        "instar_difference": ":.2f \u20ac",
        "racunala_difference": ":.2f \u20ac",
        "links_difference_percent_display": True,
        "instar_difference_percent_display": True,
        "racunala_difference_percent_display": True,
        "cheaper": True
    }

)

fig.update_layout(
    xaxis_title="Product MPN",
    yaxis_title="Price (€)"
)


# Dash -----------------------------------------------------------------------------------------------------------------

app = Dash(__name__)

labels = ['Links', 'Instar', 'Racunala.hr', 'Same price']
values = [links_cheaper, instar_cheaper, racunala_cheaper, same_price]

pie_fig = px.pie(
    names=labels,
    values=values,
    hole=0.3
)

pie_fig.update_traces(
    texttemplate="%{percent}",
    hovertemplate="<b>%{label}</b><br>%{value} products<br>%{percent}<extra></extra>"
)

pie_fig.update_layout(
    title={
        'text': 'Cheapest shop',
        'x': 0.475,
        'xanchor': 'center'
    }
)

app.layout = html.Div([
    html.H1("Price Comparison Dashboard"),
    html.P(f"Comparing {len(df)} products available on both webshops."),
    # html.H2(f"Links cheapest: {links_cheaper}"),
    # html.H2(f"Instar cheapest: {instar_cheaper}"),
    # html.H2(f"Racunala.hr cheapest: {racunala_cheaper}"),
    # html.H2(f"Same price: {same_price}"),
    dcc.Graph(
        id="cheapest-pie-chart",
        figure=pie_fig
    ),
    dcc.Input(
        id="product-search",
        type="text",
        placeholder="Search by product name or MPN...",
        style={"width": "50%"}
    ),
    dcc.Dropdown(
        id="price-filter",
        options=[
            {"label": "All products", "value": "All"},
            {"label": "Links cheapest", "value": "Links"},
            {"label": "Instar cheapest", "value": "Instar"},
            {"label": "Racunala cheapest", "value": "Racunala"},
            {"label": "Same price", "value": "Same price"}
        ],
        value="All",
        clearable=False
    ),

    dcc.Graph(
        id="price-chart",
        figure=fig
    )
])

@app.callback(
    Output("price-chart", "figure"),
    Input("price-filter", "value"),
    Input("product-search", "value")
)

def update_chart(selected_filter, search_text):

    filtered_df = df

    # Price filter
    if selected_filter != "All":
        filtered_df = filtered_df[
            filtered_df["cheaper"] == selected_filter
        ]

    # Product search
    if search_text:
        search_text = search_text.lower()

        filtered_df = filtered_df[
            filtered_df["name"].str.lower().str.contains(search_text,na=False)
            |
            filtered_df["mpn"].str.lower().str.contains(search_text, na=False)
        ]

    filtered_fig = px.bar(
        filtered_df,
        x="mpn",
        y=["links_price", "instar_price", "racunala_price"],
        barmode="group",
        title="Price Comparison: Links vs Instar vs Racunala.hr",
        hover_data={
            "name": True,
            "links_difference": ":.2f",
            "instar_difference": ":.2f",
            "racunala_difference": ":.2f",
            "links_difference_percent_display": True,
            "instar_difference_percent_display": True,
            "racunala_difference_percent_display": True,
            "cheaper": True
        }
    )

    filtered_fig.update_layout(
        xaxis_title="Product MPN",
        yaxis_title="Price (€)"
    )

    return filtered_fig

if __name__ == "__main__":
    app.run(debug=True)