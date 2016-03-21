# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import scrapy
import hashlib
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
from pprint import PrettyPrinter as pp

class ScpScrapperPipeline(object):
    def process_item(self, item, spider):
        return item


class ScpScrapperImagePipeline(ImagesPipeline):


    def file_path(self, request, response=None, info=None):
        url = request.url
        alt = url.rsplit('/', 1)[1].split('.')[0]
        image_guid = request.meta.get('sku', alt)
        abbr = request.meta['abbreviation']
        path_format = 'full/{1}/{0}.jpg'
        file_name = image_guid
        path = path_format.format(file_name, abbr)
        # used to check if the file already exists
        working_dir = os.getcwd() + '/images/'
        full_path = working_dir + path
        request.meta['file_name'] = file_name
        return path

    def thumb_path(self, request, thumb_id, response=None, info=None):
        #print(request.meta['file_name'])
        image_guid = request.meta['file_name']
        # check if image already exists and add some random char to the file name
        path_format = 'thumb/{2}/{0}/{1}_{0}.jpg'
        return path_format.format(thumb_id, image_guid, request.meta['abbreviation'])

    def get_media_requests(self, item, info):
        for image_url in item['image_urls']:
            yield scrapy.Request(image_url, meta=item)
        for part in item['parts']:
            for image_url in part['image_urls']:
                yield scrapy.Request(image_url, meta=part)
