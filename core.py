#!/usr/bin/env python
# -*- coding:utf-8 -*- 

"""
原始交易数据
@author Lpisces
@contact iamalazyrat@gmail.com
"""

import requests
import zipfile, StringIO
from bs4 import BeautifulSoup as bs
from multiprocessing.dummy import Pool as ThreadPool
import datetime
import pickle
import time
import os
from dateutil.parser import parse
import random
import json
import talib
import numpy as np

# 获取股票列表
def stock_list():
  # A股上市公司列表页面 
  STOCK_LIST_URL = "http://www.cninfo.com.cn/cninfo-new/information/companylist"

  url = STOCK_LIST_URL
  r = requests.get(url)
  soup = bs(r.text, 'html5lib')

  stock = []

  # 深圳主板
  a = soup.select('#con-a-1 > ul > li a')
  for s in a:
    code = s.text.split(" ")[0]
    name = "".join(s.text.split(" ")[1:])
    market = 'sz'
    board = 'szmb'
    stock.append((market, code, board, name))

  # 中小板
  a = soup.select('#con-a-2 > ul > li a')
  for s in a:
    code = s.text.split(" ")[0]
    name = "".join(s.text.split(" ")[1:])
    market = 'sz'
    board = 'szsme'
    stock.append((market, code, board, name))

  #创业板
  a = soup.select('#con-a-3 > ul > li a')
  for s in a:
    code = s.text.split(" ")[0]
    name = "".join(s.text.split(" ")[1:])
    market = 'sz'
    board = 'szcn'
    stock.append((market, code, board, name))

  #上证主板
  a = soup.select('#con-a-4 > ul > li a')
  for s in a:
    code = s.text.split(" ")[0]
    name = "".join(s.text.split(" ")[1:])
    market = 'sh'
    board = 'shmb'
    stock.append((market, code, board, name))

  return stock

# 复权数据
def fq(market, code, start, end, k = "day", fq = "qfq", size = 1000):
  url = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param=%s%s,%s,%s,%s,%s,%s&r=%s" % (market, code, k, start, end, size, fq, random.random())
  return json.loads(requests.get(url).text.split("=")[1])["data"][market + code][fq + k]

# macd
def macd(close, short=12, long=26, m=9):
  diff, dea, macd = talib.MACD(close, fastperiod=short, slowperiod=long, signalperiod=m)
  return (diff, dea, macd * 2)

# ma
def ma(close, p = 30):
  return talib.MA(close, p)

def test():
  data = fq("sh", "600149", "2013-01-01", "2016-11-08")
  diff, dea, _macd = macd(np.array([float(j[2]) for j in data]))
  flag = []
  for i in range(len(diff)):
    flag.append(0)
    if i < 10 or i + 2 > len(diff) - 1 :
      continue
    if min(diff[i-10:i]) > 0 and min(dea[i-10:i]) > 0:
      if _macd[i] >= 0:
        if float(data[i][2]) > max([float(j[3]) for j in data][i-60:i]):
          if max(flag[i-5:i]) == 1:
            continue
          else:
            flag[i] = 1
          print data[i]
          print "%0.2f%%" % ((max([float(n[3]) for n in data[i+1:i+3]])/float(data[i][2]) - 1) * 100, )
          print "%0.2f%%" % ((min([float(n[4]) for n in data[i+1:i+3]])/float(data[i][2]) - 1) * 100, )
  

if __name__ == "__main__":
  #print fq("sz", "000002", "2013-01-01", "2016-11-08")
  test()
