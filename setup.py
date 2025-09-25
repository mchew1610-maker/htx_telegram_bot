#!/usr/bin/env python3
"""
HTX Telegram Bot 交互式安装配置脚本
自动安装依赖并配置机器人
"""

import os
import sys
import subprocess
import time
import json
import platform
from pathlib import Path


# 颜色代码
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header():
    """打印头部信息"""
    print(Colors.HEADER + "=" * 60 + Colors.ENDC)
    print(Colors.HEADER + "       HTX Telegram Trading Bot Setup" + Colors.ENDC)
    print(Colors.HEADER + "            自动安装配置向导 v1.0" + Colors.ENDC)
    print(Colors.HEADER + "=" * 60 + Colors.ENDC)
    print()


def print_success(message):
    """打印成功消息"""
    print(Colors.OKGREEN + "✅ " + message + Colors.ENDC)


def print_error(message):
    """打印错误消息"""
    print(Colors.FAIL + "❌ " + message + Colors.ENDC)


def print_warning(message):
    """打印警告消息"""
    print(Colors.WARNING + "⚠️  " + message + Colors.ENDC)


def print_info(message):
    """打印信息"""
    print(Colors.OKCYAN + "ℹ️  " + message + Colors.ENDC)


def check_python_version():
    """检查Python版本"""
    print(Colors.BOLD + "\n1. 检查Python版本" + Colors.ENDC)
    python_version = sys.version_info

    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print_error(f"Python版本过低: {python_version.major}.{python_version.minor}")
        print_error("需要Python 3.9或更高版本")
        sys.exit(1)
    else:
        print_success(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        return True


def check_and_install_pip():
    """检查并安装pip"""
    print(Colors.BOLD + "\n2. 检查pip" + Colors.ENDC)
    try:
        import pip
        print_success("pip已安装")
        return True
    except ImportError:
        print_warning("pip未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--default-pip"])
            print_success("pip安装成功")
            return True
        except:
            print_error("pip安装失败，请手动安装")
            return False


def create_virtual_env():
    """创建虚拟环境"""
    print(Colors.BOLD + "\n3. 虚拟环境设置" + Colors.ENDC)

    if os.path.exists("venv"):
        print_info("虚拟环境已存在")
        use_existing = input("是否使用现有虚拟环境? (y/n): ").lower()
        if use_existing != 'y':
            print_info("删除旧虚拟环境...")
            subprocess.call(["rm", "-rf", "venv"])
        else:
            return True

    print_info("创建虚拟环境...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print_success("虚拟环境创建成功")
        return True
    except:
        print_error("虚拟环境创建失败")
        return False


def install_dependencies():
    """安装依赖包"""
    print(Colors.BOLD + "\n4. 安装依赖包" + Colors.ENDC)

    # 确定pip路径
    if os.path.exists("venv"):
        if platform.system() == "Windows":
            pip_path = os.path.join("venv", "Scripts", "pip")
        else:
            pip_path = os.path.join("venv", "bin", "pip")
    else:
        pip_path = "pip3"

    dependencies = [
        ("pyTelegramBotAPI", "4.17.0", "Telegram Bot API"),
        ("requests", "2.31.0", "HTTP请求库"),
        ("websocket-client", "1.7.0", "WebSocket客户端"),
        ("pandas", "2.2.0", "数据处理"),
        ("numpy", "1.26.4", "数值计算"),
        ("matplotlib", "3.8.2", "图表生成"),
        ("plotly", "5.18.0", "交互式图表"),
        ("kaleido", "0.2.1", "图表导出"),
        ("python-dotenv", "1.0.1", "环境变量管理"),
        ("aiohttp", "3.9.3", "异步HTTP"),
        ("apscheduler", "3.10.4", "定时任务"),
        ("loguru", "0.7.2", "日志管理"),
        ("redis", "5.0.1", "Redis客户端"),
        ("cryptography", "42.0.2", "加密库")
    ]

    print_info(f"需要安装 {len(dependencies)} 个依赖包\n")

    failed = []
    for i, (package, version, description) in enumerate(dependencies, 1):
        print(f"[{i}/{len(dependencies)}] 安装 {package}=={version} ({description})...", end="")
        try:
            subprocess.check_call(
                [pip_path, "install", f"{package}=={version}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(Colors.OKGREEN + " ✓" + Colors.ENDC)
        except:
            print(Colors.FAIL + " ✗" + Colors.ENDC)
            failed.append(package)

    if failed:
        print_warning(f"以下包安装失败: {', '.join(failed)}")
        print_info("尝试使用requirements.txt批量安装...")
        try:
            subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
            print_success("依赖安装完成")
            return True
        except:
            print_error("依赖安装失败")
            return False
    else:
        print_success("所有依赖安装成功")
        return True


def configure_api_keys():
    """配置API密钥"""
    print(Colors.BOLD + "\n5. 配置API密钥" + Colors.ENDC)

    # 检查是否已有配置
    if os.path.exists(".env"):
        print_info(".env文件已存在")
        overwrite = input("是否覆盖现有配置? (y/n): ").lower()
        if overwrite != 'y':
            return True

    print_info("请准备好以下信息：")
    print("  1. Telegram Bot Token (从 @BotFather 获取)")
    print("  2. HTX (火币) API Key")
    print("  3. HTX (火币) Secret Key")
    print("  4. 授权使用的Telegram用户ID (可选)")
    print()

    # 获取Telegram配置
    print(Colors.BOLD + "Telegram配置:" + Colors.ENDC)
    bot_token = input("请输入Bot Token: ").strip()
    while not bot_token:
        print_error("Bot Token不能为空")
        bot_token = input("请输入Bot Token: ").strip()

    # 获取用户ID
    allowed_users = []
    print_info("设置授权用户（留空则允许所有用户）")
    print_info("获取用户ID方法: 在Telegram中使用 @userinfobot")

    while True:
        user_id = input("输入Telegram用户ID (输入done完成): ").strip()
        if user_id.lower() == 'done' or user_id == '':
            break
        if user_id.isdigit():
            if user_id not in allowed_users:  # 避免重复添加
                allowed_users.append(user_id)
                print_success(f"已添加用户ID: {user_id}")
            else:
                print_info(f"用户ID {user_id} 已存在")
        elif user_id:
            print_error("用户ID必须是数字")

    # 获取HTX配置
    print(Colors.BOLD + "\nHTX (火币) API配置:" + Colors.ENDC)
    htx_key = input("请输入API Key: ").strip()
    while not htx_key:
        print_error("API Key不能为空")
        htx_key = input("请输入API Key: ").strip()

    htx_secret = input("请输入Secret Key: ").strip()
    while not htx_secret:
        print_error("Secret Key不能为空")
        htx_secret = input("请输入Secret Key: ").strip()

    # 高级设置
    print(Colors.BOLD + "\n高级设置（按Enter使用默认值）:" + Colors.ENDC)

    monitor_interval = input("监控间隔(秒) [默认60]: ").strip() or "60"
    grid_count = input("默认网格数量 [默认10]: ").strip() or "10"
    grid_amount = input("默认每格数量 [默认0.001]: ").strip() or "0.001"
    timezone = input("时区 [默认Asia/Shanghai]: ").strip() or "Asia/Shanghai"

    # 生成配置文件
    config_content = f"""# Telegram Bot配置
TELEGRAM_BOT_TOKEN={bot_token}
TELEGRAM_CHAT_ID=

# 允许使用的用户ID
ALLOWED_USER_IDS={','.join(allowed_users)}

# HTX (火币) API配置
HTX_ACCESS_KEY={htx_key}
HTX_SECRET_KEY={htx_secret}

# API基础URL
HTX_REST_URL=https://api.huobi.pro
HTX_WS_URL=wss://api.huobi.pro/ws/v2

# 数据库配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# 网格交易默认配置
GRID_DEFAULT_COUNT={grid_count}
GRID_DEFAULT_AMOUNT={grid_amount}

# 监控配置
MONITOR_INTERVAL={monitor_interval}
PRICE_ALERT_THRESHOLD=0.05

# 时区配置
TIMEZONE={timezone}
"""

    # 保存配置
    with open(".env", "w") as f:
        f.write(config_content)

    print_success("配置文件已保存到 .env")

    # 保存用户信息（可选）
    if allowed_users:
        user_info = {
            "allowed_users": allowed_users,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open("data/authorized_users.json", "w") as f:
            json.dump(user_info, f, indent=2)
        print_success(f"已设置 {len(allowed_users)} 个授权用户")

    return True


def create_directories():
    """创建必要的目录"""
    print(Colors.BOLD + "\n6. 创建必要目录" + Colors.ENDC)

    directories = [
        "data",
        "data/charts",
        "data/grids",
        "data/alerts",
        "data/users",
        "logs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print_success(f"创建目录: {directory}")

    return True


def test_configuration():
    """测试配置"""
    print(Colors.BOLD + "\n7. 测试配置" + Colors.ENDC)

    test_modules = input("是否测试API连接? (y/n): ").lower()
    if test_modules != 'y':
        print_info("跳过测试")
        return True

    print_info("运行测试脚本...")

    # 确定Python路径
    if os.path.exists("venv"):
        if platform.system() == "Windows":
            python_path = os.path.join("venv", "Scripts", "python")
        else:
            python_path = os.path.join("venv", "bin", "python")
    else:
        python_path = sys.executable

    try:
        result = subprocess.run(
            [python_path, "test_bot.py"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print_success("测试通过")
            print(result.stdout)
            return True
        else:
            print_error("测试失败")
            print(result.stderr)
            return False
    except Exception as e:
        print_error(f"测试运行失败: {e}")
        return False


def create_startup_script():
    """创建启动脚本"""
    print(Colors.BOLD + "\n8. 创建启动脚本" + Colors.ENDC)

    if platform.system() == "Windows":
        # Windows批处理脚本
        script_content = """@echo off
echo Starting HTX Telegram Bot...
if exist venv\\Scripts\\activate.bat (
    call venv\\Scripts\\activate.bat
)
python bot.py
pause
"""
        script_name = "start_bot.bat"
    else:
        # Linux/Mac Shell脚本
        script_content = """#!/bin/bash
echo "Starting HTX Telegram Bot..."
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi
python bot.py
"""
        script_name = "start_bot.sh"

    with open(script_name, "w") as f:
        f.write(script_content)

    if platform.system() != "Windows":
        os.chmod(script_name, 0o755)

    print_success(f"启动脚本已创建: {script_name}")
    return True


def main():
    """主函数"""
    print_header()

    steps = [
        ("检查Python版本", check_python_version),
        ("检查pip", check_and_install_pip),
        ("创建虚拟环境", create_virtual_env),
        ("安装依赖", install_dependencies),
        ("配置API密钥", configure_api_keys),
        ("创建目录", create_directories),
        ("测试配置", test_configuration),
        ("创建启动脚本", create_startup_script)
    ]

    total_steps = len(steps)
    completed = 0

    for i, (step_name, step_func) in enumerate(steps, 1):
        print(f"\n{Colors.BOLD}步骤 {i}/{total_steps}: {step_name}{Colors.ENDC}")
        print("-" * 40)

        if step_func():
            completed += 1
        else:
            print_error(f"{step_name} 失败")
            retry = input("是否重试? (y/n): ").lower()
            if retry == 'y':
                if step_func():
                    completed += 1
                else:
                    print_error("重试失败，跳过此步骤")

    # 完成
    print("\n" + "=" * 60)
    if completed == total_steps:
        print_success("🎉 安装配置完成！")
        print()
        print(Colors.BOLD + "启动机器人:" + Colors.ENDC)
        if platform.system() == "Windows":
            print("  运行: start_bot.bat")
        else:
            print("  运行: ./start_bot.sh")
        print("  或者: python bot.py")
        print()
        print(Colors.BOLD + "使用说明:" + Colors.ENDC)
        print("  1. 在Telegram中搜索你的机器人")
        print("  2. 发送 /start 开始使用")
        print("  3. 使用底部按钮菜单操作")

        if os.path.exists("data/authorized_users.json"):
            with open("data/authorized_users.json") as f:
                users = json.load(f)
                if users.get("allowed_users"):
                    print()
                    print(Colors.BOLD + "授权用户:" + Colors.ENDC)
                    for user_id in users["allowed_users"]:
                        print(f"  - {user_id}")
    else:
        print_warning(f"安装部分完成 ({completed}/{total_steps})")
        print_info("请检查失败的步骤并手动修复")

    print("\n" + "=" * 60)
    print(Colors.OKCYAN + "感谢使用HTX Telegram Trading Bot！" + Colors.ENDC)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + Colors.WARNING + "安装被用户中断" + Colors.ENDC)
        sys.exit(1)
    except Exception as e:
        print("\n" + Colors.FAIL + f"安装出错: {e}" + Colors.ENDC)
        sys.exit(1)