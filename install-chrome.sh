#!/bin/bash
# 智能安装 Chrome for Testing 脚本
# 自动检测平台、下载、解压并配置环境变量

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Chrome 版本
CHROME_VERSION="146.0.7680.66"

# 检测平台
detect_platform() {
    local os=$(uname -s)
    local arch=$(uname -m)
    
    case "$os" in
        Linux)
            case "$arch" in
                x86_64)
                    echo "linux64"
                    ;;
                aarch64)
                    echo "linux64"
                    ;;
                *)
                    echo "unsupported"
                    ;;
            esac
            ;;
        Darwin)
            case "$arch" in
                arm64)
                    echo "mac-arm64"
                    ;;
                x86_64)
                    echo "mac-x64"
                    ;;
                *)
                    echo "unsupported"
                    ;;
            esac
            ;;
        MINGW*|MSYS*|CYGWIN*)
            case "$arch" in
                x86_64)
                    echo "win64"
                    ;;
                i686|i386)
                    echo "win32"
                    ;;
                *)
                    echo "unsupported"
                    ;;
            esac
            ;;
        *)
            echo "unsupported"
            ;;
    esac
}

# 获取下载 URL
get_download_url() {
    local platform=$1
    echo "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/${platform}/chrome-${platform}.zip"
}

# 获取 Chrome 可执行文件路径
get_chrome_executable() {
    local platform=$1
    local install_dir=$2
    
    case "$platform" in
        linux64)
            echo "${install_dir}/chrome-linux64/chrome"
            ;;
        mac-arm64|mac-x64)
            echo "${install_dir}/chrome-${platform}/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
            ;;
        win32|win64)
            echo "${install_dir}/chrome-${platform}/chrome.exe"
            ;;
    esac
}

# 主函数
main() {
    echo -e "${YELLOW}🔍 检测平台...${NC}"
    PLATFORM=$(detect_platform)
    
    if [ "$PLATFORM" = "unsupported" ]; then
        echo -e "${RED}❌ 不支持的平台${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 检测到平台: $PLATFORM${NC}"
    
    # 设置安装目录
    INSTALL_DIR="${HOME}/.qianji/chrome"
    mkdir -p "$INSTALL_DIR"
    
    # 检查是否已安装
    CHROME_EXEC=$(get_chrome_executable "$PLATFORM" "$INSTALL_DIR")
    if [ -f "$CHROME_EXEC" ]; then
        echo -e "${GREEN}✓ Chrome 已安装在: $CHROME_EXEC${NC}"
        echo -e "${YELLOW}📝 配置环境变量...${NC}"
    else
        # 下载 Chrome
        DOWNLOAD_URL=$(get_download_url "$PLATFORM")
        ZIP_FILE="${INSTALL_DIR}/chrome-${PLATFORM}.zip"
        
        echo -e "${YELLOW}📥 下载 Chrome for Testing...${NC}"
        echo -e "${YELLOW}   版本: $CHROME_VERSION${NC}"
        echo -e "${YELLOW}   平台: $PLATFORM${NC}"
        echo -e "${YELLOW}   URL: $DOWNLOAD_URL${NC}"
        
        # 使用 curl 或 wget 下载
        if command -v curl &> /dev/null; then
            curl -L --progress-bar -o "$ZIP_FILE" "$DOWNLOAD_URL"
        elif command -v wget &> /dev/null; then
            wget --show-progress -O "$ZIP_FILE" "$DOWNLOAD_URL"
        else
            echo -e "${RED}❌ 需要 curl 或 wget${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✓ 下载完成${NC}"
        
        # 解压
        echo -e "${YELLOW}📦 解压中...${NC}"
        cd "$INSTALL_DIR"
        unzip -q -o "$ZIP_FILE"
        rm "$ZIP_FILE"
        echo -e "${GREEN}✓ 解压完成${NC}"
        
        # 设置权限（Linux/Mac）
        if [ "$PLATFORM" = "linux64" ] || [ "$PLATFORM" = "mac-arm64" ] || [ "$PLATFORM" = "mac-x64" ]; then
            chmod +x "$CHROME_EXEC"
        fi
        
        echo -e "${GREEN}✓ Chrome 安装完成: $CHROME_EXEC${NC}"
    fi
    
    # 配置环境变量
    echo -e "${YELLOW}📝 配置环境变量...${NC}"
    
    # 检测 shell
    SHELL_NAME=$(basename "$SHELL")
    case "$SHELL_NAME" in
        bash)
            RC_FILE="$HOME/.bashrc"
            ;;
        zsh)
            RC_FILE="$HOME/.zshrc"
            ;;
        fish)
            RC_FILE="$HOME/.config/fish/config.fish"
            ;;
        *)
            RC_FILE="$HOME/.bashrc"
            ;;
    esac
    
    # 添加环境变量
    ENV_LINE="export QIANJI_BROWSER_PATH=\"$CHROME_EXEC\""
    
    # 检查是否已存在
    if grep -q "QIANJI_BROWSER_PATH" "$RC_FILE" 2>/dev/null; then
        # 更新现有配置
        sed -i.bak "/QIANJI_BROWSER_PATH/d" "$RC_FILE" 2>/dev/null || true
        echo "$ENV_LINE" >> "$RC_FILE"
        echo -e "${GREEN}✓ 更新环境变量: $RC_FILE${NC}"
    else
        # 添加新配置
        echo "" >> "$RC_FILE"
        echo "# qianji Chrome 配置" >> "$RC_FILE"
        echo "$ENV_LINE" >> "$RC_FILE"
        echo -e "${GREEN}✓ 添加环境变量: $RC_FILE${NC}"
    fi
    
    # 立即生效
    export QIANJI_BROWSER_PATH="$CHROME_EXEC"
    
    echo ""
    echo -e "${GREEN}🎉 安装完成！${NC}"
    echo ""
    echo -e "${YELLOW}📋 使用说明:${NC}"
    echo -e "   1. 运行: ${GREEN}source $RC_FILE${NC} 使环境变量生效"
    echo -e "   2. 验证: ${GREEN}qianji status${NC}"
    echo -e "   3. 启动: ${GREEN}qianji start${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Chrome 路径:${NC} $CHROME_EXEC"
    echo -e "${YELLOW}🔧 环境变量已写入:${NC} $RC_FILE"
}

# 运行主函数
main "$@"
