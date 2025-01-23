import ujson
import importlib
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import websockets

def load_config(config_file="config.json"):
    with open(config_file, "r") as file:
        config = ujson.load(file)
    return config

def action(name):
    def wrapper(func):
        if not hasattr(action_registry, "actions"):
            action_registry.actions = {}
        action_registry.actions[name] = func
        return func
    return wrapper

class Plugin:
    def before(self, action_name):
        def wrapper(func):
            if action_name not in plugin_registry.before_hooks:
                plugin_registry.before_hooks[action_name] = []
            plugin_registry.before_hooks[action_name].append(func)
            return func
        return wrapper
    
    def after(self, action_name):
        def wrapper(func):
            if action_name not in plugin_registry.after_hooks:
                plugin_registry.after_hooks[action_name] = []
            plugin_registry.after_hooks[action_name].append(func)
            return func
        return wrapper

plugin = Plugin()

class action_registry:
    actions = {}

class plugin_registry:
    before_hooks = {}
    after_hooks = {}

class HotReloadHandler(FileSystemEventHandler):
    def __init__(self, server):
        self.server = server

    def on_modified(self, event):
        """ 文件修改时触发热重载 """
        if event.src_path.endswith(".py"):
            print(f"File changed: {event.src_path}")
            self.server.reload_plugins()
            self.server.reload_apis()
        elif event.src_path == self.server.config_file:
            print(f"Config file changed: {event.src_path}")
            self.server.reload_config()

class WebSocketServer:
    def __init__(self):
        self.config_file = "config.json"
        self.load_config(self.config_file)
        self.API_PATH = self.config.get("API_PATH", "apis")
        self.PLUGIN_PATH = self.config.get("PLUGIN_PATH", "plugins")
        self.HOST = self.config.get("HOST", "localhost")
        self.PORT = self.config.get("PORT", 8765)
        self.loaded_apis = {}
        self.loaded_plugins = {}
        self.load_apis()
        self.load_plugins()
        # 设置文件监视，热重载配置文件
        self.setup_hot_reload()

    def load_config(self, config_file):
        """ 加载配置文件 """
        with open(config_file, "r") as f:
            self.config = ujson.load(f)

    def reload_config(self):
        """ 重新加载配置文件 """
        self.load_config(self.config_file)
        print("Config reloaded:")
        print(f"HOST: {self.HOST}, PORT: {self.PORT}, API_PATH: {self.API_PATH}, PLUGIN_PATH: {self.PLUGIN_PATH}")

    def load_apis(self):
        """ 动态加载 APIs 文件夹中的 action """
        for api_file in Path(self.API_PATH).glob('*.py'):
            if api_file.stem != '__init__':
                module_name = f'{self.API_PATH}.{api_file.stem}'
                if module_name not in self.loaded_apis:
                    module = importlib.import_module(module_name)
                    self.loaded_apis[module_name] = module

    def load_plugins(self):
        """ 加载 Plugins 文件夹中的自定义 matcher """
        for plugin_file in Path(self.PLUGIN_PATH).glob('*.py'):
            if plugin_file.stem != '__init__':
                module_name = f'{self.PLUGIN_PATH}.{plugin_file.stem}'
                if module_name not in self.loaded_plugins:
                    importlib.import_module(module_name)
                    self.loaded_plugins[module_name] = module_name

    def reload_apis(self):
        """ 重载 APIs """
        for api_name, module in self.loaded_apis.items():
            try:
                importlib.reload(module)
                print(f"API {api_name} reloaded")
            except Exception as e:
                print(f"Failed to reload API {api_name}: {str(e)}")

    def reload_plugins(self):
        """ 重载 Plugins """
        for plugin_name in self.loaded_plugins.values():
            try:
                importlib.reload(importlib.import_module(plugin_name))
                print(f"Plugin {plugin_name} reloaded")
            except Exception as e:
                print(f"Failed to reload Plugin {plugin_name}: {str(e)}")

    def setup_hot_reload(self):
        """ 设置文件监视器以实现热重载 """
        event_handler = HotReloadHandler(self)
        observer = Observer()
        observer.schedule(event_handler, self.API_PATH, recursive=True)
        observer.schedule(event_handler, self.PLUGIN_PATH, recursive=True)
        observer.schedule(event_handler, self.config_file, recursive=False)  # 监视配置文件变化
        observer.start()

    async def handle_request(self, websocket):
        """ 处理来自客户端的请求 """
        while True:
            try:
                message = await websocket.recv()
                request = ujson.loads(message)
                action_name = request.get('action')
                data = request.get('data', {})
    
                # 查找 action 处理函数
                if action_name in action_registry.actions:
                    # 处理 before 插件
                    for hook in plugin_registry.before_hooks.get(action_name, []):
                        data = await hook(data)
    
                    # 执行 action
                    action_func = action_registry.actions[action_name]
                    result = await action_func(data)
    
                    # 处理 after 插件
                    for hook in plugin_registry.after_hooks.get(action_name, []):
                        result = await hook(result)
    
                    # 返回结果
                    await websocket.send(ujson.dumps({'status': 'success', 'result': result}, ensure_ascii=False))
                else:
                    await websocket.send(ujson.dumps({'status': 'error', 'message': f'Unknown action: "{action_name}"'}, ensure_ascii=False))
                
            except ujson.JSONDecodeError:
                await websocket.send(ujson.dumps({'status': 'error', 'message': '错误的格式'}, ensure_ascii=False))
            except websockets.exceptions.ConnectionClosed as e:
                print(f"Connection closed: {e.code} - {e.reason}")
                await websocket.send(ujson.dumps({'status': 'error', 'message': 'Connection closed'}, ensure_ascii=False))
    
            except Exception as e:
                await websocket.send(ujson.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False))

    async def run(self):
        """ 启动 WebSocket 服务器 """
        server = await websockets.serve(self.handle_request, self.HOST, self.PORT)
        print(f"Server is starting on {self.HOST}:{self.PORT}")
        await server.serve_forever()
