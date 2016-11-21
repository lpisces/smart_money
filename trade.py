#!/usr/bin/env python
# -*- coding:utf-8 -*- 

import config
import utils
import api
import numpy as np
import math
import sqlite3
import hashlib
import json
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import time
 
def pick(k, condition):
  """
  Find the time point matching condition in the kline
  找到符合条件的时间点

  k:
  kline data
  k线数据

  condition:
  pre defined condition
  预定义条件
  """

  n, increase = condition["n"], condition["increase"]
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
        ret.append(k[i][0])
      else:
        r.append(0)
  return list(set(ret))

def mfeature(c):
  print c
  try:
    f = feature(c["currency"], c["t"], c["since"], c["size"], c["feature_size"])
  except:
    time.sleep(5)
    return mfeature(c)

def feature(currency, t, since, size, feature_size):
  _k = utils.kline(currency, t, since, size)
  c = [i[4] for i in _k]
  c = [j / c[0] for j in c]
  diff, dea, _macd = utils.macd(np.array(c))
  f = {}
  f["diff"] = list(diff[-1*size:])
  f["dea"] = list(dea[-1*size:])
  f["macd"] = list(_macd[-1*size:])
  _k2 = utils.kline(currency, t, since - 1000 * utils.str2sec(t) + size, size)
  f["v"] = feature_benchmark(_k2, f, feature_size)
  return f

def feature_benchmark(k, f, size, p = 99.5):
  c = [i[4] for i in k]
  c = [j / c[0] for j in c]
  diff, dea, _macd = utils.macd(np.array(c))
  r = []
  for i in range(len(diff)):
    a, b, c = 0, 0, 0  
    if i < 100:
      continue
    for j in range(size):
      a += math.pow(f["diff"][j] - diff[i-size+1+j], 2)
      b += math.pow(f["dea"][j] - dea[i-size+1+j], 2)
      c += math.pow(f["macd"][j] - _macd[i-size+1+j], 2)
    r.append(math.sqrt(a+b+c))
  r.sort()
  return r[int(len(r) * (100 - p) / 100.0)]

def features(condition):
  k = utils.kline(condition["currency"], condition["t"])
  points = pick(k, condition)
  box = []
  for i in points:
    p = {}
    p["currency"], p["t"], p["since"], p["size"], p["feature_size"] = condition["currency"], condition["t"], i - 1000 * utils.str2sec(condition["t"]) * condition["size"], condition["size"], 30
    box.append(p)

  pool = ThreadPool(16)
  feas = pool.map(mfeature, box)
  pool.close() 
  pool.join()
  print len(feas)
  
#    content = json.dumps(f)
#    digest = hashlib.md5(content).hexdigest()

def init_db():
  utils.mkdir(config.db_dir)
  conn = sqlite3.connect("%s/%s" % (config.db_dir, config.db_file))
  c = conn.cursor()
  c.execute('''Create table features (digest text, content text, currency text, t text, size INTEGER, n INTEGER, increase real, feature_size INTEGER, point INTEGER)''')
  c.execute('''Create table trade (created_at INTEGER, updated_at INTEGER, digest text, buy real default 0.0, sell real default 0.0)''')
  conn.commit()
  conn.close()

def run():
  conditions = config.conditions
  for c in conditions:
    #k = utils.kline(c["currency"], c["t"])
    features(c)


if __name__ == "__main__":
  try:
    init_db()
  except:
    pass
  run()
