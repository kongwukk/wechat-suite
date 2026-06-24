# WeChat Daily

微信聊天自动总结工具。

它可以从真实微信数据库里导出指定群聊，再用 DeepSeek 生成当天 Markdown 日报。也支持继续保留原来的 Notion 流程。

## 现在能做什么

- 直接读取真实微信数据，导出指定群聊
- 按天生成群聊总结 Markdown
- 也可以继续使用原来的每日总结 + 待办提取流程
- 支持 DeepSeek、OpenAI 兼容接口

## 适用环境

- Linux / Ubuntu
- Python 3.12+
- 已解密的微信数据库或可通过 `wechat-decrypt` 读取的微信数据
- DeepSeek API Key

## 快速开始

### 1. 安装依赖

```bash
cd wechat-daily
.venv/bin/pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`。

如果同目录下存在 `config.local.yaml`，`./run_group_daily.sh` 会优先使用它；
命令启动时也会打印当前实际使用的配置文件路径。

如果你只想用“群聊日报”功能，只需要改这几项：

```yaml
group_daily:
  chat_name: "Walk AI Coding"
  date: "2026-06-23"
```

说明：
- `chat_name` 是群名
- `date` 是要总结的日期，格式 `YYYY-MM-DD`
- 导出路径和输出目录会自动使用默认值

如果你想改默认输出目录或解密仓库，也可以在 `group_daily` 下继续配置。

## 一键运行

```bash
./run_group_daily.sh
```

如果你想显式指定配置文件：

```bash
./run_group_daily.sh /abs/path/to/config.yaml
```

它会自动：

1. 从真实微信数据导出指定群聊
2. 生成当天 Markdown
3. 输出到 `group_daily_exports/`

## 输出文件

- 导出的 JSON：`markdown_exports/<群名>-export.json`
- 生成的 Markdown：`group_daily_exports/<日期>-<群名>-summary.md`

## 保留的原有功能

原来的 `main.py` 仍然可用，用于每日总结、任务提取和 Notion 写入。

```bash
python main.py --test
python main.py --console
python main.py --output-dir out --chat "某个群"
```

## 项目结构

- `main.py`：原始每日总结主流程
- `summarize_export_chat.py`：把导出的群聊 JSON 生成 Markdown
- `run_group_daily_pipeline.py`：一键导出 + 一键总结
- `run_group_daily.sh`：最短入口脚本
- `wechat_core/`：直接读微信数据库的核心模块
- `prompts/`：AI prompt 模板

## 注意事项

- `config.yaml` 里包含 API Key，不要提交自己的真实 key 到公开仓库
- `markdown_exports/` 和 `group_daily_exports/` 属于运行产物，可以随时删除
- 如果导出失败，先检查微信数据目录、`wechat-decrypt` 配置和 `DeepSeek` API Key

## 许可证

保留原项目许可证或按你的仓库设置为准。
