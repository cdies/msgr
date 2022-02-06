# -*- coding: utf-8 -*-
import sys
import scrapy
from scrapy.http import Request
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sqlite3
import os
import time
import re

# класс скачивает ссылки на все аукцоны из msgr.ru и сохраняет в бд sqlite3
class MsgrSpider(scrapy.Spider):
    name = 'msgr_parser'
    allowed_domains = ['msgr.ru']

    def __init__(self, db_connect, start_url):
        self.logging('######## start msgr.ru ########') 

        # http://www.msgr.ru/ru/results?items_per_page=All
        self.start_urls = [start_url]

        con = sqlite3.connect(db_connect)
        cur = con.cursor()

        # таблица ссылок аукционов
        query = ('CREATE TABLE IF NOT EXISTS auctions('
            'link TEXT,'
            'date TEXT,'
            'adress TEXT,'
            'type_of TEXT,'
            'rooms TEXT,'
            'room_for_sale TEXT,'
            'square TEXT,'
            'living_space TEXT,'
            'portion TEXT,'
            'price TEXT,'
            'deposit TEXT,'
            'step TEXT,'
            'UNIQUE(date, adress));')
        cur.execute(query)

        # таблица ссылок на прошедшие аукционы
        query = ('CREATE TABLE IF NOT EXISTS past_auctions('
            'date TEXT,'
            'adress TEXT,'
            'rooms TEXT,'
            'square TEXT,'
            'living_space TEXT,'
            'begin_price TEXT,'
            'final_price TEXT,'
            'UNIQUE(date, adress));')
        cur.execute(query)

        self.cur = cur
        self.con = con
        
        
    def parse(self, response):
        # ссылки на страницы с данными об аукционах
        auctions = response.xpath('//nav[@id="block-category"]/ul/li/a/@href').extract()
        auctions = set(['http://www.msgr.ru' + i for i in auctions if 'auction' in i])

        # ссылки на страницы с данными об прошедших аукционах
        past_auctions = response.xpath('//div[@class="views-element-container"]//div[@class="view-content"]//a/@href').extract()
        past_auctions = set(['http://www.msgr.ru' + i for i in past_auctions])


        for page in auctions:
            yield Request(page, callback=self.parse_auctions)

        for page in past_auctions:
            yield Request(page, callback=self.parse_past_auctions)


    def parse_auctions(self, response):
        self.logging('<< ' + response.url)
        query = "INSERT INTO `auctions` VALUES (?,?,?,?,?,?,?,?,?,?,?,?);"

        date = response.xpath('//div[@class="field__item"]/time/text()')[-1].extract()

        table = response.xpath('//div[@class="view-content"]/table/tbody/tr') 
        for i in table:
            td = i.xpath('td')   
            link = 'http://www.msgr.ru' + td[1].xpath('div/a/@href').extract_first()
            address = self.make_text(td[1])
            type_of = self.make_text(td[2])
            rooms = self.make_text(td[3])
            room_for_sale = self.make_text(td[4])
            square = self.make_text(td[5])
            livig_space = self.make_text(td[6])
            portion = self.make_text(td[7])
            price = re.sub(r'\s+', '', self.make_text(td[8]))
            deposit = re.sub(r'\s+', '', self.make_text(td[9]))
            step = re.sub(r'\s+', '', self.make_text(td[10]))


            data = (link, date, address, type_of, rooms, room_for_sale, square,
                    livig_space, portion, price, deposit, step)

            self.cur.execute(query, data)

            self.con.commit()

    def parse_past_auctions(self, response):
        self.logging('<< ' + response.url)
        query = "INSERT INTO `past_auctions` VALUES (?,?,?,?,?,?,?);"

        date = response.xpath('//time/text()').extract_first()

        table = response.xpath('//div[@class="region region-content"]//table/tbody/tr')[1:]
        for i in table:
            td = i.xpath('td')
            address = self.make_text(td[1])
            rooms = self.make_text(td[2])
            square = self.make_text(td[3])
            if len(td) == 7: # старый формат до 2021-03-03
                livig_space = self.make_text(td[4])
                begin_price = re.sub(r'\s+', '', self.make_text(td[5]))
                final_price = re.sub(r'\s+', '', self.make_text(td[6]))
            else:
                livig_space = square
                begin_price = re.sub(r'\s+', '', self.make_text(td[4]))
                final_price = re.sub(r'\s+', '', self.make_text(td[5])) 

            data = (date, address, rooms, square, livig_space, begin_price, final_price)

            self.cur.execute(query, data)

            self.con.commit()


    def make_text(self, td):
        text = td.xpath('text() | *//text()').extract()
        if len(text) != 0:
            text = ''.join(text)
            text = text.strip()
        else:
            text = ''
        return text


    def logging(self, text):
        print(text)
        with open('logs.txt', 'a') as f:
            f.write(text + '\n')


    # закрывай коннект с бд
    def __del__(self):
        self.cur.close()
        self.con.close()


def main():
    if not os.path.exists('db'):
        os.makedirs('db')

    db_connect = 'db/' +  time.strftime('%Y-%m-%d_%H%M%S', time.gmtime()) + '.db'
    start_url = 'http://www.msgr.ru/ru/results?items_per_page=All'
        
    settings = get_project_settings()
    settings['RETRY_TIMES'] = 5
    settings['DOWNLOAD_DELAY'] = 0.2
    settings['LOG_LEVEL'] = 'WARNING'
    settings['LOG_FILE'] = 'logs.txt'

    process = CrawlerProcess(settings)
    process.crawl(MsgrSpider, db_connect=db_connect, start_url=start_url)
    process.start()

if __name__ == "__main__":
    main()