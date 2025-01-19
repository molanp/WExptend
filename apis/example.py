from server import action

@action('e1')
async def example_action(data):
    """ 处理example_action的请求 """
    return {"message": "Action processed successfully", "data": data}
