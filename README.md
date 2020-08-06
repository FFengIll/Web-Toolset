# Crawler
Python crawler package which named with its target.

简易的Python爬虫工具集合，所有爬虫以爬取目标进行命名。

## Dep.
```
# python2
bs4
lxml
request

# python3
requests_html
requests_file
```

## CVE Detail
Crawler for data from [CVE Detail](https://www.cvedetails.com).

## One
A python crawler for [[One·一个]](http://wufazhuce.com/) .

Output include 2 files:
- One cache file in json, so we can update the new datas only; 
- One human-readable output.

Python编写，用于爬取 [[One·一个]](http://wufazhuce.com/) 的每日数据。

爬虫中有两个相关文件：
- json格式的cache缓存文件，用于保存中间数据，确保更新时仅爬取新数据即可；
- txt格式output文件，用于输出可读信息，若有更新则会覆盖重写。

## Open Class
Crawler for the class slides from the university share website, like MIT, CMU and so on.

Easy write, easy use.

爬取开放课程资料（使用wget完成下载）。

## Page Item
Sometimes need to get the items from a spec. page.

用于抓取page中的特定内容。

## Util
some utils.

### util.py
some completed crawler session.

### logger.py
the pre-set logging.