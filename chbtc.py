#!/usr/bin/env python
# -*- coding:utf-8 -*- 

from __future__ import absolute_import
import json
import requests
import datetime
import time
import talib
import numpy as np
import hashlib
import os
import math
import api
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

access_key    = 'b45c8123-c3d6-418c-be71-96554a21cd9a'
access_secret = '39460515-9d51-447e-a0c5-50664242e69f'

def k(currency = "btc_cny", t = "5min", since  = "", size = 1000, retry = 5):
  url = "http://api.chbtc.com/data/v1/kline?currency=%s&type=%s&since=%s&size=%s" % (currency, t, since, size)
  while retry > 0:
    try:
      return json.loads(requests.get(url).text)["data"]
    except Exception as e:
      #print e
      retry -= 1
      time.sleep(3)
      continue
  return []

def pick(k, n = 10, increase = 1):
  c = [i[4] for i in k]
  h = [i[2] for i in k]
  r = [0, ] * n
  ret = []
  for i in range(len(c)):
    if i < n:
      continue
    if max(r[i-n:i]) == 1:
      r.append(0)
      continue
    if i + n < len(c):
      if max(h[i:i+n])/c[i] > (100 + increase) / 100.0:
        r.append(1)
        #ret.append(datetime.datetime.fromtimestamp(k[i][0]/1000).strftime('%Y-%m-%d %H:%M:%S'))
        #print datetime.datetime.fromtimestamp(k[i][0]/1000).strftime('%Y-%m-%d %H:%M:%S')
        ret.append(k[i][0])
      else:
        r.append(0)
  return list(set(ret))

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

def feature(currency, t, since, size):
  _k = k(currency, t, since, size)
  c = [i[4] for i in _k]
  c = [j / c[0] for j in c]
  diff, dea, _macd = macd(np.array(c))
  f = {}
  f["diff"] = list(diff[-30:])
  f["dea"] = list(dea[-30:])
  f["macd"] = list(_macd[-30:])
  _k2 = k(currency, t, since - 1000 * str2sec(t) + size, size)
  f["v"] = pick_v(_k2, f)
  return f

def pick_v(k, f, p = 99.5):
  c = [i[4] for i in k]
  c = [j / c[0] for j in c]
  diff, dea, _macd = macd(np.array(c))
  r = []
  for i in range(len(diff)):
    a, b, c = 0, 0, 0  
    if i < 100:
      continue
    for j in range(30):
      a += math.pow(f["diff"][j] - diff[i-29+j], 2)
      b += math.pow(f["dea"][j] - dea[i-29+j], 2)
      c += math.pow(f["macd"][j] - _macd[i-29+j], 2)
    r.append(math.sqrt(a+b+c))
  r.sort()
  print r[:10]
  return r[int(len(r) * (100 - p) / 100.0)]

def _v(k, f):
  c = [i[4] for i in k]
  c = [j / c[0] for j in c]
  diff, dea, _macd = macd(np.array(c))
  r = []
  for i in range(len(diff)):
    a, b, c = 0, 0, 0  
    if i != len(diff) - 1:
      continue
    for j in range(30):
      a += math.pow(f["diff"][j] - diff[i-29+j], 2)
      b += math.pow(f["dea"][j] - dea[i-29+j], 2)
      c += math.pow(f["macd"][j] - _macd[i-29+j], 2)
    r.append(math.sqrt(a+b+c))
  return r[0]

def __v(item):
  k, f = item
  return _v(k, f)

def cond():
  cond = []
  cond.append(
    {
      "currency": "btc_cny",
      "t": "5min",
      "since": "",
      "size": 1000,
      "n": 10,
      "increase": 1
    }
  )
  cond.append(
    {
      "currency": "btc_cny",
      "t": "5min",
      "since": "",
      "size": 1000,
      "n": 10,
      "increase": 0.8
    }
  )
  cond.append(
    {
      "currency": "btc_cny",
      "t": "5min",
      "since": "",
      "size": 1000,
      "n": 10,
      "increase": 0.5
    }
  )
  cond.append(
    {
      "currency": "btc_cny",
      "t": "5min",
      "since": "",
      "size": 1000,
      "n": 10,
      "increase": 0.3
    }
  )
  return cond

def _mkdir(path):
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

def _cancel(currency):
  chbtc_api = api.chbtc_api(access_key, access_secret)
  buy_orders = chbtc_api.get_orders(currency, 1)
  sell_orders = chbtc_api.get_orders(currency, 0)
  orders = buy_orders + sell_orders
  for o in orders:
    if o["status"] not in [2, 1]:
      retry = 3
      while retry > 0:
        try:
          r = cancel_order(o["id"], currency)
          print "cancel%s" % (o["id"], )
          if r["code"] != "1000":
            retry -= 1
            continue
        except Exception as e:
          print e
          retry -= 1
          continue

def _order(currency, t = "b", retry = 3):
  _cancel(currency)
  while retry > 0:
    try:
      r = order(currency, "b")
      if r == False:
        return False
      if r["code"] != "1000":
        retry -= 1
        continue
    except Exception as e:
      print e
      retry -= 1
      continue
  time.sleep(1)
  if retry > 0:
    try:
      info = get_order(r["id"], currency)
      if info["status"] != 2:
        time.sleep(1)
        return _order(currency, t)
    except:
      return False
    return r["id"]
  return False

         
def account():
  chbtc_api = api.chbtc_api(access_key, access_secret)
  account = chbtc_api.query_account()
  return account

def get_order(oid, currency):
  chbtc_api = api.chbtc_api(access_key, access_secret)
  order = chbtc_api.get_order(oid, currency)
  return order

def cancel_order(oid, currency):
  chbtc_api = api.chbtc_api(access_key, access_secret)
  order = chbtc_api.cancel_order(oid, currency)
  return order

def order(currency, t = "b"):
  _account = account()
  chbtc_api = api.chbtc_api(access_key, access_secret)
  a = float(_account["result"]["balance"][currency.split("_")[0].upper()]["amount"])
  b = float(_account["result"]["balance"][currency.split("_")[-1].upper()]["amount"])
  tick = _tick(currency)
  sell = float(tick["ticker"]["sell"])
  buy = float(tick["ticker"]["buy"])
  cur = "%.3f" % (a, )

  if t == "b":
    t = 1
    price = "%.3f" % (sell, )
    amount = "%.3f" % (b / sell, )
  else:
    t = 0 
    price = "%.3f" % (buy, )
    amount = cur

  if float(amount) < 0.001 and t == 1:
    print "no money left."
    return False

  if float(cur) < 0.001 and t == 0:
    print "nothing to sell."
    return False

  print price, amount, t, currency
  r = chbtc_api.order(price, amount, t, currency)
  r["price"] = price
  r["status"] = "open"
  return r

def _tick(currency, retry = 5):
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

def get_feature(c):
  cond_dir = "%s_%s_%s_%s" % (c["currency"], c["t"], c["n"], c["increase"])
  feature_dir = "./data/feature/%s" % (cond_dir, )
  _mkdir(feature_dir)
  _k = k(c["currency"], c["t"], c["since"], c["size"])
  features = []
  # feature size
  f_size = 30 
  for i in pick(_k, c["n"], c["increase"]):
    feature_file = "%s/%s" % (feature_dir, i)
    if not os.path.isfile(feature_file):
      f = feature(c["currency"], c["t"], i - 1000 * str2sec(c["t"]) * (f_size + 970), f_size + 970)
      md5 = hashlib.md5(json.dumps(f)).hexdigest()
      print md5
      with open(feature_file, "w") as fd:
        fd.write(json.dumps(f))
    else:
      with open(feature_file, "r") as fd:
        f = json.loads(fd.read())
        md5 = hashlib.md5(json.dumps(f)).hexdigest()
        print md5

  for j in [f for f in os.listdir(feature_dir) if os.path.isfile("%s/%s" % (feature_dir, f))]:
    with open("%s/%s" % (feature_dir, j), "r") as fd:
      features.append(json.loads(fd.read()))
  return features

def run():
  #print account()
  b = False
  trade_dir = "./data/trade"
  _mkdir(trade_dir)

  try:
    oid = [f for f in os.listdir(trade_dir) if os.path.isfile("%s/%s" % (trade_dir, f))].sort()[-1]
    with open("%s/%s" % (trade_dir, oid), "r") as fd:
      t = json.loads(fd.read())
    _k = k(t["currency"], t["t"], t["since"], t["size"])
    order_info = get_order(oid, currency)
    if float(_k[-1][4]) / float(order_info["price"]) * 100 - 100 > t["increase"] or int(order_info["trade_date"]) + int(t["n"]) * 1000 * str2sec(t["t"]) > int(_k[-1][0]):
      _order(t["currency"], "s")
  except Exception as e:
    print "no file"
    print e
  

  for c in cond()[:1]:
    if b:
      continue
    _k = k(c["currency"], c["t"], c["since"], c["size"])
    features = get_feature(c)
    pool = ThreadPool(16)
    vs = pool.map(__v, [(_k, f) for f in features])
    pool.close() 
    pool.join()

    for i in range(len(features)):
      print "condition:\t%s" % (c, )
      print "picked value:\t%.6f" % (features[i]["v"], )
      print "current values:\t%.6f" % (vs[i])
      #if vs[i] < features[i]["v"]:
      if True:
        b = True
        print "a"
        r = _order(c["currency"], "b")
        print "b"
        print "%s/%s" % ("r", r)
        if r != False:
          with open("%s/%s" % (trade_dir, r), "w") as fd:
            fd.write(json.dumps(c))
        break

if __name__ == "__main__":
  run()
