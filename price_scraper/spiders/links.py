import re

import scrapy
from ..items import PriceScraperItem

class LinksSpider(scrapy.Spider):
    name = "links"
    allowed_domains = ["links.hr"]
    start_urls = ["https://www.links.hr/sitemap.xml"]
    sitemap_urls = ["https://www.links.hr/sitemap.xml", ]
    webshop_id = 1

    # start_urls = [
    #     "https://www.links.hr/sitemap.xml"
    # ]

    # start_urls = [
    #     "https://www.links.hr/hr/racunalo-links-pro-max-bundle-2026-core-i5-rtx-5060-16gb-ram-1tb-ssd-monitor-27-tipkovnica-mis-i-slusalice-010203571"
    # ]

    def parse(self, response, **kwargs):

        urls = response.xpath('//*[local-name()="url"]/*[local-name()="loc"]/text()').getall()

        # for url in urls:
        #
        #     if re.search(r'-\d+$', url):
        #         yield response.follow(
        #             url,
        #             callback=self.parse_product
        #         )

        for url in urls[5000:]:
            print("PRODUCT: ", url)
            if re.search(r'-\d+$', url):
                print("PRODUCT:", url)
                yield response.follow(url, callback=self.parse_product)

    def parse_product(self, response):
        product = response.xpath('//div[@itemtype="http://schema.org/Product"]')

        if not product:
            print("NOT A PRODUCT:", response.url)
            return

        name = response.xpath('//div[@itemtype="http://schema.org/Product"]//meta[@itemprop="name"]/@content').get()
        mpn = response.xpath('//span[contains(@id, "mpn")]/text()').get()

        if name and name.upper().startswith("RABLJENI -"):
            print("SKIPPING USED:", name)
            return

        if name and name.upper().startswith("IZLO"):
            print("SKIPPING DISPLAY:", name)
            return

        if mpn and mpn.upper().startswith(" LDU"):
            print("SKIPPING LDU:", name)
            return

        price = response.xpath("//span[contains(@class, 'price-value')]/text()").get()

        if price:
            price = price.replace("€", "").strip()
            price = price.replace(".", "")
            price = price.replace(",", ".")

        # yield {
        #     "name": response.xpath('//div[@itemtype="http://schema.org/Product"]//meta[@itemprop="name"]/@content').get(),
        #     "mpn": response.xpath('//div[@itemtype="http://schema.org/Product"]//meta[@itemprop="mpn"]/@content').get(),
        #     "sku": response.xpath('//div[@itemtype="http://schema.org/Product"]//meta[@itemprop="sku"]/@content').get(),
        #     # "price": response.xpath("//span[contains(@class, 'price-value')]/text()").get(),
        #     "price": price,
        #     "currency": response.xpath('//div[@itemprop="offers"]//meta[@itemprop="priceCurrency"]/@content').get(),
        #     "availability": response.xpath('//div[@itemprop="offers"]//meta[@itemprop="availability"]/@content').get(),
        #     "url": response.url,
        # }

        yield PriceScraperItem(
            name=name,
            sku=response.xpath('//div[@itemtype="http://schema.org/Product"]//meta[@itemprop="sku"]/@content').get(),
            mpn=mpn,
            price=price,
            currency=response.xpath('//div[@itemprop="offers"]//meta[@itemprop="priceCurrency"]/@content').get(),
            availability=response.xpath('//div[@itemprop="offers"]//meta[@itemprop="availability"]/@content').get(),
            url=response.url
        )