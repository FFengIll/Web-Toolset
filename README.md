# Crawler
Crawler using Python.

## One Crawler
It is a python version crawler to crawl the data from [[One·一个]](http://wufazhuce.com/) .

In the crawler, all data will cache into the cache file, so we can update the new datas only; 
and the human-readable information will output into another file.

该爬虫由Python编写，用于爬取 [[One·一个]](http://wufazhuce.com/) 的每日数据。

爬虫中有两个相关文件：cache缓存文件用于保存中间数据，确保更新时仅爬取新数据即可；
output文件用于输出可读信息（该文件每次都会被覆盖重写）。