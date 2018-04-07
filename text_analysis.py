#-*- coding:utf-8 -*-

import os
import pandas as pd
from bs4 import BeautifulSoup
import re

public_table_kw = re.compile(ur'违法行为\s*(类型|内容){0,1}')
def is_table_td(tag):
    return tag.name == 'td' and public_table_kw.search(tag.text)

def htmlpath2txt(htmlpath):
    rows = []
    with open(htmlpath) as fin:
        for line in fin:
            rows.append(line)
    return ''.join(rows)

def parse_html(infile):
    htmltxt = htmlpath2txt(infile)
    soup = BeautifulSoup(htmltxt,'lxml')
    tag = soup.find_all(is_table_td)[-1]
    tag.find_parent('table')
    this_table = False
    while True:
        tag = tag.parent
        if tag.name != 'table':
            if hasattr(tag, 'parent'):
                tag = tag.parent
            else:
                break
        else:
            this_table = True
            break
    if this_table:
        print tag.prettify()
 
if __name__ == '__main__':
    infile = r'/home/xudi/tmp/punishment_source/beijing/0_20180320.html'
    parse_html(infile)