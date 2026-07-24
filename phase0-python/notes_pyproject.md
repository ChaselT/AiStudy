[project]
name = "phase0-python"  项目名称
version = "0.1.0" 项目版本号，相当于version
description = "Add your description here" 项目描述
readme = "README.md" readme 文档是哪个
requires-python = ">=3.11" 要求的最低py版本
dependencies = [ 项目依赖
    "pydantic>=2.13.4", pydantic 依赖，版本最低需要2.13.4
]

[dependency-groups] 开发分组依赖，不进入正式版本
dev = [
    "mypy>=2.3.0", mypy需要大于2.3.0
    "pytest>=9.1.1", pytest需要大于9.1.1
]

直接执行 uv add 的时候dependencies内增加依赖
执行 uv add --dev的时候增加的是dev的依赖