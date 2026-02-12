# FPGABuilder Makefile
# 用于开发构建和测试

.PHONY: help install dev test lint format type-check clean build package all

help:  ## 显示此帮助信息
	@echo "FPGABuilder 开发命令"
	@echo ""
	@echo "使用方法:"
	@echo "  make [目标]"
	@echo ""
	@echo "目标:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install:  ## 安装FPGABuilder（开发模式）
	pip install -e .

install-dev:  ## 安装开发依赖
	pip install -e ".[dev]"

dev:  ## 运行FPGABuilder（开发模式）
	python run.py dev

run: dev  ## 运行FPGABuilder（开发模式，run的别名）

test:  ## 运行测试
	python run.py test

test-cov:  ## 运行测试并生成覆盖率报告
	pytest tests/ --cov=src --cov-report=html --cov-report=term

lint:  ## 运行代码检查
	python run.py lint

format:  ## 格式化代码
	python run.py format

type-check:  ## 运行类型检查
	python run.py type-check

check: lint type-check test  ## 运行所有检查（代码检查、类型检查、测试）

clean:  ## 清理构建文件和缓存
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build:  ## 构建分发包
	python -m build

package: build  ## 构建分发包（build的别名）

package-exe:  ## 使用PyInstaller构建可执行文件
	python scripts/package.py --exe --output dist

package-sdist:  ## 构建源代码分发包
	python scripts/package.py --sdist --output dist

package-wheel:  ## 构建wheel包
	python scripts/package.py --wheel --output dist

package-installer:  ## 构建Windows安装程序
	python scripts/package.py --installer --output dist

package-all:  ## 打包所有格式
	python scripts/package.py --all --output dist

dist-clean: clean  ## 彻底清理，包括分发包
	rm -rf dist/
	rm -rf *.egg-info/

all: check build  ## 运行所有检查并构建

# 快速命令
v: version
version:  ## 显示版本信息
	python run.py dev --version

i: install
t: test
l: lint
f: format
tc: type-check
c: clean
b: build