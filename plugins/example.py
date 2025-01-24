from WExptend.manager.plugin import Plugin

@Plugin.pre_process("test")
async def _(data):
    """ 路由前检查 """
    data["pre_process"] = "done"
    return data