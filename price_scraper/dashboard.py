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

df["most_expensive"] = df[["links_price", "instar_price", "racunala_price"]].max(axis=1)

df["links_difference"] = df["links_price"] - df["most_expensive"]
df["instar_difference"] = df["instar_price"] - df["most_expensive"]
df["racunala_difference"] = df["racunala_price"] - df["most_expensive"]

df["links_difference_percent"] = ((df["links_price"] - df["most_expensive"])/ df["most_expensive"]* 100)
df["instar_difference_percent"] = ((df["instar_price"] - df["most_expensive"])/ df["most_expensive"]* 100)
df["racunala_difference_percent"] = ((df["racunala_price"] - df["most_expensive"])/ df["most_expensive"]* 100)

df["links_difference_percent_display"] = (" " + df["links_difference_percent"].round(2).astype(str) + "%")
df["instar_difference_percent_display"] = (" " + df["instar_difference_percent"].round(2).astype(str) + "%")
df["racunala_difference_percent_display"] = (" " + df["racunala_difference_percent"].round(2).astype(str) + "%")

def find_cheapest(row):
    prices = {
        "Links": row["links_price"],
        "Instar": row["instar_price"],
        "Racunala": row["racunala_price"]
    }

    cheapest_price = min(prices.values())

    cheapest_shops = [
        shop
        for shop, price in prices.items()
        if price == cheapest_price
    ]

    if len(cheapest_shops) == 1:
        return cheapest_shops[0]

    return "Same price"

df["cheapest"] = df.apply(find_cheapest, axis=1)

links_cheapest = (df["cheapest"] == "Links").sum()
instar_cheapest = (df["cheapest"] == "Instar").sum()
racunala_cheapest = (df["cheapest"] == "Racunala").sum()
same_price = (df["cheapest"] == "Same price").sum()

# Bar graph ------------------------------------------------------------------------------------------------------------

fig = px.bar(
    df,
    x="mpn",
    y=["links_price", "instar_price", "racunala_price"],
    barmode="group",
    title="Price Comparison: Links vs Instar vs Racunala.hr",
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
        "cheapest": True
    }

)

fig.update_layout(
    xaxis_title="Product MPN",
    yaxis_title="Price (€)"
)

# Pie chart ------------------------------------------------------------------------------------------------------------
labels = ['Links', 'Instar', 'Racunala.hr', 'Same price']
values = [links_cheapest, instar_cheapest, racunala_cheapest, same_price]

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

# Dash -----------------------------------------------------------------------------------------------------------------

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Price Comparison Dashboard"),
    html.P(f"Comparing {len(df)} products available on all three webshops."),
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

    if selected_filter != "All":
        filtered_df = filtered_df[
            filtered_df["cheapest"] == selected_filter
        ]

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
            "cheapest": True
        }
    )

    filtered_fig.update_layout(
        xaxis_title="Product MPN",
        yaxis_title="Price (€)"
    )

    return filtered_fig

app.run(debug=True)