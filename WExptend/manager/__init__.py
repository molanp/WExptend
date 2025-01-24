from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from WExptend.manager.plugin import PluginLoader
from WExptend.manager.router import RouterLoader
from WExptend.log import logger

class HotReloadHandler(FileSystemEventHandler):
    def __init__(self, server):
        self.server = server

    def on_modified(self, event):
        """ 文件修改时触发热重载 """
        if event.src_path.endswith(".py"): # type: ignore
            logger.trace(f"File changed: {event.src_path}")
            self.server.reload_plugins()
            self.server.reload_routers()
        elif event.src_path == self.server.config_file:
            logger.trace(f"Config file changed: {event.src_path}")
            self.server.reload_config()

class HotReloadServer:
    def __init__(self):
        self.observer = Observer()
        self.plugin_paths = set()
        self.router_paths = set()
        self.config_file = None

    def load_plugins(self, path: str):
        """加载插件并将文件夹加入监听列表"""
        PluginLoader.load_plugins(path)
        self.plugin_paths.add(path)
        self.observer.schedule(HotReloadHandler(self), path, recursive=True)

    def reload_plugins(self):
        """重载插件"""
        PluginLoader.reload_plugins()

    def load_routers(self, path: str):
        """加载路由并将文件夹加入监听列表"""
        RouterLoader.load_routers(path)
        self.router_paths.add(path)
        self.observer.schedule(HotReloadHandler(self), path, recursive=True)

    def reload_routers(self):
        """重载路由"""
        RouterLoader.reload_routers()

    def run(self):
        """启动文件监视器"""
        self.observer.start()

    def restart(self):
        """重启文件监视器"""
        self.observer.stop()
        self.observer.join()
        self.observer = Observer()
        for path in self.plugin_paths:
            self.observer.schedule(HotReloadHandler(self), path, recursive=True)
        for path in self.router_paths:
            self.observer.schedule(HotReloadHandler(self), path, recursive=True)
        self.run()
