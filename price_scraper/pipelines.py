# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import psycopg2

class PriceScraperPipeline:

    def __init__(self):
        self.cursor = None
        self.connection = None

    def open_spider(self, spider):
        self.connection = psycopg2.connect(
            host="localhost",
            database="scraper_db",
            user="postgres",
            password="password123",
            port="5432")

        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        self.cursor.close()
        self.connection.close()

    def process_item(self, item, spider):

        webshop_id = spider.webshop_id

        mpn = item.mpn.strip() if item.mpn else None

        if not mpn:
            print("No MPN, skipping item:", item.name)
            return item

        self.cursor.execute(
            """
            SELECT id
            FROM products
            WHERE mpn = %s
            """,
            (mpn,))
        result = self.cursor.fetchone()



        if result:
            product_id = result[0]

        else:
            self.cursor.execute(
                """
                INSERT INTO products (name, sku, mpn)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (item.name, item.sku, mpn))

            product_id = self.cursor.fetchone()[0]

        self.cursor.execute(
            """
            INSERT INTO offers (product_id, webshop_id, price, currency, availability, url)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_id, webshop_id)
            DO UPDATE SET
                price = EXCLUDED.price,
                currency = EXCLUDED.currency,
                availability = EXCLUDED.availability,
                url = EXCLUDED.url   
            """,
            (product_id, webshop_id, item.price, item.currency, item.availability, item.url))

        self.connection.commit()

        return item
