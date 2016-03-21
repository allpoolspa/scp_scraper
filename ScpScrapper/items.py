# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

#import scrapy
from scrapy.item import Item, Field


class ScpScrapperItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = Field()
    price = Field()
    product_number = Field()
    list_price = Field()
    manufacturer = Field()
    oem = Field()
    department = Field()
    product_line = Field()
    uom = Field()
    obsolete = Field()
    ship_weight = Field()
    dimensions = Field()
    upc = Field()
    availability = Field()
    supercedes = Field()
    supercedes_date = Field()
    img_lrg = Field()
    branches = Field()
    image_urls = Field()
    images = Field()
    sku = Field()
    abbreviation = Field()

