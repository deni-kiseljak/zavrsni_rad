import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

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

print(df)

connection.close()