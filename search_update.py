#-*- coding:utf-8 -*-

from get_punishment_urls import crawler
from db_api import Punishment
import pandas as pd
import time


def get_today():
    t = time.localtime()
    return t.tm_year * 10000 + t.tm_mon * 100 + t.tm_mday

def search_update(update_date,include = [],exclude = []):
    crawler(include = include,exclude = exclude,init = False)
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-date','--date', dest='date', nargs='?', default = get_today())
    parser.add_argument('-include','--include', dest='include', nargs='*', default = [])
    parser.add_argument('-exclude','--exclude', dest='exclude', nargs='*', default = [])
    args = parser.parse_args()
    arg_dict = vars(args)
    print search_update(arg_dict['date'], \
                        include = arg_dict['include'],\
                        exclude = arg_dict['exclude'])
    
    