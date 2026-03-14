"""
浏览器管理器 - 对应 OpenClaw browser/chrome.js + profiles-service.js
"""

import os
from typing import Any

try:
    from patchright.async_api import Browser, BrowserContext, async_playwright
    USING_PATCHRIGHT = True
    print("[INFO] Using Patchright for enhanced stealth")
except ImportError:
    from playwright.async_api import Browser, BrowserContext, async_playwright
    USING_PATCHRIGHT = False
    print("[INFO] Using standard Playwright")

from ..models.config import BrowserConfig, ProfileConfig
from .tab_manager import TabManager


def get_default_user_data_dir() -> str:
    """获取默认的用户数据目录"""
    # 使用用户主目录下的 .qianji/user_data 文件夹
    base_dir = os.path.expanduser("~/.qianji")
    user_data_dir = os.path.join(base_dir, "user_data")
    os.makedirs(user_data_dir, exist_ok=True)
    return user_data_dir


# 反检测脚本 - 注入到每个页面以隐藏自动化特征
STEALTH_SCRIPTS = """
(() => {
    // 标记脚本已注入
    window.__stealth_injected = true;
    window.__stealth_step = 0;

    try {
        window.__stealth_step = 1;
        // 覆盖 navigator.webdriver - 多重防护
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
            configurable: true,
            enumerable: true
        });
        window.__stealth_step = 2;

    // 删除 chrome 自动化属性
    delete navigator.__proto__.webdriver;

    // 删除 window.cdc_ 开头的属性（Chrome DevTools Protocol 特征）
    Object.keys(window).forEach(key => {
        if (key.startsWith('cdc_') || key.startsWith('$cdc_') || key.startsWith('__webdriver')) {
            delete window[key];
        }
    });

    // 删除 document 上的自动化属性
    delete document.__webdriver_script_fn;
    delete document.$cdc_asdjflasutopfhvcZLmcfl_;
    delete document.cdc_adoQpoasnfa76pfcZLmcfl_;

    // 覆盖 navigator.webdriver 的 toString
    Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {
        get: () => false,
        configurable: true,
        enumerable: true
    });
    
    // 注入 window.chrome 对象
    if (!window.chrome) {
        window.chrome = {};
    }
    
    // 添加 chrome 运行时属性
    window.chrome.runtime = {
        id: undefined,
        OnInstalledReason: {
            CHROME_UPDATE: "chrome_update",
            INSTALL: "install",
            SHARED_MODULE_UPDATE: "shared_module_update",
            UPDATE: "update"
        },
        OnRestartRequiredReason: {
            APP_UPDATE: "app_update",
            OS_UPDATE: "os_update",
            PERIODIC: "periodic"
        },
        PlatformArch: {
            ARM: "arm",
            ARM64: "arm64",
            MIPS: "mips",
            MIPS64: "mips64",
            X86_32: "x86-32",
            X86_64: "x86-64"
        },
        PlatformNaclArch: {
            ARM: "arm",
            MIPS: "mips",
            MIPS64: "mips64",
            MIPS64_EL: "mips64el",
            MIPS_EL: "mipsel",
            X86_32: "x86-32",
            X86_64: "x86-64"
        },
        PlatformOs: {
            ANDROID: "android",
            CROS: "cros",
            LINUX: "linux",
            MAC: "mac",
            OPENBSD: "openbsd",
            WIN: "win"
        },
        RequestUpdateCheckStatus: {
            NO_UPDATE: "no_update",
            THROTTLED: "throttled",
            UPDATE_AVAILABLE: "update_available"
        }
    };
    
    // 添加 chrome app 属性
    window.chrome.app = {
        isInstalled: false,
        InstallState: {
            DISABLED: "disabled",
            INSTALLED: "installed",
            NOT_INSTALLED: "not_installed"
        },
        RunningState: {
            CANNOT_RUN: "cannot_run",
            READY_TO_RUN: "ready_to_run",
            RUNNING: "running"
        }
    };
    
    // 添加 chrome csi 属性
    window.chrome.csi = function() {
        return {
            onloadT: Date.now(),
            pageT: Date.now() - performance.timing.navigationStart,
            startE: performance.timing.navigationStart,
            type: "nav"
        };
    };
    
    // 添加 chrome loadTimes 属性
    window.chrome.loadTimes = function() {
        return {
            commitLoadTime: performance.timing.domContentLoadedEventStart / 1000,
            connectionInfo: "h2",
            finishDocumentLoadTime: performance.timing.domContentLoadedEventEnd / 1000,
            finishLoadTime: performance.timing.loadEventEnd / 1000,
            firstPaintAfterLoadTime: 0,
            firstPaintTime: performance.timing.domContentLoadedEventStart / 1000,
            navigationType: "Other",
            npnNegotiatedProtocol: "h2",
            requestTime: performance.timing.requestStart / 1000,
            startLoadTime: performance.timing.navigationStart / 1000,
            wasAlternateProtocolAvailable: false,
            wasFetchedViaSpdy: true,
            wasNpnNegotiated: true
        };
    };
    
    // 覆盖 permissions.query 以绕过权限检测
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    
    // 模拟真实的插件列表
    const plugins = [
        {
            name: "Chrome PDF Plugin",
            filename: "internal-pdf-viewer",
            description: "Portable Document Format",
            version: "undefined",
            length: 1,
            item: function() { return this; }
        },
        {
            name: "Chrome PDF Viewer",
            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
            description: "Portable Document Format",
            version: "undefined",
            length: 1,
            item: function() { return this; }
        },
        {
            name: "Native Client",
            filename: "internal-nacl-plugin",
            description: "Native Client module",
            version: "undefined",
            length: 2,
            item: function() { return this; }
        }
    ];
    
    // 覆盖 navigator.plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const pluginArray = plugins;
            pluginArray.length = plugins.length;
            pluginArray.item = (index) => plugins[index] || null;
            pluginArray.namedItem = (name) => plugins.find(p => p.name === name) || null;
            return pluginArray;
        },
        configurable: true
    });
    
    // 覆盖 navigator.mimeTypes
    Object.defineProperty(navigator, 'mimeTypes', {
        get: () => {
            const mimeTypes = [
                { type: "application/pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: plugins[0] },
                { type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: plugins[1] },
                { type: "application/x-nacl", suffixes: "", description: "Native Client executable", enabledPlugin: plugins[2] },
                { type: "application/x-pnacl", suffixes: "", description: "Portable Native Client executable", enabledPlugin: plugins[2] }
            ];
            const mimeTypeArray = mimeTypes;
            mimeTypeArray.length = mimeTypes.length;
            mimeTypeArray.item = (index) => mimeTypes[index] || null;
            mimeTypeArray.namedItem = (name) => mimeTypes.find(m => m.type === name) || null;
            return mimeTypeArray;
        },
        configurable: true
    });
    
    // 覆盖 Notification.permission
    Object.defineProperty(Notification, 'permission', {
        get: () => "default",
        configurable: true
    });
    
    // 修复 Canvas 指纹 - 添加轻微噪声
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (this.width > 0 && this.height > 0) {
            const ctx = this.getContext('2d');
            if (ctx) {
                const imageData = ctx.getImageData(0, 0, this.width, this.height);
                const data = imageData.data;
                // 添加微小的随机噪声（几乎不可见但改变哈希值）
                for (let i = 0; i < data.length; i += 4) {
                    if (Math.random() < 0.001) {
                        data[i] = Math.max(0, Math.min(255, data[i] + (Math.random() > 0.5 ? 1 : -1)));
                    }
                }
                ctx.putImageData(imageData, 0, 0);
            }
        }
        return originalToDataURL.apply(this, arguments);
    };
    
    // 覆盖 getContext 以支持 WebGL
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(contextType) {
        if (contextType === 'webgl' || contextType === 'experimental-webgl' || contextType === 'webgl2') {
            const gl = originalGetContext.apply(this, arguments);
            if (gl) {
                // 覆盖 WebGL 参数以隐藏自动化特征
                const originalGetParameter = gl.getParameter;
                gl.getParameter = function(parameter) {
                    // 隐藏 UNMASKED_VENDOR_WEBGL 和 UNMASKED_RENDERER_WEBGL
                    if (parameter === 0x9245) { // UNMASKED_VENDOR_WEBGL
                        return "Intel Inc.";
                    }
                    if (parameter === 0x9246) { // UNMASKED_RENDERER_WEBGL
                        return "Intel Iris OpenGL Engine";
                    }
                    return originalGetParameter.apply(this, arguments);
                };
            }
            return gl;
        }
        return originalGetContext.apply(this, arguments);
    };
    
    // 覆盖 WebGL2RenderingContext
    if (window.WebGL2RenderingContext) {
        const originalWebGL2GetParameter = window.WebGL2RenderingContext.prototype.getParameter;
        window.WebGL2RenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 0x9245) {
                return "Intel Inc.";
            }
            if (parameter === 0x9246) {
                return "Intel Iris OpenGL Engine";
            }
            return originalWebGL2GetParameter.apply(this, arguments);
        };
    }
    
    // 覆盖 navigator.platform 以匹配 User-Agent
    window.__stealth_step = 100;
    window.__platform_before = navigator.platform;
    Object.defineProperty(Navigator.prototype, 'platform', {
        get: () => "Win32",
        configurable: true,
        enumerable: true
    });
    window.__platform_after = navigator.platform;
    window.__stealth_step = 101;

    // 覆盖 navigator.languages
    Object.defineProperty(Navigator.prototype, 'languages', {
        get: () => ["zh-CN", "zh", "en-US", "en"],
        configurable: true
    });
    
    // 覆盖 navigator.deviceMemory
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8,
        configurable: true
    });
    
    // 覆盖 navigator.hardwareConcurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
        configurable: true
    });
    
    // 覆盖 screen 属性
    Object.defineProperty(screen, 'colorDepth', {
        get: () => 24,
        configurable: true
    });
    
    Object.defineProperty(screen, 'pixelDepth', {
        get: () => 24,
        configurable: true
    });
    
    // 修复 iframe 的 contentWindow
    const originalCreateElement = document.createElement;
    document.createElement = function(tagName) {
        const element = originalCreateElement.apply(this, arguments);
        if (tagName.toLowerCase() === 'iframe') {
            try {
                const originalContentWindow = element.contentWindow;
                Object.defineProperty(element, 'contentWindow', {
                    get: () => {
                        const win = originalContentWindow;
                        if (win) {
                            win.navigator.webdriver = undefined;
                        }
                        return win;
                    },
                    configurable: true
                });
            } catch (e) {}
        }
        return element;
    };
    
    // 覆盖 console.debug 以防止某些检测
    const originalConsoleDebug = console.debug;
    console.debug = function() {
        // 过滤掉自动化相关的调试信息
        const args = Array.from(arguments);
        if (args.some(arg => typeof arg === 'string' && arg.includes('automation'))) {
            return;
        }
        return originalConsoleDebug.apply(this, arguments);
    };

    // 绕过 CDP Runtime 检测
    if (window.chrome && window.chrome.runtime) {
        // 确保 chrome.runtime.connect 存在
        if (!window.chrome.runtime.connect) {
            window.chrome.runtime.connect = function() {
                return {
                    onMessage: { addListener: function() {} },
                    postMessage: function() {},
                    disconnect: function() {}
                };
            };
        }
        // 确保 chrome.runtime.sendMessage 存在
        if (!window.chrome.runtime.sendMessage) {
            window.chrome.runtime.sendMessage = function() {};
        }
    }

    // 覆盖 Error.stack 以隐藏自动化痕迹
    const OriginalError = Error;
    Error = function(...args) {
        const err = new OriginalError(...args);
        const originalStack = err.stack;
        Object.defineProperty(err, 'stack', {
            get: function() {
                return originalStack ? originalStack.replace(/at .*automation.*/gi, '') : originalStack;
            },
            configurable: true
        });
        return err;
    };
    Error.prototype = OriginalError.prototype;

    // 修复 Function.toString 以隐藏代理
    const originalFunctionToString = Function.prototype.toString;
    Function.prototype.toString = function() {
        if (this === navigator.permissions.query) {
            return 'function query() { [native code] }';
        }
        if (this === HTMLCanvasElement.prototype.toDataURL) {
            return 'function toDataURL() { [native code] }';
        }
        if (this === HTMLCanvasElement.prototype.getContext) {
            return 'function getContext() { [native code] }';
        }
        return originalFunctionToString.apply(this, arguments);
    };
    
    // 添加假的 plugins 刷新
    Object.defineProperty(navigator, 'plugins', {
        get: function() {
            const plugins = [
                {name: "Chrome PDF Plugin", filename: "internal-pdf-viewer", description: "Portable Document Format", version: undefined, length: 1},
                {name: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", description: "Portable Document Format", version: undefined, length: 1},
                {name: "Native Client", filename: "internal-nacl-plugin", description: "Native Client module", version: undefined, length: 2}
            ];
            plugins.length = 3;
            plugins.refresh = function() {};
            plugins.item = function(index) { return this[index] || null; };
            plugins.namedItem = function(name) {
                for (let i = 0; i < this.length; i++) {
                    if (this[i].name === name) return this[i];
                }
                return null;
            };
            return plugins;
        },
        configurable: true
    });
})();
"""


class BrowserManager:
    """浏览器管理器 - 管理 Playwright 浏览器实例"""

    def __init__(self, config: BrowserConfig):
        self.config = config
        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.tab_manager = TabManager()
        self._profile: ProfileConfig | None = None
        self._user_data_dir: str | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        """浏览器是否运行中"""
        return self._running and self.browser is not None

    def _get_user_data_dir(self, profile: ProfileConfig) -> str:
        """获取用户数据目录"""
        if profile.user_data_dir:
            # 使用配置文件指定的目录
            user_data_dir = os.path.expanduser(profile.user_data_dir)
        else:
            # 使用默认目录，按配置文件分目录
            base_dir = get_default_user_data_dir()
            user_data_dir = os.path.join(base_dir, profile.name)

        # 确保目录存在
        os.makedirs(user_data_dir, exist_ok=True)
        return user_data_dir

    async def start(
        self, profile_name: str | None = None, user_data_dir: str | None = None
    ) -> bool:
        """启动浏览器

        Args:
            profile_name: 配置文件名称
            user_data_dir: 用户数据目录（可选，如果不提供则使用配置文件中的设置）
        """
        if self.is_running:
            return True

        profile = self.config.get_profile(profile_name)
        self._profile = profile

        # 获取用户数据目录
        if user_data_dir:
            # 使用传入的用户数据目录（用于多浏览器实例）
            self._user_data_dir = user_data_dir
        else:
            # 使用配置文件中的用户数据目录
            self._user_data_dir = self._get_user_data_dir(profile)

        # 启动 Playwright
        self.playwright = await async_playwright().start()

        # 浏览器启动参数
        browser_args = []

        # 检测是否为 root 用户，如果是则自动添加 no-sandbox 参数
        if os.getuid() == 0 or profile.no_sandbox:
            browser_args.extend(
                [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                ]
            )

        # 反检测参数 - 隐藏自动化特征，避免被识别为机器人
        browser_args.extend(
            [
                # 核心反检测参数
                "--disable-blink-features=AutomationControlled",
                "--exclude-switches=enable-automation",
                "--disable-automation",
                # 安全和隔离
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process,AutomationControlled",
                "--disable-site-isolation-trials",
                # 渲染和性能
                "--disable-software-rasterizer",
                "--disable-logging",
                "--log-level=3",
                # 调试端口
                "--remote-debugging-port=0",
                # 后台服务
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-breakpad",
                "--disable-client-side-phishing-detection",
                "--disable-component-update",
                "--disable-default-apps",
                "--disable-domain-reliability",
                "--disable-features=TranslateUI",
                "--disable-hang-monitor",
                "--disable-ipc-flooding-protection",
                "--disable-prompt-on-repost",
                "--disable-renderer-backgrounding",
                "--disable-sync",
                "--disable-translate",
                # 指标和遥测
                "--metrics-recording-only",
                "--no-report-upload",
                "--mute-audio",
                "--no-first-run",
                "--safebrowsing-disable-auto-update",
                # WebGL 支持
                "--enable-webgl",
                "--enable-features=WebGL,WebGL2",
                "--use-gl=swiftshader",
                # 自动化提示
                "--disable-infobars",
                "--disable-popup-blocking",
                "--disable-notifications",
                # 窗口大小和位置
                "--window-size=1920,1080",
                "--window-position=0,0",
                # 扩展
                "--disable-extensions-except=",
                "--disable-component-extensions-with-background-pages",
                # 用户代理相关
                "--force-device-scale-factor=1",
                "--device-scale-factor=1",
                # 内存和性能
                "--memory-model=low",
                "--max_old_space_size=4096",
                # 额外的反检测参数
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-zygote",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu-sandbox",
            ]
        )

        # 添加自定义参数
        browser_args.extend(profile.args)

        # 确定可执行路径
        executable_path = profile.executable_path or self.config.executable_path

        # 启动浏览器
        try:
            # 统一使用 Windows 平台的 User-Agent 和配置
            # 确保 User-Agent 和 Platform 一致
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

            # 额外的上下文选项 - 用于反检测
            context_options = {
                "user_data_dir": self._user_data_dir,
                "headless": profile.headless,
                "args": browser_args,
                "user_agent": user_agent,
                "viewport": {"width": 1920, "height": 1080},
                "screen": {"width": 1920, "height": 1080},
                "device_scale_factor": 1,
                "is_mobile": False,
                "has_touch": False,
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai",
                "geolocation": {"latitude": 39.9042, "longitude": 116.4074},  # 北京
                "permissions": ["geolocation", "notifications"],
                "color_scheme": "light",
                "reduced_motion": "no-preference",
                "forced_colors": "none",
                # 添加额外的反检测选项
                "ignore_default_args": ["--enable-automation", "--enable-blink-features=AutomationControlled"],
                "bypass_csp": True,  # 绕过内容安全策略
            }

            # 添加可执行路径（如果指定）
            if executable_path:
                context_options["executable_path"] = executable_path

            # 启动浏览器
            self.browser = await self.playwright.chromium.launch_persistent_context(
                **context_options
            )
            # launch_persistent_context 返回的是 context，不是 browser
            self.context = self.browser

            # 在 context 级别注入反检测脚本（对所有新页面生效）
            print(f"[DEBUG] Adding init script to context...")

            # 简化的反检测脚本 - 只包含关键修复
            SIMPLE_STEALTH = """
Object.defineProperty(Navigator.prototype, 'webdriver', {
    get: () => false,
    configurable: true,
    enumerable: true
});

Object.defineProperty(Navigator.prototype, 'platform', {
    get: () => 'Win32',
    configurable: true,
    enumerable: true
});

Object.defineProperty(Navigator.prototype, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en'],
    configurable: true
});
"""
            await self.context.add_init_script(SIMPLE_STEALTH)
            print(f"[DEBUG] Init script added successfully")

            self._running = True

            # 为所有页面添加反检测脚本（必须在处理现有页面之前注册）
            self.context.on("page", self._on_page_created)

            # 为现有页面注册（persistent context 可能已经有页面了）
            pages = self.context.pages
            if pages:
                # 不需要 reload，脚本会在下次导航时自动注入
                await self.tab_manager.create_tab(pages[0])
            else:
                page = await self.context.new_page()
                await self.tab_manager.create_tab(page)

            return True

        except Exception as e:
            await self.stop()
            raise RuntimeError(f"Failed to start browser: {e}")

    async def stop(self) -> bool:
        """停止浏览器"""
        if not self.is_running:
            return False

        # 关闭所有标签页
        await self.tab_manager.close_all()

        # 关闭上下文（对于 persistent context，这就是 browser）
        if self.context:
            try:
                await self.context.close()
            except:
                pass
            self.context = None

        self.browser = None

        # 停止 Playwright
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass
            self.playwright = None

        self._running = False
        self._profile = None
        # 注意：不清理 _user_data_dir，以保留 cookie 和 session

        return True

    async def reset(self) -> bool:
        """重置浏览器（关闭并重新启动）"""
        profile_name = self._profile.name if self._profile else None
        await self.stop()
        return await self.start(profile_name)

    async def _on_page_created(self, page):
        """当新页面创建时注入反检测脚本"""
        await self._inject_stealth_scripts(page)

    async def _inject_stealth_scripts(self, page):
        """注入反检测脚本到页面"""
        try:
            # 在页面加载前注入脚本
            await page.add_init_script(STEALTH_SCRIPTS)
            print(f"[DEBUG] Stealth script injected to page: {page.url}")
        except Exception as e:
            # 打印注入失败的错误
            print(f"[ERROR] Failed to inject stealth script: {e}")
            import traceback
            traceback.print_exc()

    def get_status(self) -> dict[str, Any]:
        """获取浏览器状态"""
        return {
            "running": self.is_running,
            "profile": self._profile.name if self._profile else None,
            "tabs": len(self.tab_manager.tabs),
            "activeTab": self.tab_manager.active_tab_id,
            "userDataDir": self._user_data_dir,
        }
