#!/usr/bin/env python
# -*- coding:utf-8 -*- 

import utils

access_key  = ''
access_secret = ''

benchmark = 98

db_dir = "./db"
db_file = "chbtc_db"

conditions = [
  {
    "currency": "btc_cny",
    "t": "5min",
    "since": "",
    "size": 1000,
    "n": 5,
    "increase": 1,
    "feature_size": 30
  },
  {
    "currency": "btc_cny",
    "t": "5min",
    "since": "",
    "size": 1000,
    "n": 5,
    "increase": 0.8,
    "feature_size": 30
  },
  {
    "currency": "btc_cny",
    "t": "5min",
    "since": "",
    "size": 1000,
    "n": 5,
    "increase": 0.5,
    "feature_size": 30
  },
  {
    "currency": "btc_cny",
    "t": "5min",
    "since": "",
    "size": 1000,
    "n": 5,
    "increase": 0.3,
    "feature_size": 30
  }
]
