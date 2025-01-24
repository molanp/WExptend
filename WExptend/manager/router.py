from pathlib import Path
from WExptend.log import logger
import importlib
import inspect
from WExptend.exceptions.router import RouteRegistrationError


class RouterLoader:
    ROUTER_PATH = set()
    loaded_routers = {}

    @classmethod
    def load_routers(cls, path: str):
        """ 动态加载 Routers 文件夹中的 action """
        path_ = Path(path).resolve()  # 转换为绝对路径
        if str(path_) not in cls.ROUTER_PATH:
            logger.trace(f"Prepare to load router folder {path_}")
            cls.ROUTER_PATH.add(path_)
            for router_file in path_.glob('*.py'):
                logger.trace(f"Prepare to load router {router_file}")
                module_name = f'{path_.stem}.{router_file.stem}'
                if module_name not in cls.loaded_routers:
                    module = importlib.import_module(module_name)
                    cls.loaded_routers[module_name] = module
                    logger.success(f"Loaded router {module_name} from {router_file}")
                else:
                    logger.warn(f"Duplicate router '{module_name}' has been ignored")
        else:
            logger.warn(f"Path {path_} cannot be loaded more than once")

    @classmethod
    def reload_routers(cls):
        """ 重载 Routers """
        for router_name, module in cls.loaded_routers.items():
            try:
                importlib.reload(module)
                logger.info(f"Router {router_name} reloaded")
            except Exception as e:
                logger.error(f"Failed to reload router {router_name}: {str(e)}")

class RouteRegistry:
    routes = {}

def register_router(name):
    def wrapper(func):
        current_frame = inspect.currentframe()
        caller_frame = inspect.getouterframes(current_frame, 2)
        file_path = caller_frame[1].filename

        if name in RouteRegistry.routes:
            existing_file = RouteRegistry.routes[name]['file_path']
            raise RouteRegistrationError(name, existing_file, file_path)
        
        RouteRegistry.routes[name] = {'func': func, 'file_path': file_path}
        return func
    return wrapper