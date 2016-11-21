#!/usr/bin/env python
# -*- coding:utf-8 -*- 

import utils

access_key  = 'b45c8123-c3d6-418c-be71-96554a21cd9a'
access_secret = '39460515-9d51-447e-a0c5-50664242e69f'

db_dir = "./db"
db_file = "chbtc_db"

conditions = [
  {
    "currency": "btc_cny",
    "t": "5min",
    "since": "",
    "size": 1000,
    "n": 5,
    "increase": 1
  },
  {
    "currency": "btc_cny",
    "t": "5min",
    "since": "",
    "size": 1000,
    "n": 5,
    "increase": 0.8
  },
  {
    "currency": "btc_cny",
    "t": "5min",
    "since": "",
    "size": 1000,
    "n": 5,
    "increase": 0.5
  },
  {
    "currency": "btc_cny",
    "t": "5min",
    "since": "",
    "size": 1000,
    "n": 5,
    "increase": 0.3
  }
]
