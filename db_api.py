# -*- coding:utf-8 -*- 

import os,sys
pkg_path = os.path.sep.join(
    (os.path.abspath(os.curdir).split(os.path.sep)[:-1]))
if pkg_path not in sys.path:
    sys.path.append(pkg_path)
    
from future_mysql.dbBase import DB_BASE
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Index, Float, Boolean
from sqlalchemy import Table
import os

get_city = lambda x: x.split('-')[0]

class Punishment(DB_BASE):

    def __init__(self):
        db_name = 'pbc'
        table_name = 'punishement'
        super(Punishment, self).__init__(db_name)

        self.table_obj = Table(table_name, self.meta,
                                  Column('city', String(64),index = True),
                                  Column('web_url',String(128),),
                                  Column('publication_url', String(128),index = True),
                                  Column('punishment_item_url', String(128),primary_key = True),
                                  Column('update_date',Integer)
                                  )
        
    def create_table(self):
        self.table_struct = self.quick_map(self.table_obj)
        

def init_table():        
    dbapi = Punishment()
    dbapi.create_table()
    src_path = r'/home/xudi/tmp/pbc_punishment5'
    for root, dirs, files in os.walk(src_path):
        print root
        for name in files:
            fname = os.path.join(root, name)
            with open(fname,'r') as fin:
                for line in fin:
                    data = line.split()
                    dbapi.insert_listlike(dbapi.table_struct,data,merge = True)
                    
                    
if __name__ == '__main__':
    init_table()
    