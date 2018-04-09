# -*- coding:utf-8 -*- 

import os,sys
pkg_path = os.path.sep.join(
    (os.path.abspath(os.curdir).split(os.path.sep)[:-1]))
if pkg_path not in sys.path:
    sys.path.append(pkg_path)
    
from future_mysql.dbBase import DB_BASE
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Index, Float, Boolean
from sqlalchemy import Table
from sqlalchemy import func,desc
import os

get_city = lambda x: x.split('-')[0]

class Punishment(DB_BASE):

    def __init__(self):
        db_name = 'pbc'
        table_name = 'punishment'
        super(Punishment, self).__init__(db_name)

        self.table_obj = Table(table_name, self.meta,
                                  Column('city', String(64),index = True),
                                  Column('web_url',String(128),),
                                  Column('publication_url', String(128),index = True),
                                  Column('punishment_item_url', String(128),primary_key = True),
                                  Column('update_date',Integer),
                                  Column('index',Integer,autoincrement = True)
                                  )
        
    def create_table(self):
        self.table_struct = self.quick_map(self.table_obj)
 

class Publication(DB_BASE):
    
    def __init__(self):
        db_name = 'pbc'
        table_name = 'publication'
        super(Publication, self).__init__(db_name)

        self.table_obj = Table(table_name, self.meta,
                                  Column('city', String(64),primary_key = True),
                                  Column('index',Integer,primary_key = True),
                                  Column('corpname',String(256)),
                                  Column('pubnumber',String(128)),
                                  Column('violatype',String(128)),
                                  Column('violacontent',String(512)),
                                  Column('whodid',String(128)),
                                  Column('update_date',Integer),
                                  Column('amount',Float),
                                  Column('keywords',String(64)),
                                  Column('abstract',String(256))
                                  )
        
    def create_table(self):
        self.table_struct = self.quick_map(self.table_obj)
     

def get_cities():
    dbapi = Punishment()
    dbapi.create_table()
    ss = dbapi.get_session()
    cursor = ss.query(dbapi.table_struct.city).group_by(dbapi.table_struct.city).all()
    cities = [i.city for i in cursor]
    ss.close()
    return cities

def init_punishment_table():        
    dbapi = Punishment()
    dbapi.create_table()
    src_path = r'/home/xudi/tmp/pbc_punishment'
    for root, dirs, files in os.walk(src_path):
        print root
        for name in files:
            cnt = 0
            fname = os.path.join(root, name)
            with open(fname,'r') as fin:
                for line in fin:
                    data = line.split()
                    data.append(cnt)
                    cnt += 1
                    dbapi.insert_listlike(dbapi.table_struct,data,merge = True)
                    
                    
if __name__ == '__main__':
    dbapi = Publication()
    dbapi.create_table()
    
    