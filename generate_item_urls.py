# -*- coding:utf-8 -*- 
import os
import time
import re
import threading

# coding : cp936
import requests
from urlparse import urljoin
from get_dynamic_html import get_js_html
from bs4 import BeautifulSoup

unicode2utf8 = lambda x: x.encode('utf8') if isinstance(x,unicode) else x
dates_trans = lambda x: ''.join(x.split('-'))

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

def find_public_page(root_url):
    #get main page
    main_page = get_js_html(root_url)
    soup = BeautifulSoup(main_page, 'lxml')
    #init 
    key_word_outer = '政务公开目录'
    key_word_inner = re.compile(ur'行政处罚(公示){0,1}')
    key_word_punish = re.compile(ur'(((行政){0,1}处罚(的)*(信息){0,1}(公示|公示表|表)[\s]*)|([1-9]+号))')
    key_word_date  = re.compile(ur'^20[0-9]{2}-[0-9]{1,2}-[0-9]{1,2}$')
    has_found = False
    download_urls = []
    # find 公开目录
    public_xml = soup.find_all('a',text = key_word_outer )
    if len(public_xml) <= 0:
        return '',[]
    public_url = urljoin(root_url,public_xml[0].get('href'))
    print 'public_url = ',public_url
    public_page = get_js_html(public_url)
    punish_soup = BeautifulSoup(public_page,'lxml')
    # find 处罚公示
    punish_xml = punish_soup.find_all('a',text = key_word_inner)
    if len(punish_xml) <= 0:
        return '',[]
    punish_url = urljoin(root_url,punish_xml[0].get('href'))
    print 'punish_url = ',punish_url
    item_list_page = get_js_html(punish_url)
    item_list_soup = BeautifulSoup(item_list_page,'lxml')
    
    punish_items_tr = [ i.parent for i in item_list_soup.find_all('td',text = key_word_punish) if i.parent and i.find('a') ]
    punish_items_tr = filter(lambda i:i.find('td',text = key_word_date),punish_items_tr)
    punish_items = [ i.find('a',text = key_word_punish).get('href') for i in punish_items_tr]
    punish_dates = [ i.find('td',text = key_word_date).text for i in punish_items_tr]
    
    # recursively get next page
    next_page_tag = item_list_soup.find('a',text = '下一页')
    while next_page_tag and ( ('href' in next_page_tag.attrs) or ('tagname' in next_page_tag.attrs) ):
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
        next_page_tag = next_soup.find('a',text = '下一页')
#         print 'next_page_tag = ',next_page_tag
    #urljoin
    for punish_item,punish_date in zip(punish_items,punish_dates):
        des_url = urljoin(root_url,punish_item)
        if des_url != punish_url:
            download_urls.append((des_url,punish_date))          
    if len(download_urls) <= 0:
        print 'Failed = ',root_url
        return '',[]
    return punish_url,download_urls
    
    
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
            punish_url,des_urls = find_public_page(url)
            print 'len(des_urls) = ', len(des_urls)
            des_path = '/home/xudi/tmp/pbc_punishment5'
            des_path = os.path.join(des_path, '-'.join((city , str(len(des_urls)))))
    
            with open(des_path,'w+') as fout:
                for (i,j) in des_urls:
                    s = ' '.join((city,url.strip(),punish_url.strip(),i.strip(),dates_trans(j)))
                    fout.write(unicode2utf8(s))
                    fout.write('\n')

def regex_soup_test():
    html = '''
    <table width="100%" align="center" border="0" cellpadding="0" cellspacing="0" opentype="page"> 
 <tbody> 
  <tr> 
   <td style="margin: 10px auto;">
    <ul class="">
     <li class="">
      <table width="100%" border="0" cellpadding="0" cellspacing="0"> 
       <tbody> 
        <tr> 
         <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
         <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/fzhtianjin/resource/cms/2018/03/中国人民银行天津分行行政处罚信息公示表-违反《人民币银行结算账户管理办法》相关规定20180312.docx" onclick="recordLinkArticleHits('3499935')" target="_blank" title="中国人民银行天津分行行政处罚信息公示表-违反《人民币银行结算账户管理办法》相关规定(20180312).">中国人民银行天津分行行政处罚信息公示表-违反《人民币银行结算账户管理办法》相关规定(20180312).</a></font></td> 
         <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-03-16</td> 
         <td class="hei12jj" height="40" valign="middle" width="96" align="left">&nbsp;</td> 
        </tr> 
       </tbody> 
      </table></li>
     <li class="">
      <table width="100%" border="0" cellpadding="0" cellspacing="0"> 
       <tbody> 
        <tr> 
         <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
         <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/fzhtianjin/resource/cms/2018/02/中国人民银行天津分行行政处罚信息公示表—未按规定履行客户身份识别义务、保存客户身份资料（20180211）.docx" onclick="recordLinkArticleHits('3483435')" target="_blank" title="中国人民银行天津分行行政处罚信息公示表—未按规定履行客户身份识别义务、保存客户身份资料（20180211）">中国人民银行天津分行行政处罚信息公示表—未按规定履行客户身份识别义务、保存客户身份资料（20180211）</a></font></td> 
         <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-02-13</td> 
         <td class="hei12jj" height="40" valign="middle" width="96" align="left">&nbsp;</td> 
        </tr> 
       </tbody> 
      </table></li>
     <li class="">
      <table width="100%" border="0" cellpadding="0" cellspacing="0"> 
       <tbody> 
        <tr> 
         <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
         <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/fzhtianjin/resource/cms/2018/02/中国人民银行天津分行行政处罚信息公示表—未按规定履行客户身份识别义务、报送大额交易报告（20180211）.doc" onclick="recordLinkArticleHits('3483428')" target="_blank" title="中国人民银行天津分行行政处罚信息公示表—未按规定履行客户身份识别义务、报送大额交易报告（20180211）">中国人民银行天津分行行政处罚信息公示表—未按规定履行客户身份识别义务、报送大额交易报告（20180211）</a></font></td> 
         <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-02-13</td> 
         <td class="hei12jj" height="40" valign="middle" width="96" align="left">&nbsp;</td> 
        </tr> 
       </tbody> 
      </table></li>
     <li class="">
      <table width="100%" border="0" cellpadding="0" cellspacing="0"> 
       <tbody> 
        <tr> 
         <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
         <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/fzhtianjin/resource/cms/2018/02/中国人民银行天津分行行政处罚信息公示表—违反《非金融机构支付服务管理办法》等相关法律制度规定（20180207）.doc" onclick="recordLinkArticleHits('3483423')" target="_blank" title="中国人民银行天津分行行政处罚信息公示表 违反《非金融机构支付服务管理办法》等相关法律制度规定（20180207）">中国人民银行天津分行行政处罚信息公示表 违反《非金融机构支付服务管理办法》等相关法律制度规定（2018020...</a></font></td> 
         <td class="hei12jj" height="40" valign="middle" width="100" align="left">2018-02-13</td> 
         <td class="hei12jj" height="40" valign="middle" width="96" align="left">&nbsp;</td> 
        </tr> 
       </tbody> 
      </table></li>
     <li class="">
      <table width="100%" border="0" cellpadding="0" cellspacing="0"> 
       <tbody> 
        <tr> 
         <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
         <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/fzhtianjin/resource/cms/2017/12/中国人民银行天津分行行政处罚信息公示表-违反《征信业管理条例》规定（20171213）.doc" onclick="recordLinkArticleHits('3442611')" target="_blank" title="中国人民银行天津分行行政处罚信息公示表-违反《征信业管理条例》规定（20171213）">中国人民银行天津分行行政处罚信息公示表-违反《征信业管理条例》规定（20171213）</a></font></td> 
         <td class="hei12jj" height="40" valign="middle" width="100" align="left">2017-12-18</td> 
         <td class="hei12jj" height="40" valign="middle" width="96" align="left">&nbsp;</td> 
        </tr> 
       </tbody> 
      </table></li>
     <li class="">
      <table width="100%" border="0" cellpadding="0" cellspacing="0"> 
       <tbody> 
        <tr> 
         <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
         <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/fzhtianjin/resource/cms/2017/09/中国人民银行天津分行行政处罚信息公示表—拒绝兑换残缺污损人民币（20170817）.doc" onclick="recordLinkArticleHits('3373488')" target="_blank" title="中国人民银行天津分行行政处罚信息公示表-拒绝兑换残缺污损人民币（20170817）">中国人民银行天津分行行政处罚信息公示表-拒绝兑换残缺污损人民币（20170817）</a></font></td> 
         <td class="hei12jj" height="40" valign="middle" width="100" align="left">2017-08-17</td> 
         <td class="hei12jj" height="40" valign="middle" width="96" align="left">&nbsp;</td> 
        </tr> 
       </tbody> 
      </table></li>
     <li class="">
      <table width="100%" border="0" cellpadding="0" cellspacing="0"> 
       <tbody> 
        <tr> 
         <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
         <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/fzhtianjin/resource/cms/2017/10/中国人民银行天津分行行政处罚信息公示表—未按规定设置、发送收单交易信息（20170802）.doc" onclick="recordLinkArticleHits('3367185')" target="_blank" title="中国人民银行天津分行行政处罚信息公示表-未按规定设置、发送收单交易信息（20170802）">中国人民银行天津分行行政处罚信息公示表-未按规定设置、发送收单交易信息（20170802）</a></font></td> 
         <td class="hei12jj" height="40" valign="middle" width="100" align="left">2017-08-02</td> 
         <td class="hei12jj" height="40" valign="middle" width="96" align="left">&nbsp;</td> 
        </tr> 
       </tbody> 
      </table></li>
     <li class="">
      <table width="100%" border="0" cellpadding="0" cellspacing="0"> 
       <tbody> 
        <tr> 
         <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
         <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/fzhtianjin/resource/cms/2017/05/中国人民银行天津分行行政处罚信息公示表-违反存款准备金管理规定（20170527）.doc" onclick="recordLinkArticleHits('3316297')" target="_blank" title="中国人民银行天津分行行政处罚信息公示表-违反存款准备金管理规定（20170527）">中国人民银行天津分行行政处罚信息公示表-违反存款准备金管理规定（20170527）</a></font></td> 
         <td class="hei12jj" height="40" valign="middle" width="100" align="left">2017-05-27</td> 
         <td class="hei12jj" height="40" valign="middle" width="96" align="left">&nbsp;</td> 
        </tr> 
       </tbody> 
      </table></li>
     <li class="">
      <table width="100%" border="0" cellpadding="0" cellspacing="0"> 
       <tbody> 
        <tr> 
         <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
         <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/fzhtianjin/resource/cms/2017/12/中国人民银行天津分行行政处罚信息公示表-违反《征信业管理条例》规定20161121.doc" onclick="recordLinkArticleHits('3437439')" target="_blank" title="中国人民银行天津分行行政处罚信息公示表-违反《征信业管理条例》规定(20161121)">中国人民银行天津分行行政处罚信息公示表-违反《征信业管理条例》规定(20161121)</a></font></td> 
         <td class="hei12jj" height="40" valign="middle" width="100" align="left">2016-11-23</td> 
         <td class="hei12jj" height="40" valign="middle" width="96" align="left">&nbsp;</td> 
        </tr> 
       </tbody> 
      </table></li>
     <li class="">
      <table width="100%" border="0" cellpadding="0" cellspacing="0"> 
       <tbody> 
        <tr> 
         <td class="hui12" height="50" valign="middle" width="20" align="left">&nbsp;</td> 
         <td class="hei12jj" height="40" valign="middle" width="400" align="left"><font class="hei12"><a href="/fzhtianjin/113682/113700/113707/2625104/index.html" onclick="void(0)" target="_blank" title="中国人民银行行政处罚文书">中国人民银行行政处罚文书</a></font></td> 
         <td class="hei12jj" height="40" valign="middle" width="100" align="left">2011-12-29</td> 
         <td class="hei12jj" height="40" valign="middle" width="96" align="left">&nbsp;</td> 
        </tr> 
       </tbody> 
      </table></li>
    </ul></td> 
  </tr> 
  <tr> 
   <td style="line-height: 25px; margin: 0px auto; width: 400px;"> 
    <div style="width:90%; font-family: Arial;font-size: 12px;font-weight: normal; margin:15px auto 0;"> 
     <table cellspacing="0" cellpadding="0" border="0" width="100%"> 
      <tbody> 
       <tr> 
        <td nowrap="true" align="center" valign="bottom" style="line-height:23px;" class="Normal"> 共10条<span style="width:10px;display:inline-block;"></span> 分1页<span style="width:10px;display:inline-block;"></span> 当前 第1页<span style="width:15px;display:inline-block;"></span> <a tagname="[HOMEPAGE]" class="">首页</a> <span style="width:5px;display:inline-block;"></span> <a tagname="[PREVIOUSPAGE]" class="">上一页</a> <span style="width:5px;display:inline-block;"></span> <a tagname="[NEXTPAGE]" class="">下一页</a> <span style="width:5px;display:inline-block;"></span> <a tagname="[LASTPAGE]" class="">尾页</a> </td> 
       </tr> 
      </tbody> 
     </table> 
    </div><input type="hidden" name="article_paging_list_hidden" moduleid="10983" modulekey="10983" totalpage="1" /></td> 
  </tr> 
 </tbody> 
</table></td> 
      </tr> 
      <tr valign="middle"> 
       <td colspan="4" height="20"> </td> 
      </tr> 
     </tbody> 
    </table> <script type="text/javascript">
    countNum(1427);        
    </script> </td> 
  </tr> 
 </tbody> 
</table> </td> 
    </tr> 
   </tbody> 
  </table> 
'''
    soup = BeautifulSoup(html,'lxml')
    key_word_punish = re.compile(ur'(((行政){0,1}处罚(的)*(信息){0,1}(公示|公示表|表))|(第{0,1}[0-9]+号))')
    key_word_date  = re.compile(ur'20[0-9]{2}-[0-9]{1,2}-[0-9]{1,2}')
    
    punish_items_tr = [ i.parent for i in soup.find_all('td',text = key_word_punish) if i.parent ]
    punish_items_tr = filter(lambda i:i.find('td',text = key_word_date),punish_items_tr)
    punish_items = [ i.find('a',text = key_word_punish).get('href') for i in punish_items_tr]
    punish_dates = [ i.find('td',text = key_word_date).text for i in punish_items_tr]
    print punish_items,punish_dates
           
if __name__ == '__main__':
    crawler()
#     regex_soup_test()


    
