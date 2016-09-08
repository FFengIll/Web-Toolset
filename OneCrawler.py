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
cacheFile = "Cache"
outputFile = "One.txt"
retry = False
clean = False
 
def get_url(num):
    return root_url + '/one/' + str(num)

#we can filter the data already existed
def get_urls(ids): 
    urls = map(get_url, ids)
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

def getVol(title):
    volume = title
    try:
        #print volume
        revolume=re.compile("[0-9]+")
        newvol= revolume.findall(volume)
        #print newvol
        if(newvol.__len__() > 0):
            volume = newvol[0]
            #print "new",volume
    except Exception,e:
        print e
        print volume
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
        title=soup.title.string
        #get volume number from title
        volume=getVol(title)
        dataList["volume"] = volume
        #print dataList["volume"],
        
        #one statement
        for meta in soup.select('meta'):
            if meta.get('name') == 'description':
                #code mode may crash the statement, please do encode here
                dataList["content"] = meta.get('content').strip()
        #print dataList["content"]
    
        #one image
        dataList["imgUrl"] = soup.find_all('img')[1]['src'].strip()

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

  
def mysort(x,y):
    a=x['volume']
    b=y['volume']
    try:
        if(a):
            a=int(a)
        if(b):
            b=int(b)
    except Exception,e:
        print e
        print a,b
        
    return - cmp(a,b)
  
if __name__=='__main__':
        
    #get newest id
    newest = getNewest()
    print "newest one is {0}".format(newest)
    
    #load exist data in JSON file
    existData = loadExist(cacheFile)
    
    #get exist id list
    existIDs=[]
    for s in existData:   
        d=s
        id=int( d['id'] )

        #retry if invalid data
        if(retry):
            if(d['volume']==None):
                continue
        
        existIDs.append(id)
    
    #get new pending
    pendingIDs=[]    
    for i in range(newest-1500,newest+1):
        if(i<0):
            continue
            
        if(i in existIDs):
            continue
        else:
            pendingIDs.append(i)

    print pendingIDs
        
    #get url by the id we need
    urls = get_urls(pendingIDs)
    
    pool = Pool(5)
    dataList = []
    
    #run and crawl the data
    start = time.time()
    dataList = pool.map(get_data, urls)
    end = time.time()
    
    #log the number
    oldnumber=existData.__len__()
    newnumber = dataList.__len__()
    
    #retry to get the data, so we should drop the old invalid data
    if(retry):
        newExistData=[]
        for data in existData:
            if(data['volume']==None):
                continue
            else:
                newExistData.append(data)
        existData = newExistData

    #clean the data, which means drop the duplicate data with same key (id invalid we should retry)
    if(clean):
        IDs=[]
        newExistData=[]
        for data in existData:
            if(data['volume']==None):
                continue
            elif(data['id'] in IDs):
                continue
            else:
                IDs.append(data['id'])
                newExistData.append(data)
        existData = newExistData

    #combine new and old data
    existData.extend(dataList)  
 
    #if new data, sort them
    if(newnumber > 0):
        #sort by the id aka volume in ascending order
        existData.sort(lambda x,y: mysort(x,y))
    
    #update dump file only when we have new data
    if(newnumber > 0):
            
        #dump the object into json string
        jsonData = json.dumps({'data':existData})
        #print jsonData
        
        #dump the json string into file
        with open(cacheFile, 'w') as outfile:
            json.dump(jsonData, outfile)
        
        
    print 'use: %.2f s' % (end - start)
    print "exist data number: %d" % (oldnumber)
    print "found new data number: %d" %(newnumber)
    
    '''
    Output the data into a file.
    Code mode may crash the statement, please do encode here.
    '''
    output = open(outputFile,"w")
    for data in existData:
        if(data.has_key("content")):
            #try:
            if(1):
                id = data['id'].encode("utf-8")
                vol = "Vol." + data["volume"].encode("utf-8")
                content = data["content"].encode('GB18030')
                #content = data["content"].encode('utf-8')
                
                output.write(vol)
                output.write("\t")
                output.write(content)
                output.write("\n")
            #except Exception, e:
            #    print "ERROR"

    output.close()
     

  
  