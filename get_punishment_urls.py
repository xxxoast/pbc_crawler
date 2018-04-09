# -*- coding:utf-8 -*- 
import os
import time
import re
import threading

# coding : cp936
import requests
from urlparse import urljoin
from get_dynamic_html import get_js_html,download_js
from bs4 import BeautifulSoup
from sqlalchemy.sql import func

unicode2utf8 = lambda x: x.encode('utf8') if isinstance(x,unicode) else x
dates_trans = lambda x: ''.join(x.split('-'))

#init 
key_word_outer = '政务公开目录'
key_word_inner = re.compile(ur'行政处罚(公示){0,1}')
key_word_punish = re.compile(ur'(((行政){0,1}(处罚|执法)(的)*(信息){0,1}(公示|公示表|表)[\s]*)|([1-9]+号))')
key_word_date  = re.compile(ur'^20[0-9]{2}-[0-9]{1,2}-[0-9]{1,2}$')
    
HEADERS = {
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0 ',
    'Referer': "http://www.pbc.gov.cn"
}

def generate_branch_list():
    pbcurl = r'http://www.pbc.gov.cn/rmyh/105226/105442/index.html'
    html = get_js_html(pbcurl)
    soup = BeautifulSoup(html, 'lxml').find_all('table')
    branch_table = soup[63]
    atags = branch_table.find_all('a')
    with open('branch_list.txt','w+') as fout:
        for atag in atags:
            fout.write(atag.get('href'))
            fout.write('\n') 

def find_public_page(root_url,update_date ):
    #get main page
    download_urls = []
    main_page = get_js_html(root_url)
    soup = BeautifulSoup(main_page, 'lxml')
    # find 公开目录
    public_xml = soup.find_all('a',text = key_word_outer )
    if len(public_xml) <= 0:
        return '',[]
    public_url = urljoin(root_url,public_xml[0].get('href'))
    print 'public_url = ',public_url
    # find 处罚公示
    punish_page = get_js_html(public_url)
    punish_soup = BeautifulSoup(punish_page,'lxml')
    punish_xml = punish_soup.find_all('a',text = key_word_inner)
    if len(punish_xml) <= 0:
        return '',[]
    punish_url = urljoin(root_url,punish_xml[0].get('href'))
    print 'punish_url = ',punish_url
    item_list_page = get_js_html(punish_url)
    item_list_soup = BeautifulSoup(item_list_page,'lxml')
    #condition 有表有日期
    punish_items_tr = [ i.parent for i in item_list_soup.find_all('td',text = key_word_punish) if i.parent and i.find('a') ]
    punish_items_tr = filter(lambda i:i.find('td',text = key_word_date),punish_items_tr)
    #three key elements
    punish_items = [ i.find('a',text = key_word_punish).get('href') for i in punish_items_tr]
    punish_dates = [ i.find('td',text = key_word_date).text for i in punish_items_tr]
    punish_pages = [ punish_url ] * len(punish_items)
    
    # recursively get next page
    next_page_tag = item_list_soup.find('a',text = '下一页')
    while next_page_tag and ( ('href' in next_page_tag.attrs) or ('tagname' in next_page_tag.attrs) ):
        #increasement update
        if update_date is not None:
            if len(punish_dates) <= 0:
                break
            last_date = punish_dates[-1]
            if last_date < update_date:
                break
        #special case for chongqing
        if ('href' in next_page_tag.attrs):
            next_url = urljoin(root_url,next_page_tag.get('href'))
        if ('tagname' in next_page_tag.attrs):
            #special case for chongqing
            if next_page_tag.get('tagname').startswith('['):
                break
            next_url = urljoin(root_url,next_page_tag.get('tagname'))
        next_page = get_js_html(next_url) 
        next_soup = BeautifulSoup(next_page,'lxml')
        
        next_punish_items_tr = [ i.parent for i in next_soup.find_all('td',text = key_word_punish) if i.parent and i.find('a')]
        next_punish_items_tr = filter(lambda i:i.find('td',text = key_word_date),next_punish_items_tr)
        next_punish_items = [ i.find('a',text = key_word_punish).get('href') for i in next_punish_items_tr]
        next_punish_dates = [ i.find('td',text = key_word_date).text for i in next_punish_items_tr]
        
        punish_items.extend(next_punish_items)
        punish_dates.extend(next_punish_dates)
        punish_pages.extend([next_url] * len(next_punish_dates))
        next_page_tag = next_soup.find('a',text = '下一页')
         
#         print 'next_page_tag = ',next_page_tag
    #urljoin
    for punish_page,punish_item,punish_date in zip(punish_pages,punish_items,punish_dates):
        punish_url = urljoin(root_url,punish_item)
        #to make it more safe
        if punish_url != punish_page:
            download_urls.append((punish_page,punish_url,punish_date))          
    if len(download_urls) <= 0:
        print 'Failed = ',root_url
        return []
    return download_urls
    
    
def valid_city(city,include,exclude):
    if len(include) > 0:
        return True if city in include else False
    if len(exclude) > 0:
        return True if city not in exclude else False
    return True

def crawler(include = [],exclude = [],init = False):
    from db_api import Punishment
    dbapi = Punishment()
    dbapi.create_table()
    new_items = {}
    with open('branch_list.txt','r') as fin:
        for url in fin:
            city = url.split(r'//')[-1].split('.')[0]
            if not valid_city(city,include,exclude):
                continue
            print city
            new_items[city] = []
            if init:
                download_urls = find_public_page(url,update_date = None)
                des_path = '/home/xudi/tmp/pbc_punishment'
                des_path = os.path.join(des_path, '-'.join((city , str(len(download_urls)))))
                with open(des_path,'w+') as fout:
                    for (punish_page,punish_url,punish_date) in download_urls:
                        s = ' '.join((city,url.strip(),punish_page.strip(),punish_url.strip(),dates_trans(punish_date)))
                        fout.write(unicode2utf8(s))
                        fout.write('\n')
            else:
                ss = dbapi.session()
                max_count = ss.query(func.max(dbapi.table_struct.index)).filter_by(city = city).scalar() + 1
                record = ss.query(dbapi.table_struct.update_date).filter_by(city = city).order_by(dbapi.table_struct.update_date.desc()).first()
                print max_count,record.update_date
                download_urls = find_public_page(url,record.update_date)
                for (punish_page,punish_url,punish_date) in download_urls:
                    used_to = ss.query(dbapi.table_struct).filter_by(punishment_item_url = punish_url.strip()).scalar()
                    if used_to is None:
                        dbapi.insert_listlike(dbapi.table_struct,(city,url.strip(),punish_page.strip(),punish_url.strip(),dates_trans(punish_date),max_count + 1))
                        new_items[city].append((city,url.strip(),punish_page.strip(),punish_url.strip(),dates_trans(punish_date),max_count + 1))
                        max_count += 1 
                ss.close()
    if init:
        from db_api import init_punishment_table as init_table
        init_table()
    return new_items
    
def regex_soup_test():
    html = ''' '''
    soup = BeautifulSoup(html,'lxml')
    key_word_punish = re.compile(ur'(((行政){0,1}处罚(的)*(信息){0,1}(公示|公示表|表))|(第{0,1}[0-9]+号))')
    key_word_date  = re.compile(ur'20[0-9]{2}-[0-9]{1,2}-[0-9]{1,2}')
    
    punish_items_tr = [ i.parent for i in soup.find_all('td',text = key_word_punish) if i.parent ]
    punish_items_tr = filter(lambda i:i.find('td',text = key_word_date),punish_items_tr)
    punish_items = [ i.find('a',text = key_word_punish).get('href') for i in punish_items_tr]
    punish_dates = [ i.find('td',text = key_word_date).text for i in punish_items_tr]
    print punish_items,punish_dates
           
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-init','--init', dest='init', action='store_true', default=False)
    parser.add_argument('-include','--include', dest='include', nargs='*', default = [])
    parser.add_argument('-exclude','--exclude', dest='exclude', nargs='*', default = [])
    args = parser.parse_args()
    arg_dict = vars(args)
    print arg_dict
    crawler(include = arg_dict['include'],\
            exclude = arg_dict['exclude'],\
            init = arg_dict['init'])


    
