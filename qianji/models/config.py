"""
配置模型 - 对应 OpenClaw 的 browser/config.js
"""

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProfileConfig:
    """浏览器配置文件"""

    name: str
    cdp_port: int | None = None
    cdp_url: str | None = None
    color: str = "#FF4500"
    headless: bool = True
    no_sandbox: bool = False
    executable_path: str | None = None
    user_data_dir: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    driver: str = "playwright"  # "playwright" or "cdp"

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "ProfileConfig":
        """从字典创建配置"""
        return cls(
            name=name,
            cdp_port=data.get("cdpPort"),
            cdp_url=data.get("cdpUrl"),
            color=data.get("color", "#FF4500"),
            headless=data.get("headless", True),
            no_sandbox=data.get("noSandbox", False),
            executable_path=data.get("executablePath"),
            user_data_dir=data.get("userDataDir"),
            args=data.get("args", []),
            env=data.get("env", {}),
            driver=data.get("driver", "playwright"),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "cdpPort": self.cdp_port,
            "cdpUrl": self.cdp_url,
            "color": self.color,
            "headless": self.headless,
            "noSandbox": self.no_sandbox,
            "executablePath": self.executable_path,
            "userDataDir": self.user_data_dir,
            "args": self.args,
            "env": self.env,
            "driver": self.driver,
        }


@dataclass
class BrowserConfig:
    """浏览器全局配置 - 对应 OpenClaw browser/config.js"""

    enabled: bool = True
    headless: bool = True
    no_sandbox: bool = False
    attach_only: bool = False
    executable_path: str | None = None
    default_profile: str = "default"
    color: str = "#FF4500"
    remote_cdp_timeout_ms: int = 1500
    remote_cdp_handshake_timeout_ms: int = 3000
    profiles: dict[str, ProfileConfig] = field(default_factory=dict)

    # 控制服务端口 (gateway.port + 2)
    control_port: int = 18796
    relay_port: int = 18792

    @classmethod
    def from_env(cls) -> "BrowserConfig":
        """从环境变量加载配置"""
        config = cls()

        # 全局设置
        config.enabled = os.environ.get("QIANJI_ENABLED", "true").lower() == "true"
        config.headless = os.environ.get("QIANJI_HEADLESS", "true").lower() == "true"
        config.no_sandbox = os.environ.get("QIANJI_NO_SANDBOX", "false").lower() == "true"
        config.executable_path = os.environ.get("QIANJI_BROWSER_PATH")
        config.default_profile = os.environ.get("QIANJI_DEFAULT_PROFILE", "default")

        # 端口设置
        if "QIANJI_CONTROL_PORT" in os.environ:
            config.control_port = int(os.environ["QIANJI_CONTROL_PORT"])
            config.relay_port = config.control_port + 1

        # 加载配置文件
        config._load_profiles_from_env()

        return config

    def _load_profiles_from_env(self):
        """从环境变量加载配置文件"""
        # 默认配置文件
        default_profile = ProfileConfig(
            name="default",
            headless=self.headless,
            no_sandbox=self.no_sandbox,
            executable_path=self.executable_path,
        )
        self.profiles["default"] = default_profile

        # 从环境变量加载其他配置
        for key, value in os.environ.items():
            if key.startswith("QIANJI_PROFILE_"):
                parts = key.replace("QIANJI_PROFILE_", "").split("_")
                if len(parts) >= 2:
                    profile_name = parts[0].lower()
                    option = "_".join(parts[1:]).lower()

                    if profile_name not in self.profiles:
                        self.profiles[profile_name] = ProfileConfig(
                            name=profile_name,
                            headless=self.headless,
                            no_sandbox=self.no_sandbox,
                        )

                    profile = self.profiles[profile_name]
                    if option == "browser_path":
                        profile.executable_path = value
                    elif option == "headless":
                        profile.headless = value.lower() == "true"
                    elif option == "no_sandbox":
                        profile.no_sandbox = value.lower() == "true"
                    elif option == "cdp_port":
                        profile.cdp_port = int(value)
                    elif option == "cdp_url":
                        profile.cdp_url = value
                    elif option == "user_data_dir":
                        profile.user_data_dir = value

    def get_profile(self, name: str | None = None) -> ProfileConfig:
        """获取配置文件"""
        name = name or self.default_profile
        if name not in self.profiles:
            # 创建新配置
            self.profiles[name] = ProfileConfig(
                name=name,
                headless=self.headless,
                no_sandbox=self.no_sandbox,
                executable_path=self.executable_path,
            )
        return self.profiles[name]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "headless": self.headless,
            "noSandbox": self.no_sandbox,
            "attachOnly": self.attach_only,
            "executablePath": self.executable_path,
            "defaultProfile": self.default_profile,
            "color": self.color,
            "remoteCdpTimeoutMs": self.remote_cdp_timeout_ms,
            "remoteCdpHandshakeTimeoutMs": self.remote_cdp_handshake_timeout_ms,
            "controlPort": self.control_port,
            "relayPort": self.relay_port,
            "profiles": {name: profile.to_dict() for name, profile in self.profiles.items()},
        }
