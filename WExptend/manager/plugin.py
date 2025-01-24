from pathlib import Path
from WExptend.log import logger
from collections import defaultdict
import importlib


class PluginLoader:
    PLUGIN_PATH = set()
    loaded_plugins = {}

    @classmethod
    def load_plugins(cls, path: str):
        """ 加载 Plugins 文件夹中的自定义 matcher """
        path_ = Path(path).resolve()  # 转换为绝对路径
        if path_ not in cls.PLUGIN_PATH:
            logger.trace(f"Prepare to load plugin folder {path_}")
            cls.PLUGIN_PATH.add(path_)
            for plugin_file in path_.glob('*.py'):
                logger.trace(f"Prepare to load plugin {plugin_file}")
                module_name = f'{path_.stem}.{plugin_file.stem}'
                if module_name not in cls.loaded_plugins:
                    importlib.import_module(module_name)
                    cls.loaded_plugins[module_name] = module_name
                    logger.success(
                        f"Loaded plugin {plugin_file.stem} from {module_name}")
                else:
                    logger.warn(
                        f"Duplicate plugin '{module_name}' has been ignored")
        else:
            logger.warn(f"Path {path_} cannot be loaded more than once")

    @classmethod
    def reload_plugins(cls):
        """ 重载 Plugins """
        for plugin_name in cls.loaded_plugins.values():
            try:
                importlib.reload(importlib.import_module(plugin_name))
                logger.info(f"Plugin {plugin_name} reloaded")
            except Exception as e:
                logger.error(
                    f"Failed to reload plugin {plugin_name}: {str(e)}")


class Plugin:
    @classmethod
    def pre_process(cls, action_name: str, priority=5):
        def wrapper(func):
            if action_name not in PluginRegistry.pre_hooks:
                PluginRegistry.pre_hooks[action_name] = []
            PluginRegistry.pre_hooks[action_name].append((priority, func))
            PluginRegistry.pre_hooks[action_name].sort(reverse=True)  # 按优先级排序
            return func
        return wrapper

    @classmethod
    def post_process(cls, action_name: str, priority=5):
        def wrapper(func):
            if action_name not in PluginRegistry.post_hooks:
                PluginRegistry.post_hooks[action_name] = []
            PluginRegistry.post_hooks[action_name].append((priority, func))
            PluginRegistry.post_hooks[action_name].sort(reverse=True)  # 按优先级排序
            return func
        return wrapper


class PluginRegistry:
    pre_hooks = defaultdict(list)
    post_hooks = defaultdict(list)
