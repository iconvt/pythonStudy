import logging; logging.basicConfig(level=logging.INFO)
import asyncio,aiomysql
# from orm import Model,StringField,IntegerField

# 基础数据库连接池（需要开始就初始化）
@asyncio.coroutine
def create_pool(loop,**kw):
    logging.info("create database connetion pool...")
    global __pool
    __pool = yield from aiomysql.create_pool(
        host = kw.get('host','localhost'),
        port = kw.get('port',3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset','utf8'),
        autocommit = kw.get('autocommit',True),
        maxsize = kw.get('maxsize',10),
        minsize = kw.get('minsize',1),
        loop=loop
    )

# 数据库基本查询函数
@asyncio.coroutine
def select(sql,args,size=None):
    # log(sql,args)
    global __pool
    with (yield from __pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replace('?','%s'),args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs

# 数据库基本执行函数
@asyncio.coroutine
def execute(sql,args):
    logs(sql)
    global __pool
    with (yield from __pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?','%s'),args)
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return affected
def create_args_string(q):
    pass

# orm字段基础类
class Field(object):
    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
    # 魔术方法当成字符串时调用
    def __str__(self): 
        return '<%s, %s:%s>' % (self.__class__.__name__,self.column_type,self.name)
# varchar字段类
class StringField(Field):
    def __init__(self,name=None,primary_key=False,default=None,ddl='varchar(100)'):
        super().__init__(name,ddl,primary_key,default)
# Int字段类
class IntegerField(Field):
    def __init__(self,name=None,primary_key=False,default=None,ddl='int(12)'):
        super().__init__(name,ddl,primary_key,default)

# 元类,用于改变Model的行为,有点像php的类的映射 (在这里主要的工作是映射Model的字段,加载主键,以及默认的方类的方法)
class ModelMetaclass(type):
    def __new__(cls,name,bases,attrs):
        if name == "Model":
            return type.__new__(cls,name,bases,attrs)
        tableName = attrs.get('__table__',None) or name
        logging.info('found model:%s (table: %s)' % (name,tableName))
        mappings=dict()
        fields=[]
        primaryKey=None
        for k, v in attrs.items():
            if isinstance(v,Field):
                logging.info('found mapping->field:%s ==> %s' % (k,v))
                mappings[k]=v
                if v.primary_key:
                    logging.info('found primaryKey:%s ' % k)
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey=k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f:'`%s`' % f,fields))
        attrs['__mapping__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primaryKey__'] = primaryKey
        attrs['__fields__'] = fields
        attrs['__select__'] = 'select `%s`,%s from `%s`' % (primaryKey,', '.join(escaped_fields),tableName)
        attrs['__insert__'] = 'insert into `%s` (%s ,`%s`) values (%s)' % (tableName,', '.join(escaped_fields),primaryKey,create_args_string(len(escaped_fields)+1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName,', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f),fields)),primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName,primaryKey)
        return type.__new__(cls,name,bases,attrs)

# 基本的Model类
class Model(dict,metaclass=ModelMetaclass):
    # 构造函数
    def __init__(self,**kw):
        super(Model,self).__init__(**kw)

    # 魔术方法获取属性值
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'"Model" object has no attribute "%s"' % key)
    # 魔术方法，设置属性值
    def __setattr__(self,key,value):
        self[key] = value
    # 获取属性值
    def getValue(self,key):
        return getattr(self,key,None)
    # 获取属性值，没有的话给默认值
    def getValueOrDefault(self,key):
        value=getattr(self,key,None)
        if value is None:
            field = self.__mapping__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key,str(value)))
                setattr(self,key,value)
        return value
    
    # 根据主键来查询数据
    @classmethod
    @asyncio.coroutine
    def find(cls,pk):
        ''' 根据主键来获取数据'''
        res = yield from select('%s where `%s`=?' % (cls.__select__,cls.__primaryKey__),[pk],1)
        logging.info('%s where `%s`=?' % (cls.__select__,cls.__primaryKey__))
        logging.info(type(res))
        logging.info(type(res[0]))
        logging.info(res[0])    #这里是一个字典,没有字段相关的信息
        if len(res) == 0:
            return None
        return cls(**res[0])    #这里又实例化了自身,返回一个Model

    # 添加数据入库
    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueOrDefault,self.__fields__))
        args.append(self.getValueOrDefault(self.__primaryKey__))
        rows = yield from execute(self.__insert__,args)
        if rows != 1:
            logging.warn('failed to insert recored: affected rows:%s' % rows)




