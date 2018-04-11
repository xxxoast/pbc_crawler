#-*- coding:utf-8 -*-

import os
import shutil
import subprocess
import re
import logging
import time

from get_dynamic_html import get_js_html,download_js
from bs4 import BeautifulSoup
from urlparse import urljoin
from db_api import Punishment,func,desc

HEADERS = {
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20180201 Firefox/57.0 ',
    'Referer': "http://www.pbc.gov.cn"
}

root_path = r'/media/xudi/coding/tmp/punishment_source'
download_path = r'/home/xudi/tmp/selenium_download'
log_path = r'/media/xudi/coding/tmp/log'

unicode2utf8 = lambda x: x.encode('utf-8') if isinstance(x,unicode) else x
unicode2cp936 = lambda x: x.encode('cp936') if isinstance(x,unicode) else x

content_pattern = re.compile(r'[Cc]ontent-[Tt]ype:\s*([a-zA-Z]+/[a-zA-Z\-]+)')
# delete_span = re.compile(ur'<span[^>]*>(.*?)</span>')
# html = delete_span.sub(lambda x: x.group(1),html )
link_kw = re.compile(ur'((行政){0,1}处罚(信息){0,1}){0,1}(公示表|公示|表){0,1}|([1-9]+\d*号)')
href_kw = re.compile(ur'.(xls|xlsx|doc|docx|pdf|tif|jpg|jpeg|bmp|wps|et)$')
# img_kw  = re.compile(ur'.(tif|jpg|jpeg|bmp)$')

get_city = lambda x: x.split('-')[0]
is_doc_url = lambda x: href_kw.search(x)

from misc import is_table_td
from misc import unicode2utf8

def alloc_logger(name, filename, mode = 'w',level=None, format=None):
    if level == None:
        level = logging.DEBUG
    if format == None:
        format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s Line:%(lineno)d %(message)s'
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.FileHandler(filename,mode = mode)
        handler.setFormatter(logging.Formatter(format))
        logger.handlers = [handler]
    return logger

logger = alloc_logger(__name__,log_path)

def get_content_type(url):    
    ret = subprocess.Popen(['curl','-I',url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    buf = ret.stdout.read().strip()
    matched = content_pattern.search(buf,re.I)
    if matched:
        return matched.group(1)
    else:
        return 'none'
    
def strip_tags(soup,invalid_tags):
    for tag in invalid_tags: 
        for match in soup.findAll(tag):
            match.replaceWithChildren()
    return soup

def dump_doc(page_url,des_path,text,fname,index,real_url,update_date):
    suffix = fname.split('.')[-1]
    outfile_name = '.'.join(('_'.join((str(index),str(update_date))),suffix))
    outfile_path = os.path.join(des_path,outfile_name)
    content_type = None
#     print text,page_url,real_url
    download_js(page_url,text,content_type)
    try:
        logger.info( ' '.join((text, fname)))
        shutil.move(unicode2utf8(os.path.join(download_path,fname)), outfile_path)
    except:
        print ' ---> [invalid LINK]: ', page_url,fname
        logger.error(unicode2utf8(u'invalid link = {} {}'.format(page_url,fname)))
    
def create_punishment_fiels(dbapi,city,des_path):
    session = dbapi.get_session()
    cursor  = session.query(dbapi.table_struct).filter_by(city = city)
    count = session.query(func.count(dbapi.table_struct.index)).filter_by(city = city).scalar()
    session.close()
    print city,count
    if count <= 0:
        return 
    print 'publication url = ',cursor.first().publication_url
    logger.info( unicode2utf8(u'publication url = {}'.format(cursor.first().publication_url)))
    has_download = set([ int(i.split('.')[0].split('_')[0])  for i in  \
                            filter(lambda x: not x.startswith('.'),os.listdir(os.path.join(root_path,city))) ])
    cnt = 0
    city_root_url = 'http://{}.pbc.gov.cn'.format(city)
    for record in cursor.all():
        if int(record.index) in has_download:
            continue
        print 'cnt = ',cnt,', index = ',record.index
        cnt += 1
        #case 1: is excel or doc, like tianjing
        if is_doc_url(record.punishment_item_url):
            logger.info( unicode2utf8(u'direct link = {}'.format(record.punishment_item_url)))
            real_url = '/' + '/'.join(record.punishment_item_url.split('//')[-1].split('/')[1:])
#             print record.publication_url,record.punishment_item_url,real_url
            publication_html = get_js_html(record.publication_url)
            this_soup = BeautifulSoup(publication_html,'lxml')
            this_tag = this_soup.find('a',attrs = {'href':real_url})
            text = this_tag.get_text()
            fname = real_url.split('/')[-1]
            dump_doc(record.publication_url,des_path,text,fname,record.index,record.punishment_item_url,record.update_date)
            continue
        public_html = get_js_html(record.punishment_item_url)
        soup = BeautifulSoup(public_html,'lxml')
#         tag = soup.find(['p','span','td'],text = public_table_kw)
        tags = soup.find_all(is_table_td)
        tag  = None
        if len(tags) > 0:
            tag = tags[-1]
        link_tag  = soup.find('a',text = link_kw,attrs={'href':href_kw})
#         case 2: is table , like beijing
        if tag:
            logger.info( unicode2utf8(u'table = {}'.format(record.punishment_item_url)))
            table_tag = tag.find_parent('table')
            soup = strip_tags(soup, ['span','p'])
            outfile_name = '.'.join(('_'.join((str(record.index),str(record.update_date))),'html'))
            outfile_path = os.path.join(des_path,outfile_name)
            if not os.path.exists(outfile_path):
                with open(outfile_path, 'ab') as fout:
                    fout.write(table_tag.prettify().encode('utf-8'))
            continue
        #case 3: is link, like shanghai
        elif link_tag:       
            link_url = link_tag['href']
            real_link = urljoin(city_root_url,link_url)
            logger.info( unicode2utf8(u'sub_link = {}'.format(real_link)))
            text = link_tag.get_text()
            fname = link_url.split('/')[-1]
#             print record.punishment_item_url,des_path,text,fname,record.update_date,record.punishment_item_url
            dump_doc(record.punishment_item_url,des_path,text,fname,record.index,real_link,record.update_date)
            continue
        #case 4: here warning
        print ' ---> [invalid PAGE]: ',city,' ',record.punishment_item_url
        logger.error(unicode2utf8(u'invalid page = {} {}'.format(city,record.punishment_item_url)))
        
def test_html():
    html = '''
    '''
    soup = BeautifulSoup(html,'lxml')
    tag = soup.find(is_table_td)
    print tag

def get_punish_table():
    dbapi = Punishment()
    dbapi.create_table()
    ss = dbapi.get_session()
    cursor = ss.query(dbapi.table_struct.city).group_by(dbapi.table_struct.city).all()
    cities = [i.city for i in cursor]
    ss.close()
    print cities
    for city in cities:
        des_path = os.path.join(root_path,city)
        if not os.path.exists(des_path):
            os.makedirs(des_path)
        create_punishment_fiels(dbapi,city,des_path)

def test_download():
    url = r'http://tianjin.pbc.gov.cn/fzhtianjin/113682/113700/113707/index.html'
    download_js(url, u'（第13期）行政处罚信息公示表.pdf', 'application/octet-stream')

if __name__ == '__main__':
    print '--->>> download details!'
    get_punish_table()

                
