import sys
from pathlib import Path
from collections import defaultdict
from typing import Callable
from WExptend.log import logger
import importlib

from WExptend.manager.router import RouteMatcher


class PluginRegistry:
    _hooks = defaultdict(lambda: defaultdict(list))

    @classmethod
    def add_hook(cls, hook_type: str, event: str, func: Callable, priority: int):
        hooks = cls._hooks[hook_type][event]
        if all(f is not func for p, f in hooks):
            hooks.append((priority, func))
            hooks.sort(key=lambda x: x[0], reverse=True)
            logger.debug(f"Registered {hook_type} hook for {event}")

    @classmethod
    async def process_hooks(cls, hook_type: str, event: str, data):
        hooks = cls._hooks[hook_type].get(event, [])
        for p, hook in hooks:
            try:
                data = await hook(data)
            except Exception as e:
                logger.error(f"Hook {hook.__name__} failed: {str(e)}")
        return data


class Plugin:
    @classmethod
    def on_system_event(cls, event_type: str, priority: int = 5):
        """系统事件钩子（仅限框架内部使用）"""
        if event_type not in RouteMatcher.SYSTEM_EVENTS:
            raise ValueError(f"Invalid system event: {event_type}")

        def decorator(func):
            PluginRegistry.add_hook("pre", f"system:{event_type}", func, priority)
            return func

        return decorator

    @classmethod
    def on_action(cls, pattern: str = ".*", priority: int = 5):
        """支持正则的action钩子"""

        def decorator(func):
            PluginRegistry.add_hook("pre", f"action_regex:{pattern}", func, priority)
            return func

        return decorator


class PluginLoader:
    PLUGIN_PATH = set()
    loaded_plugins = {}

    @classmethod
    def load_plugins(cls, path: str):
        path_ = Path(path).resolve()
        if path_ not in cls.PLUGIN_PATH:
            logger.trace(f"Loading plugin path: {path_}")
            cls.PLUGIN_PATH.add(path_)

            for plugin_file in path_.glob("*.py"):
                module_name = f"{path_.stem}.{plugin_file.stem}"
                if module_name not in cls.loaded_plugins:
                    try:
                        module = importlib.import_module(module_name)
                        cls.loaded_plugins[module_name] = module
                        logger.success(f"Loaded plugin: {module_name}")
                    except Exception as e:
                        logger.error(f"Failed to load {module_name}: {str(e)}")

    @classmethod
    def reload_plugins(cls):
        PluginRegistry._hooks.clear()
        for module_name in list(cls.loaded_plugins.keys()):
            if module_name in sys.modules:
                del sys.modules[module_name]
        cls.loaded_plugins.clear()
        for path in cls.PLUGIN_PATH:
            cls.load_plugins(str(path))
