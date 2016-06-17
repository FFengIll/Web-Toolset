# -*- coding:utf-8 -*-  
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

#we can filter the data already existed
def get_urls(begin,end,filter):
  newIDs=[]
  for i in range(begin,end+1):
    if(i in filter):
      continue
    else:
      newIDs.append(i)
  
  urls = map(get_url, newIDs)
  return urls
  
def get_urlid(url):
  substr=url.split('/')
  return substr[-1]

def getNewest():
  url_home="http://wufazhuce.com/"
  response=requests.get(url_home)
  soup=bs4.BeautifulSoup(response.text, "html.parser")

  container=soup.find('div',id="main-container")
  container=container.find_all('a', href=re.compile("http://wufazhuce.com/one/[0-9]+"))
  print container

  newest=0
  for a in container:
    idre=re.compile("[0-9]+")
    id=idre.findall(a.get('href'))
    print id
    res= int(id[0])
    if(res > newest):
        newest = res
        print newest
    
  return newest

def standardVol(volume):
    #print volume
    revolume=re.compile("[0-9]+")
    newvol= revolume.findall(volume)
    #print newvol
    if(newvol.__len__() > 0):
        volume = "Vol." + newvol[0]
        #print "new",volume
    return volume
    
  
def get_data(url):
  dataList = {}
  
  #get the id to identify the data
  id=get_urlid(url)
  dataList['id']=id
  #default volume is None
  dataList['volume']=None
  
  try:
    #visit url
    response = requests.get(url)

    #no data or can not reach, just return with id
    if response.status_code != 200:
        return dataList

    #parse as html
    soup = bs4.BeautifulSoup(response.text,"html.parser")

    #title
    volume=soup.title.string[0:10].split()[0]
    #process volume
    volume=standardVol(volume)
    dataList["volume"] = volume
    #print dataList["volume"],
    
    #one statement
    for meta in soup.select('meta'):
      if meta.get('name') == 'description':
        #code mode may crash the statement, please do encode here
        dataList["content"] = meta.get('content')
    #print dataList["content"]

    #one image
    dataList["imgUrl"] = soup.find_all('img')[1]['src']

  except Exception,e:
    print e
    
  return dataList

def loadExist(file):
  existData=None
  try:
    with open(file) as infile:
      #only read the json string from a file into a python object
      existData=json.load(infile)
      #must load the string into a json object
      existData=json.loads(existData)
  except Exception,e:
    return []
    
  #get data
  existData=existData["data"]
  #print existData
  
  return existData

if __name__=='__main__':
  #print standardVol("VOL.192")
  #exit(0)
  
  #get newest id
  newest = getNewest()
  #exit(0)
  
  #load exist data in JSON file
  existData = loadExist('data.txt')
  
  #get exist id list
  existIDs=[]
  for s in existData:   
    d=s
    id=int( d['id'] )
    existIDs.append(id)
  
  print existIDs
  #existIDs=[]
  #exit(0)
  
  
  #get url by the id we need
  urls = get_urls(newest-150,newest,existIDs)

  pool = Pool(4)
  dataList = []

  start = time.time()
  dataList = pool.map(get_data, urls)
  end = time.time()
  
  #log the number
  oldnumber=existData.__len__()
  newnumber = dataList.__len__()
    
  #combine data
  existData.extend(dataList)  
  
  #if new data, sort them
  if(newnumber > 0):
      #sort by the id aka volume in ascending order
      existData.sort(lambda x,y: cmp(x['volume'],y['volume']))
  
  #update dump file only when we have new data
  if(newnumber > 0):
        
    #dump the object into json string
    jsonData = json.dumps({'data':existData})
    #print jsonData
    
    #dump the json string into file
    with open('data.txt', 'w') as outfile:
      json.dump(jsonData, outfile)
      
  #print to read
  for data in existData:
    if(data.has_key("content")):
        #code mode may crash the statement, please do encode here
        try:
          print data['id'].encode("utf-8"), 
          print data["volume"].encode("utf-8"),
          #print data["content"].encode('utf-8')
          print data["content"].encode('GB18030')
        except Exception, e:
          print "ERROR"
          #exit(0)
     
  print 'use: %.2f s' % (end - start)
  print "exist data number: %d" % (oldnumber)
  print "found new data number: %d" %(newnumber)
  
  