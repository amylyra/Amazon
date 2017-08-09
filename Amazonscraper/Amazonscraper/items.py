# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AmazonscraperItem(scrapy.Item):
    # define the fields for your item here like:
    Product_Name = scrapy.Field()
    Brand_Name = scrapy.Field()
    Category = scrapy.Field()
    Ranking = scrapy.Field()
    Rating = scrapy.Field()
    Reviews = scrapy.Field()
    ASIN = scrapy.Field()
    Price = scrapy.Field()
    Description = scrapy.Field()
    Benefits = scrapy.Field()
    Suggested_Use = scrapy.Field()
    Consumer_Reviews = scrapy.Field()
    ReviewSummary = scrapy.Field()
    Page_url = scrapy.Field()