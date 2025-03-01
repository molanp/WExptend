from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from WExptend.manager.plugin import PluginLoader
from WExptend.manager.router import RouterLoader
from WExptend.log import logger


class HotReloadHandler(FileSystemEventHandler):
    def __init__(self, server):
        self.server = server

    def on_modified(self, event):
        if str(event.src_path).endswith(".py"):
            logger.trace(f"Detected file change: {event.src_path}")
            PluginLoader.reload_plugins()
            RouterLoader.reload_routers()


class HotReloadServer:
    def __init__(self):
        self.observer = Observer()
        self.plugin_paths = set()
        self.router_paths = set()
        self.config_file = None

    def load_plugins(self, path: str):
        """加载插件并将文件夹加入监听列表"""
        if path in self.plugin_paths:
            return
        PluginLoader.load_plugins(path)
        self.plugin_paths.add(path)
        self.observer.schedule(HotReloadHandler(self), path, recursive=True)

    def reload_plugins(self):
        """重载插件"""
        PluginLoader.reload_plugins()

    def load_routers(self, path: str):
        """加载路由并将文件夹加入监听列表"""
        if path in self.router_paths:  # 新增判断
            return
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
