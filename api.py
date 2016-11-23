#!/usr/bin/env python
# -*- coding:utf-8 -*- 

import json, urllib2, hashlib,struct,sha,time
import config
import utils

class chbtcApi:

  def __init__(self, mykey, mysecret):
    self.mykey  = mykey
    self.mysecret = mysecret

  def __fill(self, value, lenght, fillByte):
    if len(value) >= lenght:
      return value
    else:
      fillSize = lenght - len(value)
    return value + chr(fillByte) * fillSize

  def __doXOr(self, s, value):
    slist = list(s)
    for index in xrange(len(slist)):
      slist[index] = chr(ord(slist[index]) ^ value)
    return "".join(slist)

  def __hmacSign(self, aValue, aKey):
    keyb   = struct.pack("%ds" % len(aKey), aKey)
    value  = struct.pack("%ds" % len(aValue), aValue)
    k_ipad = self.__doXOr(keyb, 0x36)
    k_opad = self.__doXOr(keyb, 0x5c)
    k_ipad = self.__fill(k_ipad, 64, 54)
    k_opad = self.__fill(k_opad, 64, 92)
    m = hashlib.md5()
    m.update(k_ipad)
    m.update(value)
    dg = m.digest()
    
    m = hashlib.md5()
    m.update(k_opad)
    subStr = dg[0:16]
    m.update(subStr)
    dg = m.hexdigest()
    return dg

  def __digest(self, aValue):
    value  = struct.pack("%ds" % len(aValue), aValue)
    h = sha.new()
    h.update(value)
    dg = h.hexdigest()
    return dg

  def __api_call(self, path, params = ''):
    retry = 5
    while retry > 0:
      try:
        SHA_secret = self.__digest(self.mysecret)
        sign = self.__hmacSign(params, SHA_secret)
        reqTime = (int)(time.time()*1000)
        params+= '&sign=%s&reqTime=%d'%(sign, reqTime)
        url = 'https://trade.chbtc.com/api/' + path + '?' + params
        request = urllib2.Request(url)
        response = urllib2.urlopen(request, timeout=2)
        doc = json.loads(response.read())
        return doc
      except Exception,ex:
        print ex
        time.sleep(1)
        retry -= 1
    return None

  def get_account_info(self):
    try:
      params = "method=getAccountInfo&accesskey="+self.mykey
      path = 'getAccountInfo'
      obj = self.__api_call(path, str(params))
      return obj
    except Exception,ex:
      print ex
      return None

  def order(self, price, amount, t, currency):
    try:
      params = "method=order&accesskey=%s&price=%s&amount=%s&tradeType=%s&currency=%s" % (self.mykey, price, amount, t, currency)
      path = 'order'
      obj = self.__api_call(path, str(params))
      return obj
    except Exception,ex:
      print ex
      return None

  def get_order(self, oid, currency):
    try:
      params = "method=getOrder&accesskey=%s&id=%s&currency=%s" % (self.mykey, oid, currency)
      path = 'getOrder'
      obj = self.__api_call(path, str(params))
      return obj
    except Exception,ex:
      print ex
      return None

  def cancel_order(self, oid, currency):
    try:
      params = "method=cancelOrder&accesskey=%s&id=%s&currency=%s" % (self.mykey, oid, currency)
      path = 'cancelOrder'
      obj = self.__api_call(path, str(params))
      return obj
    except Exception,ex:
      print ex
      return None

  def get_orders(self, currency, t = 1, pageIndex = 1):
    try:
      params = "method=getOrders&accesskey=%s&tradeType=%s&currency=%s&pageIndex=%s" % (self.mykey, t, currency, pageIndex)
      path = 'getOrders'
      obj = self.__api_call(path, str(params))
      return obj
    except Exception,ex:
      print ex
      return None

def check(ret):
  if ret ==  None:
    return False
  if "code" in ret and str(ret["code"]) != "1000":
    return False
  return True
    
if __name__ == '__main__':
  access_key = config.access_key
  access_secret = config.access_secret
  api = chbtcApi(access_key, access_secret)
  r = api.get_account_info()
  if check(r):
    account = r 
    print "API get_account_info OK"
  else:
    print "API get_account_info error"
    exit()

  currency = "btc_cny"


  ids = []
  r = api.get_orders(currency, 1, 1)
  if check(r):
    for i in r:
      if i["status"] not in [1,2]:
        ids.append(i["id"])
    print "API get_orders OK"
  else:
    print "API get_orders error"
    exit()

  r = api.get_orders(currency, 0, 1)
  if check(r):
    for i in r:
      if i["status"] not in [1,2]:
        ids.append(i["id"])
    print "API get_orders OK"
  else:
    print "API get_orders error"
    exit()

  for i in ids:
    r = api.cancel_order(i, currency)
    if check(r):
      print "API cancel_order OK"
    else:
      print r["message"]
      print "API cancel_order error"


  a = float(account["result"]["balance"][currency.split("_")[0].upper()]["amount"])
  b = float(account["result"]["balance"][currency.split("_")[-1].upper()]["amount"])

  tick = utils.tick(currency)
  sell = float(tick["ticker"]["sell"])
  buy = float(tick["ticker"]["buy"])

  amount = "%.3f" % (b / sell, )
  if float(amount) < 0.001:
    amount = "%.3f" % (a, )
    price = buy * 1.1
    t = 0
    if float(amount) < 0.001:
      print "no money or btc for test"
      exit()
  else:
    price = sell * 0.9
    t = 1

  if float(amount) > 0.01:
    amount = 0.01
  r = api.order(price, amount, t, currency)
  if check(r):
    print "API order OK"
  else:
    print "API order error"
    print r["code"], r["message"]
    exit()

  order_id = r["id"]
  r = api.get_order(order_id, currency)
  if check(r):
    print r
    print "API get_order OK"
  else:
    print r["message"]
    print "API get_order error"
    exit()

  ids = []
  r = api.get_orders(currency, 1, 1)
  if check(r):
    for i in r:
      if i["status"] not in [1,2]:
        ids.append(i["id"])
    print "API get_orders OK"
  else:
    print "API get_orders error"
    exit()
  r = api.get_orders(currency, 0, 1)
  if check(r):
    for i in r:
      if i["status"] not in [1,2]:
        ids.append(i["id"])
    print "API get_orders OK"
  else:
    print "API get_orders error"
    exit()

  for i in ids:
    r = api.cancel_order(i, currency)
    if check(r):
      print "API cancel_order OK"
    else:
      print r["message"]
      print "API cancel_order error"
    
  
  


