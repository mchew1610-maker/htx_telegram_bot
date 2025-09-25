# HTX Telegram Bot Makefile

.PHONY: help install test run clean docker-build docker-up docker-down logs

help: ## 显示帮助信息
	@echo "HTX Telegram Bot - 可用命令:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	@echo "📦 安装Python依赖..."
	@pip install -r requirements.txt
	@echo "✅ 依赖安装完成"

setup: ## 初始化项目配置
	@echo "🔧 初始化项目..."
	@cp -n .env.example .env || true
	@mkdir -p data/charts data/grids data/alerts data/users logs
	@echo "✅ 项目初始化完成"
	@echo "📝 请编辑 .env 文件配置API密钥"

test: ## 运行测试
	@echo "🧪 运行测试..."
	@python test_bot.py

run: ## 运行机器人
	@echo "🚀 启动机器人..."
	@python bot.py

run-bg: ## 后台运行机器人
	@echo "🚀 后台启动机器人..."
	@nohup python bot.py > logs/console.log 2>&1 &
	@echo "✅ 机器人已在后台运行"
	@echo "📊 查看日志: tail -f logs/bot.log"

stop: ## 停止机器人
	@echo "🛑 停止机器人..."
	@pkill -f "python bot.py" || true
	@echo "✅ 机器人已停止"

logs: ## 查看日志
	@tail -f logs/bot.log

clean: ## 清理临时文件
	@echo "🧹 清理临时文件..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type f -name ".DS_Store" -delete
	@echo "✅ 清理完成"

docker-build: ## 构建Docker镜像
	@echo "🐳 构建Docker镜像..."
	@docker-compose build
	@echo "✅ 镜像构建完成"

docker-up: ## 启动Docker容器
	@echo "🐳 启动Docker容器..."
	@docker-compose up -d
	@echo "✅ 容器启动完成"
	@echo "📊 查看日志: docker-compose logs -f"

docker-down: ## 停止Docker容器
	@echo "🐳 停止Docker容器..."
	@docker-compose down
	@echo "✅ 容器已停止"

docker-logs: ## 查看Docker日志
	@docker-compose logs -f htx-bot

docker-shell: ## 进入Docker容器
	@docker-compose exec htx-bot /bin/bash

backup: ## 备份数据
	@echo "💾 备份数据..."
	@tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz data/ logs/
	@echo "✅ 备份完成"

update: ## 更新依赖
	@echo "📦 更新依赖..."
	@pip install --upgrade -r requirements.txt
	@echo "✅ 更新完成"

status: ## 检查运行状态
	@echo "📊 检查运行状态..."
	@ps aux | grep -v grep | grep "python bot.py" || echo "❌ 机器人未运行"
	@echo ""
	@echo "📁 数据文件:"
	@ls -lh data/ 2>/dev/null || echo "无数据文件"
	@echo ""
	@echo "📝 最新日志:"
	@tail -5 logs/bot.log 2>/dev/null || echo "无日志文件"
