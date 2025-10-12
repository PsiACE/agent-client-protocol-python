# Releasing

This project tracks the ACP schema tags published by
[`agentclientprotocol/agent-client-protocol`](https://github.com/agentclientprotocol/agent-client-protocol).
Every release should line up with one of those tags so that the generated `acp.schema` module, examples, and package
version remain consistent.

## 准备阶段

1. 选择目标 schema 版本（例如 `v0.4.5`），并重新生成协议文件：

   ```bash
   ACP_SCHEMA_VERSION=v0.4.5 make gen-all
   ```

   该命令会下载对应的 schema 包并重写 `schema/` 与 `src/acp/schema.py`。

2. 同步更新 `pyproject.toml` 中的版本号，并根据需要调整 `uv.lock`。

3. 运行基础校验：

   ```bash
   make check
   make test
   ```

   `make check` 会执行 Ruff 格式化/静态检查、类型分析以及依赖完整性校验；`make test` 则运行 pytest（含 doctest）。

4. 更新文档与示例（例如 Gemini 集成）以反映变化。

## 提交与合并

1. 确认 diff 仅包含预期变动：schema 源文件、生成的 Pydantic 模型、版本号以及相应文档。
2. 使用 Conventional Commits（如 `release: v0.4.5`）提交，并在 PR 中记录：
   - 引用的 ACP schema 标签
   - `make check` / `make test` 的结果
   - 重要的行为或 API 变更
3. 获得评审通过后合并 PR。

## 通过 GitHub Release 触发发布

仓库采用 GitHub Workflow (`on-release-main.yml`) 自动完成发布。主干合并完成后：

1. 在 GitHub Releases 页面创建新的 Release，选择目标标签（形如 `v0.4.5`）。如标签不存在，Release 创建过程会自动打上该标签。
2. Release 发布后，工作流会：
   - 将标签写回 `pyproject.toml`（以保证包版本与标签一致）
   - 构建并通过 `uv publish` 发布到 PyPI（使用 `PYPI_TOKEN` 机密）
   - 使用 `mkdocs gh-deploy` 更新 GitHub Pages 文档

无需在本地执行 `uv build` 或 `uv publish`；只需确保 Release 草稿信息完整（新增特性、兼容性注意事项等）。

## 其他注意事项

- Schema 有破坏性修改时，请同步更新 `tests/test_json_golden.py`、端到端用例（如 `tests/test_rpc.py`）以及相关示例。
- 如果需要清理生成文件，可运行 `make clean`，之后重新执行 `make gen-all`。
- 发布前务必确认 `ACP_ENABLE_GEMINI_TESTS` 等可选测试在必要环境下运行通过，以避免 Release 后出现回归。
