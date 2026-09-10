# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import dataclass


@dataclass
class PriceScraperItem:
    name: str | None = None
    sku: str | None = None
    mpn: str | None = None
    price: float | None = None
    currency: str | None = None
    availability: str | None = None
    url: str | None = None

