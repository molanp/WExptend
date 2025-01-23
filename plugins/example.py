from server import plugin

# before插件：验证数据是否包含某个关键字段
@plugin.before('e1')
async def check_key(data):
    if 'key' not in data:
        raise ValueError("Missing 'key' in data")
    return data

# after插件：在响应中添加额外信息
@plugin.after('e1')
async def add_processed_flag(result):
    result['processed'] = True
    return result
