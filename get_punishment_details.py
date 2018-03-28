#-*- coding:utf-8 -*-

import os
import shutil
import subprocess

from get_dynamic_html import get_js_html,download_js
from bs4 import BeautifulSoup
from urlparse import urljoin
import re
from db_api import Punishment,func

import urllib2

HEADERS = {
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20180201 Firefox/57.0 ',
    'Referer': "http://www.pbc.gov.cn"
}

root_path = r'/home/xudi/tmp/punishment_source'
download_path = r'/home/xudi/tmp/selenium_download'

get_city = lambda x: x.split('-')[0]
is_doc_url = lambda x: x.endswith('.doc') or x.endswith('.docx') or x.endswith('.xls') \
                    or x.endswith('.xlsx') or x.endswith('.pdf')

content_pattern = re.compile(r'[Cc]ontent-[Tt]ype:\s*([a-zA-Z]+/[a-zA-Z\-]+)')
delete_span = re.compile(ur'<span[^>]*>(.*?)</span>')
#html = delete_span.sub(lambda x: x.group(1),html )
public_table_kw = re.compile(ur'违法行为\s*(类型|内容){0,1}')
link_kw = re.compile(ur'(行政){0,1}处罚(信息){0,1}(公示表|公示|表){0,1}')
href_kw = re.compile(ur'.(xls|xlsx|doc|docx|pdf)$')
img_kw  = re.compile(ur'.(tif|jpg|jpeg|bmp)$')

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
    content_type = get_content_type(real_url)
    print text,page_url,real_url,content_type
    download_js(page_url,text,content_type)
    shutil.move(os.path.join(download_path,fname), outfile_path)
    
def create_punishment_fiels(dbapi,city,des_path):
    session = dbapi.get_session()
    cursor  = session.query(dbapi.table_struct).filter_by(city = city).all()
    count = session.query(func.count(dbapi.table_struct.index)).filter_by(city = city).scalar()
    session.close()
    print city,count
    cnt = 0
    city_root_url = 'http://{}.pbc.gov.cn'.format(city)
    for record in cursor:
        print cnt
        cnt += 1
        #case 1: is excel or doc, like tianjing
        if is_doc_url(record.punishment_item_url):
            real_url = '/'.join(record.punishment_item_url.split('//')[-1].split('/')[1:])
            print record.punishment_item_url
            this_soup = BeautifulSoup(record.publication_url,'lxml')
            this_tag = this_soup.find('a',attrs = {'href',real_url})
            text = this_tag.get_text()
            fname = real_url.split('/')[-1]
            dump_doc(record.publication_url,des_path,text,fname,record.index,record.punishment_item_url,record.update_date)
            continue
        public_html = get_js_html(record.punishment_item_url)
        soup = BeautifulSoup(public_html,'lxml')
        tag = soup.find(['p','span','td'],text = public_table_kw)
        link_tag  = soup.find('a',text = link_kw,attrs={'href':href_kw})
        img_tag   = soup.find('a',attrs={'href':img_kw})
        #case 2: is table , like beijing
        if tag:
            print 'table = ',record.punishment_item_url
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
            print 'link = ',real_link
            text = link_tag.get_text()
            fname = link_url.split('/')[-1]
#             print record.punishment_item_url,des_path,text,fname,record.update_date,record.punishment_item_url
            dump_doc(record.punishment_item_url,des_path,text,fname,record.index,real_link,record.update_date)
            continue
        elif img_tag:
            print 'img, skipped'
            continue
        #case 4: here warning
        print '[Error] ---> ',city,' ',record.punishment_item_url

def test_html():
    html = '''
    <table border="1" cellpadding="0" cellspacing="0" style="border-bottom: medium none; border-left: medium none; border-collapse: collapse; margin-left: 0px; border-top: medium none; border-right: medium none; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt; mso-padding-alt: 0pt 5.4pt 0pt 5.4pt; mso-table-layout-alt: fixed">
 <tbody>
  <tr>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 38.95pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 宋体; font-size: 14pt; mso-ascii-font-family: Times New Roman">
      序号
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 103.1pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 宋体; font-size: 14pt; mso-ascii-font-family: Times New Roman">
      企业名称
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 94.85pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 宋体; font-size: 14pt; mso-ascii-font-family: Times New Roman">
      处罚决定书
     </span>
    </p>
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 宋体; font-size: 14pt; mso-ascii-font-family: Times New Roman">
      文号
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 92.5pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 宋体; font-size: 14pt; mso-ascii-font-family: Times New Roman">
      违法行为
     </span>
    </p>
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 宋体; font-size: 14pt; mso-ascii-font-family: Times New Roman">
      类型
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 宋体; font-size: 14pt; mso-ascii-font-family: Times New Roman">
      行政处罚内容
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 宋体; font-size: 14pt; mso-ascii-font-family: Times New Roman">
      作出行政处罚决定机关名称
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 宋体; font-size: 14pt; mso-ascii-font-family: Times New Roman">
      作出行政处罚决定日期
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 81pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 宋体; font-size: 14pt; mso-ascii-font-family: Times New Roman">
      备注
     </span>
    </p>
   </td>
  </tr>
  <tr>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 38.95pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: Times New Roman; font-size: 14pt; mso-ascii-font-family: Times New Roman; mso-fareast-font-family: 宋体">
      1
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 103.1pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312; mso-bidi-font-family: 仿宋_GB2312">
      上汽通用汽车金融
     </span>
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      公司
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 94.85pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿��_GB2312">
      上海银罚字[2015]2号
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 92.5pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      违反存款准备金管理规定
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-justify: inter-ideograph; text-align: justify">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      罚款人民币50万元
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      中国人民银行上海分行
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312; mso-fareast-font-family: 仿宋_GB2312">
      2015年2月4日
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 81pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
    </p>
   </td>
  </tr>
  <tr>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 38.95pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: Times New Roman; font-size: 14pt; mso-ascii-font-family: Times New Roman; mso-fareast-font-family: 宋体">
      2
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 103.1pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      上海奉贤浦发村镇银行股份有限公司
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 94.85pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      上海银罚字[2015]3号
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 92.5pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      违反存款准备金管理规定
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      罚款人民币98400元
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      中国人民银行上海分行
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312; mso-fareast-font-family: 仿宋_GB2312">
      2015年2月4日
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 81pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
    </p>
   </td>
  </tr>
  <tr>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 38.95pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: Times New Roman; font-size: 14pt; mso-ascii-font-family: Times New Roman; mso-fareast-font-family: 宋体">
      3
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 103.1pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="center">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      汇丰银行（中国）有限公司
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 94.85pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      上海银罚字[2015]4号
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 92.5pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      违反存款准备金管理规定
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      罚款人民币20万元
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      中国人民银行上海分行
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312; mso-fareast-font-family: 仿宋_GB2312">
      2015年2月4日
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 81pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
    </p>
   </td>
  </tr>
  <tr>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 38.95pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: Times New Roman; font-size: 14pt; mso-ascii-font-family: Times New Roman; mso-fareast-font-family: 宋体">
      4
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 103.1pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      西班牙桑坦德银行有限公司上海分行
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 94.85pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      上海银罚字[2015]17号
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 92.5pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      违反存款准备金管理规定
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      罚款人民币1000元
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      中国人民银行上海分行
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312; mso-fareast-font-family: 仿宋_GB2312">
      2015年5月28日
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 81pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
    </p>
   </td>
  </tr>
  <tr>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 38.95pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: Times New Roman; font-size: 14pt; mso-ascii-font-family: Times New Roman; mso-fareast-font-family: 宋体">
      5
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 103.1pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      渣打银行（中国）有限公司
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 94.85pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      上海银罚字[2015]18号
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 92.5pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      违反存款准备金管理规定
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      罚款人民币20万元
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312">
      中国人民银行上海分行
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 99pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
     <span style="font-family: 仿宋_GB2312; font-size: 12pt; mso-ascii-font-family: 仿宋_GB2312; mso-fareast-font-family: 仿宋_GB2312">
      2015年5月28日
     </span>
    </p>
   </td>
   <td style="border-bottom: windowtext 1pt solid; border-left: windowtext 1pt solid; padding-bottom: 0pt; padding-left: 5.4pt; width: 81pt; padding-right: 5.4pt; border-top: windowtext 1pt solid; border-right: windowtext 1pt solid; padding-top: 0pt; mso-border-top-alt: solid windowtext 0.5pt; mso-border-left-alt: solid windowtext 0.5pt; mso-border-bottom-alt: solid windowtext 0.5pt; mso-border-right-alt: solid windowtext 0.5pt" valign="top">
    <p class="MsoNormal" style="text-align: center">
    </p>
   </td>
  </tr>
 </tbody>
</table>
'''
    #     html = delete_span.sub(lambda x: x.group(1),html )
    soup = BeautifulSoup(html,'lxml')
    soup = strip_tags(soup, ['span','p'])
    print soup.prettify()
    tag = soup.find('span',text = public_table_kw)
    link_tag  = soup.find('a',text = link_kw,attrs={'href':href_kw})
#     print tag
    table_tag = tag.find_parent('table')
    print table_tag.prettify()
    
def get_punish_table():
    dbapi = Punishment()
    dbapi.create_table()
    ss = dbapi.get_session()
    cursor = ss.query(dbapi.table_struct.city).group_by(dbapi.table_struct.city).all()
    cities = [i.city for i in cursor]
    ss.close()
    cities = ['shanghai',]
    print cities
    for city in cities:
        des_path = os.path.join(root_path,city)
        if not os.path.exists(des_path):
            os.makedirs(des_path)
        create_punishment_fiels(dbapi,city,des_path)

def test_download():
    url = r'http://shanghai.pbc.gov.cn/fzhshanghai/113577/114832/114918/3008150/index.html'
    download_js(url, u'（第13期）行政处罚信息公示表.pdf', 'application/octet-stream')


if __name__ == '__main__':
#     test_html()
#     get_punish_table()
#     test_content_type()
    test_download()

    