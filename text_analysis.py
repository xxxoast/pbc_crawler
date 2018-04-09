#-*- coding:utf-8 -*-

import os
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import subprocess
import re
import pdftables_api

from db_api import Publication

root_path = r'/home/xudi/tmp/punishment_source'

public_table_kw = re.compile(ur'违法行为\s*(类型|内容){0,1}')
payment_kw = re.compile(ur'(网络支付)|(预付卡)|(银行卡)|(收单)|(备付金)|(票据)|(商户)|(支付服务管理)|(结算)|(账户)')
unpayment_kw = re.compile(ur'(空头支票)|(现金)|(残损币)|(假币)|(准备金)|(统计)|(国库)|(反洗钱)|(身份识别)|(外汇)|(消费者)|(征信)')
content_kw = re.compile(ur'违[法规](行为){0,1}\s*(类型|内容){0,1}')
chinese_kw = re.compile(ur'[\u4e00-\u9fa5]')
doc_kw     = re.compile(ur'.(docx{0,1})|(wps)|(xls)|(xlsx)$')
amount_kw  = re.compile(ur'([1-9][0-9，,.]*万{0,1})元')
sum_amount_kw = re.compile(ur'[合总]计[\u4e00-\u9fa5]*([1-9][0-9，,.]*万{0,1})元')
tenk_kw    = re.compile(ur'万')
comma_kw   = re.compile(ur'[,，]')
empty = re.compile('[ \n\t/-]')

is_replaceble = lambda x: isinstance(x,str) or isinstance(x,unicode)
date_f = lambda x: int(x[:4]) * 10000 + int(x[4:-2]) * 100 + int(x[-2:])

is_invalid_file = lambda x: x.endswith('.et') or x.endswith('.tif')

def str2float(text):
    no_comma = comma_kw.sub('',text)
    no_spot  = no_comma.split('.')[0]
    multiply = 1
    if tenk_kw.search(text):
        no_spot = tenk_kw.sub('',no_spot)
        multiply = 10000
    return multiply * float(no_spot)
    
def get_punishment_amount(text):
    total = [ i for i in sum_amount_kw.findall(text) if len(i) > 0]
    if len(total) > 0:
        total = str2float(total[-1])
        return total
    else:
        each = [ i for i in amount_kw.findall(text) if len(i) > 0]
        return sum([str2float(i) for i in each])

def flatten(l):    
    for el in l:    
        if hasattr(el, "__iter__") and not isinstance(el, basestring):    
            for sub in flatten(el):    
                yield sub    
        else:    
            yield el 

def get_violation_kw(x):
    matched = [ j for i in payment_kw.findall(x) for j in i if len(j) > 0]
    return ','.join(matched)
    
def locat_content_column(columns):
    for index,col in enumerate(columns):
        reobj = content_kw.search(col)
        if reobj:
            return index
    return -1

def is_table_td(tag):
    return tag.name == 'td' and public_table_kw.search(tag.text)

def htmlpath2txt(htmlpath):
    rows = []
    with open(htmlpath) as fin:
        for line in fin:
            rows.append(line)
    return ''.join(rows)

def parse_html(infile,dbapi,update_date = None):
    city,index,date = infile.split('/')[-2],infile.split('/')[-1].split('_')[0],int(infile.split('/')[-1].split('_')[1].split('.')[0])  
    ss = dbapi.get_session()
    has_stored = ss.query(dbapi.table_struct.index).filter_by(city = city,index=index).scalar()
    if has_stored:
        ss.close()
        return 
    if update_date and update_date > date:
        ss.close()
        return
    htmltxt = htmlpath2txt(infile)
    soup = BeautifulSoup(htmltxt,'lxml')
    tag = soup.find_all(is_table_td)[-1]
    tag = tag.find_parent('table')
    df = pd.read_html(tag.prettify())[0]
    df = df.applymap(lambda x:re.sub(empty,'',x) if is_replaceble(x) else x)
    if str(df.columns[0]) == '0':
        df.columns = df.iloc[0].values
        df.drop([0,],axis = 0,inplace = True)
    col_index = locat_content_column(df.columns)
    punish_index = col_index + 1
    is_payment = df.ix[:,col_index].apply(lambda x: True if payment_kw.search(x) else False)
    not_payment = df.ix[:,col_index].apply(lambda x: True if unpayment_kw.search(x) else False)
    df = df[ (is_payment) & np.logical_not(not_payment)]
    df = df.fillna('')
    keywords = df.ix[:,col_index].apply(get_violation_kw)
    db_table_columns = dbapi.get_column_names(dbapi.table_struct) 
    for row_index,row in df.iterrows():
        amount = get_punishment_amount(row[df.columns[punish_index]]) / 10000
        arglist = flatten((city,index,row[df.columns[1:6]].values,
                                   date_f(chinese_kw.sub('',row[df.columns[6]])),
                                   amount,keywords[row_index],row[df.columns[-1]]))
        argdict = dict(zip(db_table_columns,arglist))
        ss.add(dbapi.table_struct(**argdict))
        ss.commit()
    ss.close()
    return 

def test_html(dbapi):    
    infile = r'/home/xudi/tmp/punishment_source/beijing/0_20180320.html'
    parse_html(infile,dbapi)

def parse_doc(infile,dbapi,update_date = None):
    desfile = doc_kw.sub('.html',infile)
    city,index,date = infile.split('/')[-2],infile.split('/')[-1].split('_')[0],int(infile.split('/')[-1].split('_')[1].split('.')[0])  
    ss = dbapi.get_session()
    has_stored = ss.query(dbapi.table_struct.index).filter_by(city = city,index=index).scalar()
    ss.close()
    if not has_stored:
        subprocess.call(r'/usr/bin/unoconv -f html -o {} {}'.format(desfile,infile).split(),shell=False)
        if os.path.exists(desfile):
            parse_html(desfile,dbapi)

def parse_pdf(infile,dbapi,update_date = None):
    outfile = infile.replace('.pdf','.csv')
    c = pdftables_api.Client('k8hrttpelsyi')
    c.csv(infile,outfile)
    
def update_publication(update_date = None):    
    dbapi = Publication()
    dbapi.create_table()
    #convert doc/docx/xls/xlsx/wps to html
    print 'step 1, convert docs to html'
    for root, dirs, files in os.walk(root_path):
        print root.split('/')[-1]
        for ifile in filter(lambda x: doc_kw.search(x) is not None,files):
            print ifile
            infile = os.path.join(root,ifile) 
            desfile = doc_kw.sub('.html',infile)
            if not os.path.exists(desfile):
                subprocess.call(r'/usr/bin/unoconv -f html -o {} {}'.format(desfile,infile).split(),shell=False)
                
    print 'step 2, parse html, store into db'
    for root, dirs, files in os.walk(root_path):
        print root.split('/')[-1]
        for ifile in filter(lambda x: (not x.startswith('.')) and x.endswith('.html'),files):
            print ifile
            infile = os.path.join(root,ifile)
            if infile.endswith('.html'):
                parse_html(infile,dbapi,update_date)

            
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-date','--date', dest='date', nargs='?', default = None)
    args = parser.parse_args()
    arg_dict = vars(args)
    print update_publication(arg_dict['date'])
    