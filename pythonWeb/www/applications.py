import functools
# 定义函数映射
def get(path):
	'''
	Define decorator @get('/path')
	'''
	def decorator(func):
		@functools.wraps(func)  #这里又是装饰器，把函数wrapper传进去
		def wrapper(*args,**kw):
			return func(*args,**kw)
		wrapper.__method__ = "GET"
		wrapper.__route__ = path
		return wrapper
	return decorator

def post(path):
	'''
	Define decorator @post('/path')
	'''
	def decorator(func):
		@functools.wraps(func)  #这里又是装饰器，把函数wrapper传进去
		def wrapper(*args,**kw):
			return func(*args,**kw)
		wrapper.__method__ = "POST"
		wrapper.__route__ = path
		return wrapper
	return decorator

@get('/index')
def index():
	return '啦啦啦啦啦'

@post('/blog')
def blog():
	return '不是博克拉'