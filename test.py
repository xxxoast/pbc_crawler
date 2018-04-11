#-*- coding:utf-8 -*-
from bs4 import BeautifulSoup
import re
from misc import is_table_td

html = '''
<td width="20%" style="width:20.32%;border:solid windowtext 1.0pt;border-left:  none;padding:0cm 5.4pt 0cm 5.4pt;height:62.6pt"> <p class="MsoNormal" align="center"><b><span>违法行为</span></b></p> <p class="MsoNormal" align="center"><b><span>类<span lang="EN-US">&nbsp;&nbsp;&nbsp; </span>型</span></b></p> </td>
'''

soup = BeautifulSoup(html,'lxml')
tags = soup.find_all(is_table_td)
print tags[0].prettify()