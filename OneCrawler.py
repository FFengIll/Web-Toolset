'''
Reference: http://python.jobbole.com/84714/
'''

import argparse
import re
from multiprocessing import Pool
import requests
import bs4
import time
import json
import io
 
root_url = 'http://wufazhuce.com'
 
def get_url(num):
    return root_url + '/one/' + str(num)

def get_urls(begin,end):
  urls = map(get_url, range(begin,end))
  return urls



def getNewest():
  url_home="http://wufazhuce.com/"
  response=requests.get(url_home)
  soup=bs4.BeautifulSoup(response.text, "html.parser")

  container=soup.find('div',id="main-container")
  container=container.find('a', href=re.compile("http://wufazhuce.com/one/[0-9]+"))
  print container

  idre=re.compile("[0-9]+")
  id=idre.findall(container.get('href'))
  print id
  res= int(id[0])
  print res
  return res

def get_data(url):
  dataList = {}

  #visit url
  response = requests.get(url)

  #no data
  if response.status_code != 200:
      return {'noValue': 'noValue'}

  #parse as html
  soup = bs4.BeautifulSoup(response.text,"html.parser")

  #title
  volume=soup.title.string[0:10].split()[0]
  dataList["index"] = volume
  print dataList["index"],

  #one statement
  for meta in soup.select('meta'):
    if meta.get('name') == 'description':
      dataList["content"] = meta.get('content')
  print dataList["content"]

  #one picture
  dataList["imgUrl"] = soup.find_all('img')[1]['src']
  return dataList


if __name__=='__main__':
  newest=getNewest()

  pool = Pool(4)
  dataList = []

  #get url by the id we need
  urls = get_urls(newest-50,newest)

  start = time.time()
  dataList = pool.map(get_data, urls)
  end = time.time()

  print 'use: %.2f s' % (end - start)
  exit(1)
  jsonData = json.dumps({'data':dataList})
  with open('data.txt', 'w') as outfile:
    json.dump(jsonData, outfile)