import os
from typing import Any
from dotenv import load_dotenv
from pathlib import Path

cwd = Path.cwd()


class Config:
    content = {}

    @classmethod
    def load_env(cls):
        # 读取主.env文件
        env_path = cwd / ".env"
        load_dotenv(dotenv_path=env_path)

        # 获取 environment 参数
        environment = os.getenv("ENVIRONMENT", "dev").upper()
        specific_env_path = cwd / f".env.{environment.lower()}"
        load_dotenv(dotenv_path=specific_env_path, override=True)

        # 合并加载的环境变量到配置中，全部大写键名
        cls.content = {}
        for key, value in os.environ.items():
            if key.isupper():
                cls.content[key] = cls.convert_value(value)

    @staticmethod
    def convert_value(value: str) -> Any:
        # 尝试将字符串转换为相应的类型
        try:
            if value.lower() in ["true", "false"]:
                return value.lower() == "true"
            return float(value) if "." in value else int(value)
        except ValueError:
            return value

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        获取配置项的值，如果不存在则返回默认值。

        :param key: 配置项的键
        :param default: 默认值
        :return: 返回配置项的值，类型可能是 int, str, list, float 或 bool
        """
        if cls.content is None:
            cls.load_env()  # 读取配置文件
        return cls.content.get(key.upper(), default)
