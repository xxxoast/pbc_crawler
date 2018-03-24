# -*- coding:utf-8 -*- 
# coding=utf-8
import os
import time
import re
import threading

# coding : cp936
import requests
from urlparse import urljoin
from get_dynamic_html import get_js_html
from bs4 import BeautifulSoup

unicode2utf8 = lambda x: x.encode('utf-8') if isinstance(x,unicode) else x

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
            fout.write(atag['href'])
            fout.write('\n') 

def find_public_page(root_url):
    #get main page
    main_page = get_js_html(root_url)
    soup = BeautifulSoup(main_page, 'lxml')
    
    key_word_outer = '政务公开目录'
    key_word_inner = re.compile(ur'行政处罚(公示){0,1}')
    key_word_punish = re.compile(ur'(((行政){0,1}处罚(的)*(信息){0,1}(公示|公示表|表))|(第[0-9]+号))')
    has_found = False
    download_urls = []
    
    # find 公开目录
    public_xml = soup.find_all('a',text = key_word_outer )
    if len(public_xml) <= 0:
        continue
    public_url = urljoin(root_url,public_xml[0]['href'])
    print 'public_url = ',public_url
    public_page = get_js_html(public_url)
    punish_soup = BeautifulSoup(public_page,'lxml')
    # find 处罚公示
    punish_xml = punish_soup.find_all('a',text = key_word_inner)
    if len(punish_xml) <= 0:
        continue
    punish_url = urljoin(root_url,punish_xml[0]['href'])
    print 'punish_url = ',punish_url
    item_list_page = get_js_html(punish_url)
    item_list_soup = BeautifulSoup(item_list_page,'lxml')
    punish_items = item_list_soup.find_all('a',text = key_word_punish)
    next_page_tag = item_list_soup.find('a',text = '下一页')
    while 'href' in next_page_tag.attrs:
        next_url = urljoin(root_url,next_page_tag['href'])
        next_page = get_js_html(next_url) 
        next_soup = BeautifulSoup(next_page,'lxml')
        next_punish_items = next_soup.find_all('a',text = key_word_punish)
        punish_items.extend(next_punish_items)
        next_page_tag = next_soup.find('a',text = '下一页')
    if len(punish_items) <= 0:
        continue
    for punish_item in punish_items:
        des_url = urljoin(root_url,punish_item['href'])
        if des_url != punish_url:
            download_urls.append(des_url)
        has_found = True 
                            
    if not has_found:
        print 'Failed = ',root_url
        return []
    return download_urls
    
    
def valid_city(city,include,exclude):
    if len(include) > 0:
        return True if city in include else False
    if len(exclude) > 0:
        return True if city not in exclude else False
    return True

def crawler(include = [],exclude = []):
    with open('branch_list.txt','r') as fin:
        for url in fin:
            city = url.split(r'//')[-1].split('.')[0]
            print city
            if not valid_city(city,include,exclude):
                continue
            des_urls = find_public_page(url)
            print 'len(des_urls) = ', len(des_urls)
            des_path = '/home/xudi/tmp/pbc_punishment3'
            with open(os.path.join(des_path, '-'.join((city , str(len(des_urls))))),'w+') as fout:
                for i in des_urls:
                    fout.write(unicode2utf8(i))
                    fout.write('\n')

def test_single():
    url = 'http://haikou.pbc.gov.cn'
    city = url.split(r'//')[-1].split('.')[0]
    print city
    des_urls = find_public_page(url)
    print 'len(des_urls) = ', len(des_urls)
    des_path = '/home/xudi/tmp/test_single'
    with open(os.path.join(des_path, city),'w+') as fout:
        for i in des_urls:
            fout.write(unicode2utf8(i))
            fout.write('\n')


def regex_test():
    html = '''
    <table border="0" cellpadding="0" cellspacing="0" width="100%" align="center" opentype="page"> 
 <tbody> 
  <tr> 
   <td style="margin: 10px auto;">
    <table border="0" cellpadding="0" cellspacing="0" width="90%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
       <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/shenzhen/122811/122833/122840/3504041/index.html" onclick="void(0)" target="_blank" title="中国人民银行深圳市中心支行行政处罚公示表（2018年第51期）">中国人民银行深圳市中心支行行政处罚公示表（2018年第51期）</a></font></td> 
       <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-22</td> 
       <td class="hei12jj" height="40" valign="middle" align="left">&nbsp;</td> 
      </tr> 
     </tbody> 
    </table>
    <table border="0" cellpadding="0" cellspacing="0" width="90%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
       <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/shenzhen/122811/122833/122840/3501264/index.html" onclick="void(0)" target="_blank" title="中国人民银行深圳市中心支行行政处罚公示表（2018年第50期）">中国人民银行深圳市中心支行行政处罚公示表（2018年第50期）</a></font></td> 
       <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-19</td> 
       <td class="hei12jj" height="40" valign="middle" align="left">&nbsp;</td> 
      </tr> 
     </tbody> 
    </table>
    <table border="0" cellpadding="0" cellspacing="0" width="90%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
       <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/shenzhen/122811/122833/122840/3501254/index.html" onclick="void(0)" target="_blank" title="中国人民银行深圳市中心支行行政处罚公示表（2018年第49期）">中国人民银行深圳市中心支行行政处罚公示表（2018年第49期）</a></font></td> 
       <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-19</td> 
       <td class="hei12jj" height="40" valign="middle" align="left">&nbsp;</td> 
      </tr> 
     </tbody> 
    </table>
    <table border="0" cellpadding="0" cellspacing="0" width="90%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
       <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/shenzhen/122811/122833/122840/3501243/index.html" onclick="void(0)" target="_blank" title="中国人民银行深圳市中心支行行政处罚公示表（2018年第48期）">中国人民银行深圳市中心支行行政处罚公示表（2018年第48期）</a></font></td> 
       <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-19</td> 
       <td class="hei12jj" height="40" valign="middle" align="left">&nbsp;</td> 
      </tr> 
     </tbody> 
    </table>
    <table border="0" cellpadding="0" cellspacing="0" width="90%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
       <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/shenzhen/122811/122833/122840/3501235/index.html" onclick="void(0)" target="_blank" title="中国人民银行深圳市中心支行行政处罚公示表（2018年第47期）">中国人民银行深圳市中心支行行政处罚公示表（2018年第47期）</a></font></td> 
       <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-19</td> 
       <td class="hei12jj" height="40" valign="middle" align="left">&nbsp;</td> 
      </tr> 
     </tbody> 
    </table>
    <table border="0" cellpadding="0" cellspacing="0" width="90%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
       <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/shenzhen/122811/122833/122840/3501205/index.html" onclick="void(0)" target="_blank" title="中国人民银行深圳市中心支行行政处罚公示表（2018年第46期）">中国人民银行深圳市中心支行行政处罚公示表（2018年第46期）</a></font></td> 
       <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-19</td> 
       <td class="hei12jj" height="40" valign="middle" align="left">&nbsp;</td> 
      </tr> 
     </tbody> 
    </table>
    <table border="0" cellpadding="0" cellspacing="0" width="90%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
       <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/shenzhen/122811/122833/122840/3500457/index.html" onclick="void(0)" target="_blank" title="中国人民银行深圳市中心支行行政处罚公示表（2018年第45期）">中国人民银行深圳市中心支行行政处罚公示表（2018年第45期）</a></font></td> 
       <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-16</td> 
       <td class="hei12jj" height="40" valign="middle" align="left">&nbsp;</td> 
      </tr> 
     </tbody> 
    </table>
    <table border="0" cellpadding="0" cellspacing="0" width="90%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
       <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/shenzhen/122811/122833/122840/3497277/index.html" onclick="void(0)" target="_blank" title="中国人民银行深圳市中心支行行政处罚公示表（2018年第44期）">中国人民银行深圳市中心支行行政处罚公示表（2018年第44期）</a></font></td> 
       <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-12</td> 
       <td class="hei12jj" height="40" valign="middle" align="left">&nbsp;</td> 
      </tr> 
     </tbody> 
    </table>
    <table border="0" cellpadding="0" cellspacing="0" width="90%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
       <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/shenzhen/122811/122833/122840/3497272/index.html" onclick="void(0)" target="_blank" title="中国人民银行深圳市中心支行行政处罚公示表（2018年第43期）">中国人民银行深圳市中心支行行政处罚公示表（2018年第43期）</a></font></td> 
       <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-12</td> 
       <td class="hei12jj" height="40" valign="middle" align="left">&nbsp;</td> 
      </tr> 
     </tbody> 
    </table>
    <table border="0" cellpadding="0" cellspacing="0" width="90%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
       <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/shenzhen/122811/122833/122840/3497267/index.html" onclick="void(0)" target="_blank" title="中国人民银行深圳市中心支行行政处罚公示表（2018年第42期）">中国人民银行深圳市中心支行行政处罚公示表（2018年第42期）</a></font></td> 
       <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-12</td> 
       <td class="hei12jj" height="40" valign="middle" align="left">&nbsp;</td> 
      </tr> 
     </tbody> 
    </table></td> 
  </tr> 
  <tr> 
   <td style="line-height: 25px; margin: 0px auto; width: 400px;"> 
    <table class="fenye" style="position:relative" border="0" cellpadding="0" cellspacing="0" width="95%"> 
     <tbody> 
      <tr> 
       <td class="hui12" height="41" valign="top" align="right"> 
        <div align="center"> 
         <span style="font-size:12px"> 共<b>427</b>条&nbsp;&nbsp; 分<b>43</b>页&nbsp;&nbsp; 当前&nbsp;第<b>1</b>页&nbsp;&nbsp; <a tagname="[HOMEPAGE]" class="">首页</a> <a tagname="[PREVIOUSPAGE]" class="">上一页</a> <a style="cursor:pointer" href="/shenzhen/122811/122833/122840/15142/index2.html" tagname="/shenzhen/122811/122833/122840/15142/index2.html" class="pagingNormal">下一页</a> <a style="cursor:pointer" href="/shenzhen/122811/122833/122840/15142/index43.html" tagname="/shenzhen/122811/122833/122840/15142/index43.html" class="pagingNormal">末页</a> </span> 
        </div></td> 
      </tr> 
     </tbody> 
    </table><input type="hidden" name="article_paging_list_hidden" moduleid="15142" modulekey="15142" totalpage="43" /></td> 
  </tr> 
 </tbody> 
</table>
'''
    soup = BeautifulSoup(html,'lxml')
    key_word_punish = ur'[\s]*(行政){0,1}处罚(的)*(信息){0,1}[\s]*(公示表|表|公示)'
    tags = soup.find_all('a',text = re.compile(key_word_punish))
    print len(tags)
    for tag in tags:
        print tag.text
           
if __name__ == '__main__':
    crawler()
#     test_single()
#     regex_test()


    
