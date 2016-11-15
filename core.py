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
from multiprocessing import Pool
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
def _fq(market, code, start, end, k = "day", fq = "qfq", size = 640):
  url = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param=%s%s,%s,%s,%s,%s,%s&r=%s" % (market, code, k, start, end, size, fq, random.random())
  return json.loads(requests.get(url).text.split("=")[1])["data"][market + code][fq + k]

def long_fq(market, code, start, end, k = "day", fq = "qfq", size = 640):
  date_s, date_e = parse(start), parse(end)
  data = []
  while True:
    start = date_s.strftime("%Y-%m-%d")
    end = date_e.strftime("%Y-%m-%d")
    if (date_e - date_s).days <= 640:
      data += _fq(market, code, start, end, k, fq, size)
      print start, end
      return data
    else:
      end = (date_s + datetime.timedelta(days = 640)).strftime("%Y-%m-%d")
      data += _fq(market, code, start, end, k, fq, size)
      print start, end
      date_s = parse(end) + datetime.timedelta(days = 1)
    

# macd
def macd(close, short=12, long=26, m=9):
  diff, dea, macd = talib.MACD(close, fastperiod=short, slowperiod=long, signalperiod=m)
  return (diff, dea, macd * 2)

# ma
def ma(close, p = 30):
  return talib.MA(close, p)

def pick(q):
  market, code, start, end = q
  try:
    data = long_fq(market, code, start, end)
  except Exception as e:
    print e
    if parse(start) < parse(end):
      start = (parse(start) + datetime.timedelta(days = 100)).strftime("%Y-%m-%d")
      if parse(start) >= parse(end):
        return (market, code, [])
      q = (market, code, start, end)
      return pick(q)
  c = [float(j[2]) for j in data]
  n = 10
  percent = 50
  r = [0, ] * n
  ret = []
  for i in range(len(c)):
    if i < n:
      continue
    if max(r[i-n:i]) == 1:
      r.append(0)
      continue
    if i + n < len(c):
      if max(c[i:i+n])/c[i] > (100 + percent) / 100.0:
        r.append(1)
        ret.append(data[i][0])
      else:
        r.append(0)
  return (market, code, list(set(ret)))

if __name__ == "__main__":
  q = []
#  for i in stock_list():
#    q.append((i[0], i[1], "2011-01-01", "2016-11-08"))
  q.append(("sz", "000002", "2011-01-01", "2016-11-14"))
  pool = ThreadPool(16)
  r = pool.map(pick, q)
  pool.close() 
  pool.join()

  data = long_fq("sz", "000002", "2011-01-01", "2016-11-14")
  p = []
  for i in range(len(data)):
    if data[i][0] in r[0][2]:
      p.append(i)
  print p
    

