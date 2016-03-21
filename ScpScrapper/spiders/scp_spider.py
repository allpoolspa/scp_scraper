# This program crawls the Scp sites, generally we only scrap a certain
# manufacturers product list. It grabs the product information, which can be
# seen in items.py, while getting the availability at each SCP/Superior branch.
# It uses Scrapy and Selenium. We use selenium due to some javascript loaded data,
# namely the branches and availabilty information.

# HOW IT WORKS:
# This is a CrawlSpider that logins into the pool360 website, then
# using the rules it goes to each product link for each page and grabs
# the relevant information and goes to the next page in the product
# search results. We use a Firefox webdriver for the selenium app.


import time
import logging
from os import environ as ev
from scrapy import log
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector
from ScpScrapper.items import ScpScrapperItem
from scrapy.spider import BaseSpider
from scrapy.http import Request, FormRequest, HtmlResponse
from scrapy.item import Item, Field

from selenium import webdriver
from selenium import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LoginSpider(CrawlSpider):

    MANUFACTURER = 'ABCO'
    name = 'scp'
    #aladdin
    start_urls=['https://pool360.poolcorp.com/search.aspx?searchterm=%23all&r=%2bTop%2fmanufacturers%2fabco+distributors']
    #start_urls = ['https://pool360.poolcorp.com/Products/SearchResults/tabid/89/language/en-US/Default.aspx?q=%23all&r=%2bTop%2fmanufacturers%2fhayward+pool+products']
    login_page = 'https://pool360.poolcorp.com/signin.aspx'
    rules = (
        # Extract product links so that parse_items can scrap the appropriate data for each product.
        Rule(SgmlLinkExtractor(restrict_xpaths=('//span[@class="ProductName"]/a[@class="ProductTitle"]',)), callback='parse_items', follow=True),

        # Extract links so that the web crawler can move to the next page.
        Rule(SgmlLinkExtractor(restrict_xpaths=('//div[@class="TopPager"]/ol[@class="PageNavigation"]/li[@class="next"]/a[@class="ActivePager"]',))),
    )

    def __init__(self):
        CrawlSpider.__init__(self)
        self.log = logging.getLogger('scpLogger')
        self.driver = webdriver.Firefox()

    def __del__(self):
        self.driver.close()
        CrawlSpider.__del__(self)

    def start_requests(self):
        """Starts the login process."""
        self.log.info(" Beginning Login")
        yield Request(
            url=self.login_page,
            callback=self.login,
            dont_filter=True
        )

    def login(self, response):
        """Login with both the selenium and scrapy app."""
        self.driver.get(response.url)
        WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(
                (By.NAME, "ctl00$PageContent$ctl00$ctrlLogin$UserName")
            )
        )
        username = self.driver.find_element_by_name('ctl00$PageContent$ctl00$ctrlLogin$UserName')
        password = self.driver.find_element_by_name('ctl00$PageContent$ctl00$ctrlLogin$Password')
        username.clear()
        password.clear()
        username.send_keys(ev['SCP_USERNAME'])
        password.send_keys(ev['SCP_PW'])
        self.driver.find_element_by_name('ctl00$PageContent$ctl00$ctrlLogin$LoginButton').click()

        WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[@id='cusName']")
            )
        )
        url = self.driver.current_url
        cookies = self.driver.get_cookies()
        return Request(self.start_urls[0], cookies=cookies)

    def after_login(self, response):
        """This makes sure that we logged into the pool360 website.
        We only check the scrapy app at this time. To be a complete check
        we will have to add a check for the selenium app.
        """
        print 'Hello'
        hxs = Selector(response)
        if 'Logout' not in response.body:
            self.log.info("Login failed")
            print response.body
            return
        self.log.info('Logged in.')
        return Request(
            url=self.start_urls[0],
        )

    def parse_items(self, response):
        """This gets the product info that we need from the products
        page. It calls _get_availability(), which selenium handles.
        """
        hxs = Selector(response)
        item = ScpScrapperItem()
        #Get the fields we need
        try:
            item['price'] = hxs.xpath('//span[@class="priceValue"]/text()').extract()[0]
        except KeyError:
            self.log.info('Unable to find price')
        try:
            item['title'] = hxs.xpath('normalize-space(//table[@id="tblproductInfo"]//td[2]/h6/text())').extract()[0]
        except KeyError:
            self.log.info('Unable to find title')
        try:
            product_info = hxs.xpath('//ul[@class="productListInfo"]/li')
        except KeyError:
            self.log.info('Unable to find product list')
        #A dictionary that maps the website ids with the items.py ids.
        info_mapper = {
            'product #': 'product_number',
            'list price': 'list_price',
            'mfg': 'manufacturer',
            'mfg #': 'oem',
            'department': 'department',
            'product line': 'product_line',
            'uom': 'uom',
            'obsolete': 'obsolete',
            'ship weight (lbs)': 'ship_weight',
            'dimensions': 'dimensions',
            'supercedes': 'supercedes',
            'supercedes date': 'supercedes_date',
            'upc code': 'upc'
        }
        for info in product_info:
            try:
                key, value = info.xpath('normalize-space(text())').extract()[0].split(':')
                key = key.strip().lower()
                value = value.strip()
                try:
                    if key == 'mfg':
                        item['manufacturer'] = self.get_manufacturer(value)
                        print item['manufacturer']
                    else:
                        item[info_mapper[key]] = value
                except:
                    pass
            except KeyError:
                self.log.info('Unable to find {}'.format(info))

        item['image_urls'] = self.safe_get_info("//a[@id='productlb']", "href")
        item['branches'] = self._get_availability(response)
        manufacturer = item.get('manufacturer', self.MANUFACTURER)
        item['sku'] = self.make_sku(
            manufacturer,
            item.get('oem', item.get('upc'))
        )
        item['abbreviation'] = self.get_abbreviation(manufacturer)
        yield item

    def get_abbreviation(self, manufacturer):
        chars_to_remove = ['.','-',' ']
        clean_manufacturer = manufacturer.translate(
            None, ''.join(chars_to_remove)
        ).lower()
        return clean_manufacturer[:3].upper()

    def make_sku(self, manufacturer, part_number):
        return self.get_abbreviation(manufacturer) + "_" + part_number

    def _get_availability(self, response):
        """This table is generated by javascript, so we need selenium
        to get the fields. We grab the branches and availability quantity
        at each branch.
        """
        self.driver.get(response.url)
        time.sleep(2.5)
        try:
            branch_quantity = self.driver.find_elements_by_xpath('//table[@class="productAvailData"]//tr')
        except KeyError:
            self.log.info('Unable to find table')
        branches_list = [branch.text for branch in branch_quantity]
        branches_dict = {}
        for info in branches_list:
            if ':' in info:
                branch, quantity = info.split(':')
                branches_dict[branch] = quantity
        return branches_dict

    def safe_get_info(self, xpath, attribute, root=None):
        self.driver.implicitly_wait(1)
        try:
            if root:
                return str(
                    root.find_element_by_xpath(xpath).get_attribute(attribute)
                )
            return str(
                self.driver.find_element_by_xpath(
                    xpath
                ).get_attribute(attribute)
            )
        except:
            self.log.info(
                "Can't get {} with xpath {} ".format(attribute, xpath)
            )
            return None

    def get_manufacturer(self, manufacturer):
        chars_to_remove = ['.','-',' ']
        manufacturers = {
            'oreq' : 'Oreq',
            'aquachek' : 'Aquachek',
            'game' : 'GAME',
            'unicel' : 'Unicel',
            'valpak' : 'Val-Pak',
            'usseal' : 'US Seal',
            'aladdin' : 'Aladdin',
            'waterway' : 'Waterway',
            'zodiac' : 'Zodiac',
            'pentair' : 'Pentair',
            'hayward' : 'Hayward',
            'srsmith' : 'S.R. Smith',
            'aosmith' : 'A.O. Smith',
            'afrasindustries' : 'Afras Industries',
            "odyssey" : "Odyssey",
            "raypak" : "Raypak",
            "polaris" : "Polaris",
            "jandy" : "Jandy",
            "custommoldedproducts": "Custom Molded Products"
        }
        clean_manufacturer = manufacturer.translate(
            None, ''.join(chars_to_remove)
        ).lower()
        try:
            return manufacturers[clean_manufacturer]
        except:
            for key, man in manufacturers.items():
                if key in clean_manufacturer:
                    return man
        return manufacturer

