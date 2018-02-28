import logging; logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time,inspect,jinja2
from datetime import datetime

from aiohttp import web

from www import myorm
# from www import applications
from www.adminModel import Admin

# # 定义函数映射
# def get(path):
# 	'''
# 	Define decorator @get('/path')
# 	'''
# 	def decorator(func):
# 		@functools.wraps(func)  #这里又是装饰器，把函数wrapper传进去
# 		def wrapper(*args,**kw):
# 			return func(*args,**kw)
# 		wrapper.__method__ = "GET"
# 		wrapper.__route__ = path
# 		return wrapper
# 	return decorator

# def post(path):
# 	'''
# 	Define decorator @post('/path')
# 	'''
# 	def decorator(func):
# 		@functools.wraps(func)  #这里又是装饰器，把函数wrapper传进去
# 		def wrapper(*args,**kw):
# 			return func(*args,**kw)
# 		wrapper.__method__ = "GET"
# 		wrapper.__route__ = path
# 		return wrapper
# 	return decorator

# 这里是处理请求handle
class app_requestHandle(object):

	def __init__(self,app,fn):
		self._app = app
		self._func = fn

	@asyncio.coroutine
	def __call__(self,request):   # 这个函数就相当于第一节里面的 def index(request): 
		# 这里可以集中做很多统一的事   request 中参数有哪些,怎么获取啊?要怎么传给kw啊
		kw = {}
		r = yield from self._func(**kw)
		return r
		# return web.Response(body=r)

# 注册路由处理函数
def app_add_route(app,fn):
	method = getattr(fn,'__method__',None)
	path = getattr(fn,'__route__',None)
	if path is None or method is None:
		raise ValueError("@get or @post not defined in %s" % str(fn))
	#如果这个处理函数不是迭代器，也不是协程 就执行下面的那个（不晓得是不是这个意思哦）
	if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
		fn = asyncio.coroutine(fn)
	logging.info('add route %s %s => %s(%s)' % (method,path,fn,', '.join(inspect.signature(fn).parameters.keys())))
	app.router.add_route(method,path,app_requestHandle(app,fn))

#自动根据模块名称获得模块信息，
def app_regiest_route(app,module_name):   
	n=module_name.rfind('.') #确认模块名称中.在右边出现的位置，没有找到返回-1
	if n==(-1):
		mod = __import__(module_name,globals(),locals()) # 导入模块，并传入有效的变量 
	else:
		name = module_name[n+1:]  #获得模块的名称
		mod = getattr(__import__(module_name[:n],globals(),locals(),[name]),name)
	for attr in dir(mod):
		if attr.startswith('_'):	#以什么开头
			continue
		fn = getattr(mod,attr)   # 其实就是模块里面的属性啊，方法啊的名称
		if callable(fn):		#如果是函数 就可以注册成为路由啦
			method = getattr(fn,'__method__',None)   
			path = getattr(fn,'__route__',None)
			if method and path:		#检查该方法是否拥有路由的属性
				app_add_route(app,fn) #注册路由
		
# @asyncio.coroutine
# def index(request): # 首页网站
# 	userData=yield from Admin.find(57835)   # 查询数据库的用户id为57835的用户信息,返回的是一个Model(也是字典)
# 	logging.info(userData)
# 	logging.info(userData.__mapping__)  # 存的是各字段的信息
# 	logging.info(userData.__fields__)  # 存的是各字段名称 主键单独的
# 	logging.info(userData.__primaryKey__)  # 存的是主键名称
# 	return web.Response(body='<h1>Awesome</h1> name=>%s' % userData.a_realname)


# 记录日志中间件
@asyncio.coroutine
def logger_factory(app, handler):
    @asyncio.coroutine
    def logger(request):
        # 记录日志:
        logging.info('Request: %s %s' % (request.method, request.path))
        # 继续处理请求:
        logging.info(type(handler))
        # return (yield from handler(request))
        # return request
    return logger

# 返回值中间件
@asyncio.coroutine
def response_factory(app, handler):
    @asyncio.coroutine
    def response(request):
        # 结果:
        r = yield from handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
        	pass

@asyncio.coroutine
def init(loop):
	# 创建应用
    # app = web.Application(loop=loop,middlewares=[
    # 	logger_factory,response_factory
    # 	])  #现在加入了中间件
    app = web.Application(loop=loop) 
    #加载模板引擎
    # init_jinja2(app,filters=dict(datetime=datetime_filter)) #filter是辅助函数吧,引擎内是否有自带的
    # 根据应用模块注册路由
    app_regiest_route(app,"www.applications") 
    # 应该是路由吧
    # app.router.add_route("GET",'/',index)
    srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    #创建一个数据库连接池 global __pool
    yield from myorm.create_pool(loop,user='root',db='hz30',password='')   
    return srv
def logs(log):
	logging.debug(log)



if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.run_until_complete(init(loop))
	loop.run_forever()
