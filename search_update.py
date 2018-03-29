#-*- coding:utf-8 -*-

from get_punishment_urls import crawler
from db_api import Punishment
import pandas as pd

def search_update(update_date,include = [],exclude = []):
    crawler(include = include,exclude = exclude,mode = 'update')
    dbapi = Punishment()
    dbapi.create_table()
    sql = '''
        select * from pbc.punishment as t
        where t.update_date > {}
        ''' .format(update_date)
    if len(include) > 0:
        sql = sql + \
        'and t.city in ({})'.format(','.join([ repr(i) for i in include]))    
    if len(exclude) > 0:
        sql = sql + \
        'and t.city not in ({})'.format(','.join([ repr(i) for i in exclude]))
    sql = ''.join((sql,';'))
    df = pd.read_sql_query(sql,dbapi.engine)
    return df
    
if __name__ == '__main__':
#     print search_update(20180301,include = ['beijing','shanghai'],exclude = ['shanghai'])
    test_html()