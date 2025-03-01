# router.py 完整改造
from pathlib import Path
import sys
import re
import inspect
import importlib
from typing import Callable, Optional
from collections import defaultdict
from WExptend.log import logger
from WExptend.exceptions.router import RouteRegistrationError


class RouteMatcher:
    """路由匹配器基类"""

    SYSTEM_EVENTS = {"connect", "disconnect", "heartbeat"}

    def __init__(self, match_type: str, pattern, priority: int = 1):
        """
        :param match_type: 匹配类型
            - 'exact': 精确匹配action
            - 'regex': 正则匹配action
            - 'event': 系统事件
        """
        self.match_type = match_type
        self.pattern = re.compile(pattern) if match_type == "regex" else pattern
        self.priority = priority

        if match_type == "event" and pattern in self.SYSTEM_EVENTS:
            raise ValueError(f"Cannot register system event: {pattern}")

    def __call__(self, func):
        frame = inspect.currentframe().f_back.f_back  # type: ignore
        file_path = frame.f_code.co_filename  # type: ignore
        RouteRegistry.register(self, func, file_path)
        return func


# 新装饰器体系 --------------------------------------------------
def on_command(action_name: str, priority: int = 1):
    """精确匹配action"""
    _validate_action_name(action_name)
    return RouteMatcher("exact", action_name, priority)


def on_regex(pattern: str, priority: int = 2):
    """正则匹配action"""
    return RouteMatcher("regex", pattern, priority)


def on_event(event_type: str, priority: int = 0):
    """自定义事件（非系统事件）"""
    return RouteMatcher("event", event_type, priority)


def _validate_action_name(name: str):
    """验证action命名规范"""
    if name in RouteMatcher.SYSTEM_EVENTS:
        raise ValueError(f"Action name {name} is reserved")
    if not re.match(r"^[a-zA-Z_]\w*$", name):
        raise ValueError("Invalid action name format")


class RouteRegistry:
    """路由注册中心"""

    _routes = {
        "exact": defaultdict(list),
        "regex": [],
        "event": defaultdict(list),
    }

    @classmethod
    def register(cls, matcher: RouteMatcher, func: Callable, file_path: str):
        # 冲突检测
        if matcher.match_type == "exact":
            if existing := next(
                (
                    r
                    for r in cls._routes["exact"][matcher.pattern]
                    if r["matcher"].priority == matcher.priority
                ),
                None,
            ):
                raise RouteRegistrationError(
                    matcher.pattern, existing["file_path"], file_path
                )

        # 存储路由
        entry = {"matcher": matcher, "func": func, "file_path": file_path}
        match matcher.match_type:
            case "exact":
                cls._routes["exact"][matcher.pattern].append(entry)
                cls._routes["exact"][matcher.pattern].sort(
                    key=lambda x: x["matcher"].priority, reverse=True
                )
            case "regex":
                cls._routes["regex"].append(entry)
                cls._routes["regex"].sort(
                    key=lambda x: x["matcher"].priority, reverse=True
                )
            case "event":
                cls._routes["event"][matcher.pattern].append(entry)

        logger.debug(f"Registered {matcher.match_type} route: {matcher.pattern}")

    @classmethod
    def get_handler(cls, request: dict) -> Optional[Callable]:
        """纯action路由匹配"""
        # 系统事件处理
        if event_type := request.get("event_type"):
            return next(
                (e["func"] for e in cls._routes["event"].get(event_type, [])), None
            )

        if action := request.get("action"):
            # 精确匹配优先
            return (
                exact_handlers[0]["func"]
                if (exact_handlers := cls._routes["exact"].get(action))
                else next(
                    (
                        regex_entry["func"]
                        for regex_entry in cls._routes["regex"]
                        if regex_entry["matcher"].pattern.match(action)
                    ),
                    None,
                )
            )
        else:
            return None


class RouterLoader:
    """路由加载器"""

    ROUTER_PATH = set()
    loaded_routers = {}

    @classmethod
    def load_routers(cls, path: str):
        path_ = Path(path).resolve()
        if path_ not in cls.ROUTER_PATH:
            logger.trace(f"Loading router path: {path_}")
            cls.ROUTER_PATH.add(path_)
            for router_file in path_.glob("*.py"):
                module_name = f"{path_.stem}.{router_file.stem}"
                if module_name not in cls.loaded_routers:
                    try:
                        module = importlib.import_module(module_name)
                        cls.loaded_routers[module_name] = module
                        logger.success(f"Loaded router: {module_name}")
                    except Exception as e:
                        logger.error(f"Failed to load {module_name}: {str(e)}")

    @classmethod
    def reload_routers(cls):
        """完全重载路由的修复方案"""
        # 1. 清空路由注册表
        RouteRegistry._routes = {
            "exact": defaultdict(list),
            "regex": [],
            "event": defaultdict(list),
        }

        # 2. 清除模块缓存
        for module_name in list(cls.loaded_routers.keys()):
            if module_name in sys.modules:
                # 递归删除子模块
                for submodule in list(sys.modules.keys()):
                    if submodule.startswith(module_name.split(".")[0]):
                        del sys.modules[submodule]

        # 3. 重置加载记录
        cls.loaded_routers.clear()
        original_paths = list(cls.ROUTER_PATH)
        cls.ROUTER_PATH.clear()

        # 4. 重新加载路由
        for path in original_paths:
            cls.load_routers(str(path))
