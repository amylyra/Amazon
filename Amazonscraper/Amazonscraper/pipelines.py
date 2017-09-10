# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem

class AmazonscraperPipeline(object):

    def __init__(self):
        self.amazon_seen = set()

    def process_item(self, item, spider):
        amazonASIN = (item['ASIN'] if item['ASIN'] else '')
        if amazonASIN in self.amazon_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.amazon_seen.add(amazonASIN)
            return item