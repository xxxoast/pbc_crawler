# -*- coding:utf-8 -*- 

import os,sys
pkg_path = os.path.sep.join(
    (os.path.abspath(os.curdir).split(os.path.sep)[:-1]))
if pkg_path not in sys.path:
    sys.path.append(pkg_path)
    
from future_mysql.dbBase import DB_BASE
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Index, Float, Boolean
from sqlalchemy import Table

class City(DB_BASE):

    def __init__(self):
        db_name = 'pbc'
        table_name = 'punishemnt_items'
        super(City, self).__init__(db_name)

        self.table_struct = Table(table_name, self.meta,
                                  Column('city', String(64),index = True),
                                  Column('web_url',String(256),index = True),
                                  Column('publication_url', String(256),index = True),
                                  Column('punishment_item', String(256)),primary_key = True),
                                  Column('update_date',Integer)
                                  )
        
    def create_table(self):
        self.user_struct = self.quick_map(self.table_struct)
        
if __name__ == '__main__':
    pass