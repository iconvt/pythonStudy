import logging; logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time
from datetime import datetime

from aiohttp import web

from www import myorm
from www.adminModel import Admin

@asyncio.coroutine
def index(request): # 首页网站
	userData=yield from Admin.find(57835)   # 查询数据库的用户id为57835的用户信息,返回的是一个Model(也是字典)
	logging.info(userData)
	logging.info(userData.__mapping__)  # 存的是各字段的信息
	logging.info(userData.__fields__)  # 存的是各字段名称 主键单独的
	logging.info(userData.__primaryKey__)  # 存的是主键名称
	return web.Response(body='<h1>Awesome</h1> name=>%s' % userData.a_realname)

@asyncio.coroutine
def init(loop):
	# 创建应用
    app = web.Application(loop=loop)
    # 应该是路由吧
    app.router.add_route("GET",'/',index)
    srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    #创建一个数据库连接池 global __pool
    yield from myorm.create_pool(loop,user='root',db='hz30',password='')   
    return srv
def logs(log):
	logging.debug(log)


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
