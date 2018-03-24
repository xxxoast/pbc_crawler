#-*- coding:utf-8 -*-

import os
import pandas as pd

from web_proxy_selenium import get_js_html
from bs4 import BeautifulSoup
from urlparse import urljoin
import requests
import re

HEADERS = {
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0 ',
    'Referer': "http://news.cnphotos.net/pic/nude/20060727/024438.html"
}

# src_path = r'/home/xudi/tmp/pbc_punishment3'
src_path = r'/home/xudi/tmp/punishment_test'
des_path = r'/home/xudi/tmp/punishment_source'

get_city = lambda x: x.split('-')[0]
is_doc_or_excel = lambda x: x.endswith('.doc') or x.endswith('.docx') or x.endswith('.xls') or x.endswith('.xlsx')

link_kw = re.compile(ur'(行政){0,1}处罚(信息){0,1}(公示表|公示|表)')
cnt = 0

def dump_doc(doc_url,des_dir):
    global cnt
    outfile = requests.get(doc_url,headers=HEADERS, timeout=10)
    suffix   = doc_url.split('.')[-1]
    outfile_name = '.'.join((str(cnt),suffix))
    outfile_path = os.path.join(des_dir,outfile_name)
    cnt += 1
    with open(outfile_path, 'ab') as fout:
        fout.write(outfile.content)
    
def create_punishment_fiels(sfname,des_dir,city):
    with open(sfname) as fin:
        global cnt
        cnt = 0
        root_url = 'http://{}.pbc.gov.cn/'.format(city)
        for public_url in fin:
            print cnt,public_url
            #is excel or doc, like tianjing
            if is_doc_or_excel(public_url):
                dump_doc(public_url,des_dir)
                continue
            public_html = get_js_html(public_url)
            soup = BeautifulSoup(public_html,'lxml')
            table_tags = soup.find_all('table',text = '行政处罚内容')
            link_tags  = soup.find_all('a',text = link_kw)
            #is table , like beijing
            if len(table_tags) > 0:
                outfile_name = '.'.join(str(cnt),'.txt')
                outfile_path = os.path.join(des_dir,outfile_name)
                cnt += 1
                with open(outfile_path, 'ab') as fout:
                    fout.write(table_tags.get_text())
            #is link, like shanghai
            else:
                for link_tag in link_tags:
                    link_url = link_tag['href']
                    doc_url  = urljoin(root_url,link_url)
                    dump_doc(doc_url,des_dir)
            
if __name__ == '__main__':
    for root, dirs, files in os.walk(src_path):
        for name in files:
            fname = os.path.join(root, name)
            city  = get_city(name)
            print city
            des_dir = os.path.join(des_path,city)
            if not os.path.exists(des_dir):
                os.makedirs(des_dir)
            create_punishment_fiels(fname,des_dir,city)
            