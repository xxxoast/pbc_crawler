#-*- coding:utf-8 -*-

import os
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import subprocess
import re
import pdftables_api

from db_api import Publication
from misc import valid_city,unicode2utf8
from misc import is_table_td,dates_trans 
from misc import empty

root_path = r'/home/xudi/tmp/punishment_source'

payment_kw = re.compile(ur'(网络支付)|(预付卡)|(银行卡)|(收单)|(备付金)|(票据)|(支票)|(账户)|(商户)|(支付服务管理)|([清结]算)|(支付)')
unpayment_kw = re.compile(ur'(现金)|(残损币)|(假币)|(准备金)|(统计)|(国库)|(反洗钱)|(身份识别)|(外汇)|(消费者)|(征信)')
content_kw = re.compile(ur'违[法规](行为){0,1}\s*(类型|内容){0,1}')
date_kw = re.compile(ur'[\u4e00-\u9fa5/\\.-]')
doc_kw     = re.compile(ur'.((docx{0,1})|(wps)|(xls)|(xlsx))$')
amount_kw  = re.compile(ur'(?:(?:([1-9][0-9，,.]*万?)元)|(?:罚款([1-9][0-9，,.]*万?)元?))')
# amount_kw  = re.compile(ur'([1-9][0-9，,.]*万?)元')
sum_amount_kw = re.compile(ur'[合总共]计[\u4e00-\u9fa5]*([1-9][0-9，,.]*万?)元')
tenk_kw    = re.compile(ur'万')
comma_kw   = re.compile(ur'[,，]')

is_invalid_file = lambda x: x.endswith('.et') or x.endswith('.tif') or x.endswith('.png') 
is_replaceble = lambda x: isinstance(x,str) or isinstance(x,unicode)
    
def parse_pdf(infile,dbapi,update_date = None):
    outfile = infile.replace('.pdf','.csv')
    c = pdftables_api.Client('k8hrttpelsyi')
    c.csv(infile,outfile)
    
def str2float(text):
    no_comma = comma_kw.sub('',text)
    multiply = 1
    if tenk_kw.search(text):
        no_comma = tenk_kw.sub('',no_comma)
        multiply = 10000
    return multiply * float(no_comma)

def flatten(l):    
    for el in l:    
        if hasattr(el, "__iter__") and not isinstance(el, basestring):    
            for sub in flatten(el):    
                yield sub    
        else:    
            yield el
            
def get_punishment_amount(text):
    total = [ i for i in sum_amount_kw.findall(text) if len(i) > 0]
    if len(total) > 0:
        total = str2float(total[-1])
        return total
    else:
        each = [ i for i in flatten(amount_kw.findall(text)) if len(i) > 0]
        return sum([str2float(i) for i in each])


def get_violation_kw(x):
    matched = [ j for i in payment_kw.findall(x) for j in i if len(j) > 0]
    return ','.join(matched)
    
def locat_content_column(columns):
    for index,col in enumerate(columns):
        reobj = content_kw.search(col)
        if reobj:
            return index
    return -1

def htmlpath2txt(htmlpath):
    rows = []
    with open(htmlpath) as fin:
        for line in fin:
            rows.append(line)
    return ''.join(rows)

def parse_html(infile,dbapi,ss,update_date = None):
#     print infile
    city,index,publish_date = infile.split('/')[-2],infile.split('/')[-1].split('_')[0],int(infile.split('/')[-1].split('_')[1].split('.')[0])  
    has_stored = ss.query(dbapi.table_struct.index).filter_by(city = city,index=index).first()
    if has_stored:
        return 
    if update_date and update_date > publish_date:
        return
    htmltxt = htmlpath2txt(infile)
    soup = BeautifulSoup(htmltxt,'lxml')
    tags = soup.find_all(is_table_td)
    if len(tags) > 0:
        tag = tags[0]
    else:
        return 
    tag = tag.find_parent('table')
    dfs = pd.read_html(tag.prettify())
    df = dfs[0]
    df = df.dropna(axis = 1,how = 'all')
    df = df.applymap(lambda x:empty.sub('',x) if is_replaceble(x) else x)
    if len(df.columns) < 5:
        return 
    if str(df.columns[0]) == '0':
        df.iloc[0] = df.iloc[0].fillna('')
        df.columns = df.iloc[0].values
        df.drop([0,],axis = 0,inplace = True)
    col_index = locat_content_column(df.columns)
    punish_index = col_index + 1
    #去尾
    valid_rows = df[df.columns[col_index-1:col_index + 3]].\
                    apply(lambda x: np.logical_and(pd.notnull(x) , len(unicode2utf8(x)) > 0))
    df = df.loc[ valid_rows.all(axis = 1) ]
    if len(df) == 0:
        return
    df = df.fillna(method = 'pad')
    df = df.fillna('')
    df.drop_duplicates(subset=[df.columns[col_index-1],df.columns[col_index-2]], keep='first', inplace=True)
    is_payment = df.ix[:,col_index].apply(lambda x: True if payment_kw.search(x) else False)
    not_payment = df.ix[:,col_index].apply(lambda x: True if unpayment_kw.search(x) else False)
    df = df[ (is_payment) & np.logical_not(not_payment)]
    keywords = df.ix[:,col_index].apply(get_violation_kw)
    db_table_columns = dbapi.get_column_names(dbapi.table_struct) 
    for row_index,row in df.iterrows():
        amount = get_punishment_amount(row[df.columns[punish_index]]) / 10000
        if abs(amount) <= 0.1:
            continue
        decision_date = dates_trans(row[df.columns[col_index+3]])
        arglist = flatten((city,index,row[df.columns[col_index-2:col_index+3]].values,
                                   decision_date if decision_date else publish_date,
                                   amount,keywords.loc[row_index],row[df.columns[-1]]))
        argdict = dict(zip(db_table_columns,arglist))
        ss.merge(dbapi.table_struct(**argdict))
        ss.commit()
    return 

#1.convert doc/docx/xls/xlsx/wps to html
def convert_docs_to_htmls(include,exclude):
    print 'step 1, convert docs to html'
    for root, dirs, files in os.walk(root_path):
        city = root.split('/')[-1]
        if not valid_city(city,include,exclude):
            continue
        print city
        for ifile in filter(lambda x: doc_kw.search(x) is not None,files):
            infile = os.path.join(root,ifile) 
            desfile = doc_kw.sub('.html',infile)
            if not os.path.exists(desfile):
                subprocess.call(r'/usr/bin/unoconv -f html -o {} {}'.format(desfile,infile).split(),shell=False)

#2.remove extra rows of table before head
def precess_htmls(include,exclude):
    for root, dirs, files in os.walk(root_path):
        city = root.split('/')[-1]
        if not valid_city(city,include,exclude):
            continue
        print city
        #去头
        for ifile in filter(lambda x: (not x.startswith('.')) and x.endswith('.html'),files):
            infile = os.path.join(root,ifile)
            if infile.endswith('.html'):
                soup,rewrite = None,False
                with open(infile,'r') as fin:
                    buffer = ''.join(fin.readlines())
                    soup = BeautifulSoup(buffer,'lxml')
                    td_tags = soup.find_all(is_table_td)
                    if len(td_tags) > 0:
                        td_tag = td_tags[0]
                    else:
                        continue
                    tr_tag = td_tag.find_parent('tr')
                    previous_trs = tr_tag.find_previous_siblings('tr') 
                    if len(previous_trs) > 0:
                        rewrite = True
                        for tr in previous_trs:
                            tr.extract()
                if rewrite:
                    with open(infile,'w') as fout:
                        fout.write(soup.prettify(encoding='utf-8'))

#3.dumpdb
def dumpdb(include,exclude,update_date = None):
    dbapi = Publication()
    dbapi.create_table()
    ss = dbapi.get_session()
    for root, dirs, files in os.walk(root_path):
        city = root.split('/')[-1]
        if not valid_city(city,include,exclude):
            continue
        print city
        for ifile in filter(lambda x: (not x.startswith('.')) and x.endswith('.html'),files):
            infile = os.path.join(root,ifile)
            if infile.endswith('.html'):
                parse_html(infile,dbapi,ss,update_date)
                        
def update_publication(include = [], exclude = [], update_date = None):    
    print '    --->>> convert_docs_to_htmls'
    convert_docs_to_htmls(include,exclude)
    print '    --->>> precess_htmls'
    precess_htmls(include,exclude)
    print '    --->>> dumpdb'
    dumpdb(include,exclude,update_date)
    
def remove_invalid():
    for root, dirs, files in os.walk(root_path):
        print root.split('/')[-1]
        for ifile in filter(lambda x: x.endswith('..html'),files):
            infile = os.path.join(root,ifile)
            os.remove(infile)

def test():
    infile = r'/home/xudi/tmp/punishment_source/shanghai/119_20170913.html'
    dbapi = Publication()
    dbapi.create_table()
    ss = dbapi.get_session()
    parse_html(infile, dbapi, ss)

if __name__ == '__main__':
    print '--->>> text analysis!'
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-date','--date', dest='date', nargs='?', default = None)
    parser.add_argument('-include','--include', dest='include', nargs='*', default = [])
    parser.add_argument('-exclude','--exclude', dest='exclude', nargs='*', default = [])
    args = parser.parse_args()
    arg_dict = vars(args)
    update_publication(include = arg_dict['include'],\
                       exclude = arg_dict['exclude'],\
                       update_date = arg_dict['date'])
    print 'done!'
