import psycopg2
import pandas as pd
import plotly.express as px


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
    MAX(CASE WHEN w.name = 'Instar' THEN o.price END) AS instar_price
FROM products p
JOIN offers o ON p.id = o.product_id
JOIN webshops w ON o.webshop_id = w.id
GROUP BY p.id, p.name, p.mpn
HAVING COUNT(DISTINCT o.webshop_id) = 2
ORDER BY p.mpn;
"""

df = pd.read_sql(query, connection)
df["difference"] = df["links_price"] - df["instar_price"]

fig = px.bar(
    df,
    x="mpn",
    y=["links_price", "instar_price"],
    barmode="group",
    title="Price Comparison: Links vs Instar",
    hover_data=["name", "difference"]
)

fig.update_layout(
    xaxis_title="Product MPN",
    yaxis_title="Price (€)"
)


fig.show()

connection.close()