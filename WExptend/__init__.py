import os
import asyncio
import websockets
import logging
from WExptend.config import Config, cwd
from WExptend.handler import handle_request
from WExptend.log import logger
from WExptend.manager import HotReloadServer


init_done = False  # 用于跟踪 init 是否已执行

# 获取 websockets 模块的日志记录器并禁用日志输出
logging.getLogger("websockets").setLevel(logging.CRITICAL)


def init():
    """初始化配置"""
    global init_done
    if not os.path.exists(cwd / ".env"):
        with open(cwd / ".env", "w") as f:
            f.write("ENVIRONMENT=pro")

    environment = Config.get("environment", "pro")  # 默认值为 "pro"
    if not os.path.exists(cwd / f".env.{environment}"):
        with open(cwd / f".env.{environment}", "w") as f:
            f.write("HOST=0.0.0.0\nPORT=8765")

    os.makedirs(cwd / "plugins", exist_ok=True)
    os.makedirs(cwd / "routers", exist_ok=True)
    init_done = True


async def main():
    """启动服务器"""
    if not init_done:
        raise RuntimeError("Initialization not done. Please run init() before main().")

    host = Config.get("host", "0.0.0.0")
    port = int(Config.get("port", 8765))

    async with websockets.serve(handle_request, host, port):  # type: ignore
        logger.success(f"Server is running on {host}:{port}")
        await asyncio.Future()  # Run forever


def run():
    run_hot_reload()
    asyncio.run(main())


server = HotReloadServer()


def load_plugins(path: str):
    """加载插件"""
    server.load_plugins(path)


def reload_plugins():
    """重载插件"""
    server.reload_plugins()


def load_routers(path: str):
    """加载路由"""
    server.load_routers(path)


def reload_routers():
    """重载路由"""
    server.reload_routers()


def run_hot_reload():
    """启动文件监视器"""
    server.run()


def restart_hot_reload():
    """重启文件监视器"""
    server.restart()
