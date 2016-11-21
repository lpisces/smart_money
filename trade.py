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
import time, datetime
 
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

  n, increase, feature_size = condition["n"], condition["increase"], condition["feature_size"]
  c = [i[4] for i in k[:-1]]
  h = [i[2] for i in k[:-1]]
  r = [0, ] * (n + feature_size)
  ret = []
  for i in range(len(c)):
    if i < feature_size:
      continue
    if max(r[-n:]) == 1:
      r.append(0)
      continue
    if i + n + 1< len(c):
      if max(h[i+1:i+n+1])/c[i] > (100 + increase) / 100.0:
        r.append(1)
        ret.append(k[i][0])
      else:
        r.append(0)
    else:
      break
  return list(set(ret))

def mfeature(c):
  f = feature(c["k"], c["point"], c["feature_size"])
  return f
  try:
    #f = feature(c["currency"], c["t"], c["since"], c["size"], c["feature_size"])
    f = feature(c["k"], c["point"], c["feature_size"])
    return f
  except Exception as e:
    print e
    time.sleep(3)
    return mfeature(c)

#def feature(currency, t, since, size, feature_size):
#  _k = utils.kline(currency, t, since, size)
#  c = [i[4] for i in _k]
#  c = [j / c[0] for j in c]
#  diff, dea, _macd = utils.macd(np.array(c))
#  f = {}
#  f["diff"] = list(diff[-1*size:])
#  f["dea"] = list(dea[-1*size:])
#  f["macd"] = list(_macd[-1*size:])
#  _k2 = utils.kline(currency, t, since - 1000 * utils.str2sec(t) * size, size)
#  f["v"] = feature_benchmark(_k2, f, feature_size)
#  return f

def feature(k, point, feature_size):
  c = [i[4] for i in k[:-1]]
  c = [j / c[0] for j in c]
  diff, dea, _macd = utils.macd(np.array(c))
  f = {}
  for ki in range(len(c)):
    if k[ki][0] == point:
      break
  f["diff"] = list(diff[ki - feature_size:ki])
  f["dea"] = list(dea[ki - feature_size:ki])
  f["macd"] = list(_macd[ki - feature_size:ki])
  f["v"] = feature_benchmark(k, f, feature_size)
  #print f["v"]
  #print "".join(hashlib.md5(json.dumps(f)).hexdigest())
  #print point
  #print "".join(hashlib.md5(json.dumps(k[:-1])).hexdigest())
  #print k[:-1]
  #print point
  #print ki - feature_size, ki
  return f

def feature_benchmark(k, f, size, p = 99):
  c = [i[4] for i in k[:-1]]
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
  k = utils.kline(condition["currency"], condition["t"], "", condition["size"])
  points = pick(k, condition)
  box = []
  for i in points:
    p = {}
    #p["currency"], p["t"], p["since"], p["size"], p["feature_size"] = condition["currency"], condition["t"], i - 1000 * utils.str2sec(condition["t"]) * condition["size"], condition["size"], 30
    p["k"], p["point"], p["feature_size"] = k, i, condition["feature_size"]
    box.append(p)

  pool = ThreadPool(16)
  feas = pool.map(mfeature, box)
  pool.close() 
  pool.join()

  conn = sqlite3.connect("%s/%s" % (config.db_dir, config.db_file))
  c = conn.cursor()
  feature_items = []
  for f in range(len(feas)):
    content = json.dumps(feas[f])
    digest = "".join(hashlib.md5(content).hexdigest())
    point = points[f]
    c.execute("select content from features where digest = ? or point = ?", (digest, point))
    r = c.fetchone() 
    if r != None:
      print "digest(%s) or point(%s) exits." % (digest, point)
      print json.loads(r[0])["v"]
      print datetime.datetime.fromtimestamp(point/1000).strftime('%Y-%m-%d %H:%M:%S')
      continue

    currency = condition["currency"]
    size = condition["size"]
    n = condition["n"]
    increase = condition["increase"]
    feature_size = 30
    feature_items.append((digest, content, condition["currency"], condition["t"], condition["size"], condition["n"], condition["increase"], feature_size, point))
  c.executemany("insert into features values (?, ?, ?, ?, ?, ?, ?, ?, ?)", feature_items)
  conn.commit()
  conn.close()
  return feature_items

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
  items = []
  for c in conditions:
    items += features(c)
  print len(items)


if __name__ == "__main__":
  try:
    init_db()
  except:
    pass
  while True:
    run()
    time.sleep(5 * 60)
