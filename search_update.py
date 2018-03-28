#-*- coding:utf-8 -*-

from get_item_urls import crawler

update_date = 20180301

if __name__ == '__main__':
    print crawler(mode = 'update', update_date = update_date)