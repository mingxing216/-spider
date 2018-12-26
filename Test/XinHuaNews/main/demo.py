import hashlib



new_url = 'http://www.xinhuanet.com/politics/2018-10/10/c_1123535948.htm'

print(hashlib.sha1(new_url.encode('utf-8')).hexdigest())