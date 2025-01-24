import ujson
import websockets
from WExptend.manager.router import RouteRegistry
from WExptend.manager.plugin import PluginRegistry
from WExptend.log import logger
from WExptend.exceptions import handle_exception


async def handle_request(websocket):
    """ 处理来自客户端的请求 """
    client_ip = websocket.remote_address[0]  # 获取客户端 IP 地址
    logger.success(f"New connection from {client_ip}")

    while True:
        try:
            message = await websocket.recv()
            request = ujson.loads(message)
            if not (isinstance(request, dict) and "action" in request.keys() and "data" in request.keys()):
                await websocket.send(ujson.dumps({'status': 'error', 'message': 'Invalid message format.'}, ensure_ascii=False))
                continue
            action_name = request.get('action')
            data = request.get('data', {})
            logger.success(
                f"Received from {client_ip}: {action_name} - {data}")

            # 查找 action 处理函数
            if action_name in RouteRegistry.routes:
                # 处理 pre_process 插件
                if action_name in PluginRegistry.pre_hooks:
                    for priority, hook in sorted(PluginRegistry.pre_hooks[action_name], reverse=True):
                        data = await hook(request)

                # 执行动作
                action_func = RouteRegistry.routes[action_name]['func']
                result = await action_func(request)

                # 处理 post_process 插件
                if action_name in PluginRegistry.post_hooks:
                    for priority, hook in sorted(PluginRegistry.post_hooks[action_name], reverse=True):
                        result = await hook(request)

                # 返回结果
                await websocket.send(ujson.dumps({'status': 'success', 'result': result}, ensure_ascii=False))
            else:
                await websocket.send(ujson.dumps({'status': 'error', 'message': f'Unknown action: "{action_name}"'}, ensure_ascii=False))

        except ujson.JSONDecodeError:
            await websocket.send(ujson.dumps({'status': 'error', 'message': 'Invalid message format.'}, ensure_ascii=False))
        except websockets.exceptions.ConnectionClosed as e:
            logger.warn(f"Connection closed: {e.code} - {e.reason}")
            await websocket.send(ujson.dumps({'status': 'error', 'message': 'Connection closed'}, ensure_ascii=False))
        except Exception as e:
            error_message = await handle_exception(e)
            await websocket.send(ujson.dumps({'status': 'error', 'message': error_message}, ensure_ascii=False))
