import urllib.request
import urllib.parse
import http.cookiejar,re
import sqlite3
import time
import math
opener = None
id     = None

# 定义一个自己的头类, 继承 HTTPRedirectHandler
# 重写 http_error_302, 直接返回 fp(reponse);
class __RedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, hdrs):
        return fp

# 带Cookie访问
def openurl(parms):
  global opener
  if opener == None:
      #cookie设置
      cj =  http.cookiejar.CookieJar()
      opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), __RedirectHandler)
  ret = opener.open(parms,timeout=5)
  return ret

# sqllite control
conn = None
cursor = None
commit_num = 0
commit_count = 0

def create_():
  global conn
  global  cursor
  try:
    conn = sqlite3.connect('itjcw.db')
    cursor = conn.cursor()
    cursor.execute('create table download_url (id varchar(20) primary key, resource_type_name varchar(25), book_type_name varchar(25), price varchar(25), book_name varchar(50) , url varchar(256), baidu_pass varchar(50), dc_pass varchar(50), pic_url varchar(256), error_text varchar(50))')

  except Exception as e:
    print('Error:',e)

def close_():
  global conn
  global  cursor

  try:
    cursor.close()
    conn.commit()
    conn.close()
  except Exception as e:
      print('Error:',e)


def insert_(**parms):
  global commit_num
  global commit_count

  try:
    cursor.execute('insert into download_url VALUES (?,?,?,?,?,?,?,?,?,?)',( parms['id'], parms['resource_type_name'], parms['book_type_name'], parms['price'], parms['book_name'], parms['url'], parms['baidu_pass'], parms['dc_pass'], parms['pic_url'], parms['error_text']))
  except Exception as e:
    try:
      cursor.execute('update download_url set' 
                     + ' resource_type_name =  \''+ parms['resource_type_name'] + '\' ,'
                     + ' book_type_name =  \''+ parms['book_type_name'] + '\' ,'
                     + ' price =  \''+ parms['price'] + '\' ,'
                     + ' book_name =  \''+ parms['book_name'] + '\' ,' 
                     + ' url = \'' + parms['url'] + '\' ,' 
                     + ' baidu_pass = \'' + parms['baidu_pass'] + '\' ,'
                     + ' dc_pass = \'' + parms['dc_pass'] + '\' ,'
                     + ' pic_url = \'' + parms['pic_url'] +'\' ,' 
                     + ' error_text = \'' + parms['error_text'] +'\'' 
                     + ' where id = \''+ parms['id'] +'\''
                     )

    except Exception as e:
      print('insert_ Error:',e)
      pass

  if commit_count % commit_num == 0:
    conn.commit()

# http://www.itjiaocheng.com/coin/download.php?open=0&aid=10131

#
down_url = re.compile(r'<li class="pan-baidu"><a href="(.*?)" target="_blank">百度云盘</a> <span>提取码：<i>(.*?)</i>    <!--解压密码：<i></i>-->(.*?)</span></li>')
book_t = re.compile(r'<p><a href=\'(.*?)\' title=\'(.*?)\'><img src="(.*?)" /></a></p>')

book_type = re.compile(r'<p>分类：(.*?)</p>')
resource_type = re.compile(r'<p>类型：(.*?)</p>')
r_price = re.compile(r'<p>售价：(.*?)</p>')


def getBookType(url):
  resource_name = ''
  book_type_name = ''
  price = ''
  html = openurl('http://www.itjiaocheng.com' + url).read().decode('utf-8')
  if html == None:
    raise Exception("Invalid book type")
  
  book_type_ = book_type.search(html)
  if book_type_ != None:
      book_type_name = book_type_.group(1)
  
  resource_type_ = resource_type.search(html)
  if resource_type_ != None:
    resource_name = resource_type_.group(1)

  r_price_ = r_price.search(html)
  if r_price_ != None:
    price = r_price_.group(1)

  return [resource_name, book_type_name, price]


def getBaiduPage(id):
  global down_url
  global book_t
  resource_type_name = ''
  book_type_name = ''
  price = ''
  book_name = ''
  url = ''
  baidu_pass = ''
  dc_pass = ''
  pic_url = ''
  error_text = ''
  try:
    html = openurl('http://www.itjiaocheng.com/coin/download.php?open=0&aid=' + id).read().decode('utf-8')
    if html == None:
      raise Exception("Invalid down page")

    book = book_t.search(html)
    if book != None:
      book_name = book.group(2)
      pic_url = book.group(3)
      brp_ = getBookType(book.group(1))
      resource_type_name = brp_[0]
      book_type_name = brp_[1]
      price = brp_[2]

    if price.find('收费') != -1:
      raise Exception("Need paid")

    down =  down_url.search(html);
    if down == None:
      raise Exception("Invalid baidu url")



    baidu_pass = down.group(2)
    dc_pass = down.group(3)

    url = openurl('http://www.itjiaocheng.com/coin/' + down.group(1)).getheaders()[5][1]

    if url.find('dwz.cn') != -1:
       url = openurl(url).getheaders()[7][1]

  except Exception as e:
    print('getBaiduPage Error:',e, '|  id : ',id)
    error_text = str(e)
    pass

  if book_type_name == None:
    book_type_name = ''
  if resource_type_name == None:
    resource_type_name = ''
  if price == None:
    price = ''
  if book_name == None:
    book_name = ''
  if url == None:
    url = ''
  if baidu_pass == None:
    baidu_pass = ''
  if dc_pass == None:
    dc_pass = ''
  if pic_url == None:
    pic_url = ''


  insert_(id = id, 
          resource_type_name = resource_type_name,
          book_type_name = book_type_name, 
          price = price, 
          book_name = book_name, 
          url= url, 
          baidu_pass = baidu_pass, 
          dc_pass = dc_pass, 
          pic_url = pic_url, 
          error_text = error_text)

def login_(**parms):
  global commit_num
  global commit_count
  global id

  flag = False
  #初始化
  parms_key = ['password','username','domain','startid','endid', 'wait_time']
  arg = {}
  for key in parms_key:
    if key in parms:
      arg[key] = parms[key]
    else:
      arg[key] = ''

  # 登陆
  postdata = {
   'fmdo':'ajaxlogin',
   'myset':'ajax',
   'dopost':'send',
   'keeptime':'604800',
   'userid':arg['username'],
   'pwd':arg['password'],
    }
  postdata = urllib.parse.urlencode(postdata)
  postdata = postdata.encode('utf-8')
  req = urllib.request.Request(
    url= arg['domain'],
    data=postdata
    )

  html = openurl(req).read().decode('utf-8')

  if html != '7' :
    raise Exception("登陆失败")

  commit_num = int(math.sqrt(arg['endid'] - arg['startid']))

  # 补漏
  # id = [10122]
  
  if id != None:
    for i in id:
      commit_count+=1
      print("currentId : ", i)
      getBaiduPage(str(i))
      time.sleep(arg['wait_time'])
  else:
    for i in range(arg['startid'], arg['endid']):
      commit_count+=1
      print("currentId : ", i)
      getBaiduPage(str(i))
      time.sleep(arg['wait_time'])

  flag = True

  return flag


if __name__ == '__main__':
	
  create_()
  
  # 用户名 及 密码
  while True:
    user = input('input your username:')
    pwd = input('input your password:')
    if len(user) != 0 and len(pwd) != 0:
      pass
    elif len(user) == 0 and len(pwd) == 0:
      user = "xxxx"
      pwd  = "xxxx"
      print('使用默认账户')
      
    else:
      print('错误的输入')
      continue

    break
  
  
  # http://www.itjiaocheng.com/user/login.php
  # 0~10150
  
  # 测试网站
  dom='http://www.itjiaocheng.com/user/login_ajax.php'
  
  try:
    flag = login_(username=user,password=pwd,domain=dom, startid = 0, endid = 10224, wait_time = 0.001)
    if not flag:
      print('读取失败!')
      exit(0)
    else:
      print('读取成功')
  
  except Exception as e:
     print('Error:',e)
  
  close_()