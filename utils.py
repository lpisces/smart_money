#!/usr/bin/env python
# -*- coding:utf-8 -*- 

import json
import requests
import time
import talib
import os

def kline(currency = "btc_cny", t = "5min", since  = "", size = 1000, retry = 5):
  url = "http://api.chbtc.com/data/v1/kline?currency=%s&type=%s&since=%s&size=%s" % (currency, t, since, size)
  while retry > 0:
    try:
      return json.loads(requests.get(url).text)["data"]
    except Exception as e:
      retry -= 1
      time.sleep(3)
      continue
  return []

def tick(currency, retry = 5):
  url = "http://api.chbtc.com/data/v1/ticker?currency=%s" % (currency, )
  while retry > 0:
    try:
      return json.loads(requests.get(url).text)
    except Exception as e:
      #print e
      retry -= 1
      time.sleep(3)
      continue
  return []

def str2sec(s):
  t = {
    "1min": 60, 
    "3min": 60 * 3, 
    "5min": 60 * 5, 
    "15min": 60 * 15,
    "30min": 60 * 30,
    "1day" : 60 * 60 * 24,
    "3day" : 60 * 60 * 24 * 3,
    "1week": 60 * 60 * 24 * 7,
    "1hour": 60 * 60,
    "2hour": 60 * 60 * 2,
    "4hour": 60 * 60 * 4,
    "6hour": 60 * 60 * 6,
    "12hour": 60 * 60 * 12
  }
  return t[s]

def macd(close, short=12, long=26, m=9):
  diff, dea, macd = talib.MACD(close, fastperiod=short, slowperiod=long, signalperiod=m)
  return (diff, dea, macd * 2)

def mkdir(path):
  try:
    p = path.split("/")
    p = ["/".join(p[:i+1]) for i in range(len(p))][1:]
    for i in p:
      if not os.path.isdir(i):
        os.mkdir(i)
    return True
  except Exception as e:
    print e
    return False

