# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WalgreensItem(scrapy.Item):
    
    Product_name = scrapy.Field()
    category = scrapy.Field()
    skuId = scrapy.Field()
    upc = scrapy.Field()
    wicId = scrapy.Field()
    sizeCount = scrapy.Field()
    productId = scrapy.Field()
    productImageUrl = scrapy.Field()
    brandName = scrapy.Field()
    regularPrice = scrapy.Field()
    Review = scrapy.Field()
    warnings = scrapy.Field()
    ingredients = scrapy.Field()
    description = scrapy.Field()
    ProductPageUrl = scrapy.Field()
    ReviewText = scrapy.Field()
