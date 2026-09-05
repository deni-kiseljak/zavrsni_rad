import json

import scrapy
from scrapy.spiders import SitemapSpider
from ..items import PriceScraperItem


class InstarSpider(scrapy.Spider):
    name = "instar"
    allowed_domains = ["instar-informatika.hr"]
    start_urls = ["https://www.instar-informatika.hr/sitemap.xml"]
    sitemap_urls= ["https://www.instar-informatika.hr/sitemap.xml",]
    sitemap_rules = [("/product/", "parse")]
    webshop_id = 2

    def parse(self, response, **kwargs):
        urls = response.xpath("//*[local-name()='url']/*[local-name()='loc']/text()").getall()
        # print("URLS---------------------------------------------------\n\n", urls)
        for url in urls[:]:
            # print(url)
            if "/product/" in url:
                yield response.follow(url,callback=self.parse_product)
        # product_urls = [
        #     url for url in urls
        #     if "/product/" in url
        # ]

        # for url in product_urls:
        #     yield response.follow(url, callback=self.parse_product)

    def parse_product(self, response, **kwargs):
        json_ld = response.xpath('//script[@type="application/ld+json"]/text()').getall()

        for script in json_ld:
            try:
                data = json.loads(script)
            except json.JSONDecodeError:
                continue

            if data.get("@type") != "Product":
                continue

            product = data
            offer = product.get("offers") or {}

            if not offer:
                continue

            price = offer.get("price")

            if not price:
                continue

            yield PriceScraperItem(
                name=product.get("name"),
                sku=product.get("sku"),
                mpn=response.xpath("//div[@class='barcode']/span/text()").get(),
                price=price,
                currency=offer.get("priceCurrency"),
                availability=offer.get("availability"),
                url=response.url,
            )
            break

    # def parse(self, response, **kwargs):
    #     yield from self.parse_product(response)

    # def parse(self, response):
    #     with open("page.html", "wb") as f:
    #         f.write(response.body)

    # def parse_product(self, response):
    #     yield {
    #         "name": response.css("h1::text").get(),
    #         "url": response.url,
    #         "price": response.xpath("//span[contains(@class, 'mainprice')]/string()").get(),
    #         "currency": response.css("span::text").get(),
    #     }