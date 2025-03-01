import ujson
import websockets
from typing import Dict, Any
from WExptend.log import logger
from WExptend.manager.router import RouteRegistry, RouteMatcher
from WExptend.manager.plugin import PluginRegistry
from WExptend.exceptions import handle_exception


async def handle_request(websocket: websockets.WebSocketServerProtocol):  # type: ignore
    client_ip = websocket.remote_address[0]
    logger.info(f"Client connected: {client_ip}")

    try:
        # 发送连接事件（使用event_type）
        await _process_system_event(websocket, "connect", {"client_ip": client_ip})

        async for message in websocket:
            await _handle_message(websocket, client_ip, message)

    except websockets.exceptions.ConnectionClosed as e:
        logger.warn(f"Connection closed: {e.code}-{e.reason}")
        await _send_error(websocket, "Connection closed")
    except Exception as e:
        await _send_error(websocket, await handle_exception(e))
    finally:
        await _process_system_event(websocket, "disconnect", {"client_ip": client_ip})


async def _handle_message(websocket, client_ip, message):
    try:
        request = _parse_message(message)
        logger.debug(f"Request from {client_ip}: {request}")

        if "event_type" in request:
            await _send_error(websocket, "Client cannot send system events")
            return

        response = await _process_user_action(request)
        await _send_safe(websocket, response)

    except ujson.JSONDecodeError:
        await _send_error(websocket, "Invalid JSON format")
    except Exception as e:
        await _send_error(websocket, await handle_exception(e))


def _parse_message(message: str) -> Dict[str, Any]:
    request = ujson.loads(message)

    if not isinstance(request, dict):
        raise ValueError("Request must be a dictionary")

    # 验证事件类型
    has_event = "event_type" in request
    has_action = "action" in request

    if has_event and has_action:
        raise ValueError("Cannot have both event_type and action")
    if not has_event and not has_action:
        raise ValueError("Must have either event_type or action")

    if has_event and request["event_type"] not in RouteMatcher.SYSTEM_EVENTS:
        raise ValueError(f"Invalid system event: {request['event_type']}")

    if has_action:
        if not isinstance(request.get("data", {}), dict):
            raise ValueError("data must be dictionary")
        if request["action"] in RouteMatcher.SYSTEM_EVENTS:
            raise ValueError(f"Reserved action name: {request['action']}")

    return request


async def _process_system_event(websocket, event_type: str, data: dict):
    """处理系统事件"""
    request = {"event_type": event_type, "data": data}

    # 执行系统事件钩子
    processed_data = await PluginRegistry.process_hooks(
        "pre", f"system:{event_type}", data
    )

    if handler := RouteRegistry.get_handler(request):
        try:
            await handler({"data": processed_data})
        except Exception as e:
            logger.error(f"System event {event_type} failed: {str(e)}")


async def _process_user_action(request: Dict[str, Any]) -> Dict[str, Any]:
    """改造后的处理流程"""
    try:
        # 在预处理前注入原始action
        raw_data = {
            **request["data"],
            "_original_action": request["action"],  # 新增注入点
        }

        # 执行action预处理钩子（传递包含原始action的数据）
        processed_data = await PluginRegistry.process_hooks(
            "pre",
            f"action:{request['action']}",
            raw_data,  # 使用包含原始action的数据
        )

        if handler := RouteRegistry.get_handler({"action": request["action"]}):
            # 传递处理后的完整数据
            result = await handler(processed_data)
            final_result = await PluginRegistry.process_hooks(
                "post", f"action:{request['action']}", result
            )
            return {"status": "success", "data": final_result}

        return {"status": "error", "data": {"message": "No handler found"}}
    except Exception as e:
        return {"status": "error", "data": {"message": handle_exception(e)}}


async def _send_safe(websocket, response: Dict[str, Any]):
    try:
        await websocket.send(ujson.dumps(response, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Send failed: {str(e)}")


async def _send_error(websocket, message: str):
    await _send_safe(websocket, {"status": "error", "data": {"message": message}})
