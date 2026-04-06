# App Package

`app/` 是 Python 子工程根目录。

- `pyproject.toml` 和 `uv.lock` 都放在这里
- `finance_pipeline/` 是可安装包
- `tests/` 是 Python 侧单测

从仓库根目录运行时，统一使用：

```bash
uv --directory app sync --group dev
uv --directory app run pytest
```
