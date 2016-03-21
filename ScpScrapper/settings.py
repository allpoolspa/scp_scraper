# -*- coding: utf-8 -*-

# Scrapy settings for ScpScrapper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#
import os

BOT_NAME = 'ScpScrapper'
DOWNLOADER_MIDDLEWARES = {
        'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware' : None,
        'ScpScrapper.comm.rotate_useragent.RotateUserAgentMiddleware' :400
    }
SPIDER_MODULES = ['ScpScrapper.spiders']
NEWSPIDER_MODULE = 'ScpScrapper.spiders'
LOG_FILE = 'log.json'

FEED_FORMAT = 'json'
FEED_URI = 'scp.json'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'ScpScrapper (+http://www.yourdomain.com)'
ITEM_PIPELINES = {
    #'scrapy.pipelines.images.ImagesPipeline': 300,
    'ScpScrapper.pipelines.ScpScrapperImagePipeline': 1,
}
#IMAGES_STORE = 'images' # local image store
IMAGES_STORE = 's3://scppics/' # AMAZON S3
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
