# WExptend
一个高性能、可拓展的 WebSocket 服务端框架

**WExptend** 是一个高性能、可拓展的 WebSocket 框架，旨在构建可扩展且灵活的实时应用程序。该框架内置插件化路由与匹配支持，允许您轻松扩展功能并集成自定义逻辑到 WebSocket 应用中。

## 特性

- **WebSocket 支持**：无缝处理 WebSocket 连接和消息。
- **可拓展性**：采用模块化设计，便于通过插件扩展功能。
- **灵活路由**：使用自定义路由逻辑，根据定义的模式引导 WebSocket 流量。
- **插件架构**：在不修改核心代码的情况下添加新功能或自定义行为。
- ~~**热重载**：自动监测并刷新插件和路由的更新。~~(这个测试的时候发现没用，还在修)

## 安装

要安装 **WExptend**，只需使用 `pip` 。

```shell
pip install wexptend
```

## 基本使用

以下是一个使用 **WExptend** 设置 WebSocket 服务器的基础示例：

```py
import WExptend

WExptend.init()

WExptend.load_plugins("plugins")

WExptend.load_routers("routers") #如果你不加载路由，加载再多的插件也没用

WExptend.run()
```

后期计划是像nonebot那样可以指定插件文件夹之类的

## 文档

欲了解更多信息，请查看完整文档：

[正在写](#)

## 贡献

我们欢迎贡献！要贡献代码，请 fork 仓库、创建新分支并提交 Pull Request。

## 许可证

**WExptend** 使用 MIT 许可证。更多详情请参见 [LICENSE](LICENSE) 文件。
