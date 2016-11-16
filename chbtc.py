#!/usr/bin/env python
# -*- coding:utf-8 -*- 

import json
import requests
import datetime
import time
import talib
import numpy as np
import hashlib
import os
import math

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

if __name__ == "__main__":
  f_size = 30
  for c in cond()[:1]:
    cond_dir = "%s_%s_%s_%s" % (c["currency"], c["t"], c["n"], c["increase"])
    _mkdir("./data/feature/%s" % (cond_dir, ))
    _k = k(c["currency"], c["t"], c["since"], c["size"])

    for i in pick(_k, c["n"], c["increase"]):
      f_file = "./data/feature/%s/%s" % (cond_dir, i)
      if not os.path.isfile(f_file):
        f = feature(c["currency"], c["t"], i - 1000 * str2sec(c["t"]) * (f_size + 970), f_size + 970)
        md5 = hashlib.md5(json.dumps(f)).hexdigest()
        with open(f_file, "w") as fd:
          fd.write(json.dumps(f))

    _c = [i[4] for i in _k]
    _c = [j / _c[0] for j in _c]
    diff, dea, _macd = macd(np.array(_c))
    for j in [f for f in os.listdir("./data/feature/%s" % (cond_dir, )) if os.path.isfile(os.path.join("./data/feature/%s" % (cond_dir, ), f))]:
      with open(os.path.join("./data/feature/%s" % (cond_dir, ), j), "r") as feature_file:
        fea = json.loads(feature_file.read())
        v = _v(_k, fea)
        if v < fea["v"]:
          print "buy"
        print "c:%s" % (v, )
        print "v:%s" % (fea["v"], )
    
    
