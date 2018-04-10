#-*- coding:utf-8 -*-
from bs4 import BeautifulSoup
import re

html = '''
<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: none; padding: 0cm" width="72">
     <p align="center" class="cjk">
      <strong>
       <font size="3" style="font-size: 12pt">
        违法行为类
       </font>
      </strong>
      <strong>
       <font face="Times New Roman, serif">
        <font size="3" style="font-size: 12pt">
        </font>
       </font>
      </strong>
      <strong>
       <font size="3" style="font-size: 12pt">
        型
       </font>
      </strong>
     </p>
    </td>
'''
def is_table_td(tag):
    if tag.name == 'td':
        print repr(tag.text)
    return tag.name == 'td' and public_table_kw.search(tag.text)

soup = BeautifulSoup(html,'lxml')
public_table_kw = re.compile(ur'违[法规反]行为\s*(类型|内容)')
tags = soup.find_all(is_table_td)
print tags