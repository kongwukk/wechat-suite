# WeChat Daily

微信聊天自动总结工具。

它可以从真实微信数据库里导出指定群聊或联系人聊天，再用 DeepSeek、NewAPI 或其他 OpenAI 兼容模型生成当天 Markdown 日报或个人聊天摘要。也支持继续保留原来的 Notion 流程。

## 现在能做什么

- 直接读取真实微信数据，导出指定群聊
- 按天生成群聊总结 Markdown
- 按天生成个人聊天摘要，分析对方态度、建议、需求和关键信息
- 也可以继续使用原来的每日总结 + 待办提取流程
- 支持 DeepSeek、NewAPI、OpenAI 兼容接口

## 适用环境

- Windows 11 或 Linux / Ubuntu
- Python 3.12+
- 已解密的微信数据库或可通过 `wechat-decrypt` 读取的微信数据
- DeepSeek、NewAPI 或其他 OpenAI 兼容模型 API Key

## 快速开始

### 1. 安装依赖

Windows 11 推荐在仓库根目录运行：

```bat
setup_win11.bat
```

只安装本目录依赖也可以：

```bat
cd wechat-daily
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux / Ubuntu：

```bash
cd wechat-daily
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. 配置

建议复制模板到本地配置后编辑：

```bat
copy config.yaml.example config.local.yaml
```

```bash
cp config.yaml.example config.local.yaml
```

如果同目录下存在 `config.local.yaml`，`run_group_daily.bat` / `./run_group_daily.sh` 会优先使用它；
命令启动时也会打印当前实际使用的配置文件路径。

如果你只想用“群聊日报”功能，只需要改这几项：

```yaml
group_daily:
  chat_name: "Walk AI Coding"
  date: "2026-06-23"

personal_chat:
  chat_name: "张三"
  date: "2026-06-23"        # 单日摘要
  # start_date: "2026-06-01" # 时间段摘要，填了 start_date/end_date 会优先于 date
  # end_date: "2026-06-23"
```

说明：
- `chat_name` 是群名
- `personal_chat.chat_name` 是联系人显示名、备注名或 wxid
- `date` 是要总结的日期，格式 `YYYY-MM-DD`
- `personal_chat.start_date` / `personal_chat.end_date` 可以生成一段时间内的个人聊天摘要
- 导出路径和输出目录会自动使用默认值

使用 NewAPI 时，把 `ai` 改成类似这样：

```yaml
ai:
  provider: "newapi"
  api_key: "YOUR_NEWAPI_API_KEY"
  model: "gpt-4o-mini"
  base_url: "http://127.0.0.1:3000/v1"
```

如果你想改默认输出目录或解密仓库，也可以在 `group_daily` 下继续配置。

## 一键运行

Windows 11：

```bat
run_group_daily.bat
```

Linux / Ubuntu：

```bash
./run_group_daily.sh
```

生成个人聊天摘要：

```bat
run_group_daily.bat --mode personal
```

```bash
./run_group_daily.sh --mode personal
```

生成某段时间的个人聊天摘要：

```bash
./run_group_daily.sh config.local.yaml --mode personal --chat-name "张三" --start-date 2026-06-01 --end-date 2026-06-23
```

如果你想显式指定配置文件：

```bat
run_group_daily.bat C:\path\to\config.local.yaml
```

```bash
./run_group_daily.sh /abs/path/to/config.yaml
```

它会自动：

1. 从真实微信数据导出指定群聊或联系人聊天
2. 生成当天 Markdown
3. 群聊日报输出到 `group_daily_exports/`，个人摘要输出到 `personal_chat_exports/`

## 输出文件

- 导出的 JSON：`markdown_exports/<群名>-export.json`
- 生成的 Markdown：`group_daily_exports/<日期>-<群名>-summary.md`
- 个人摘要 Markdown：`personal_chat_exports/<日期>-<联系人>-personal-summary.md`
- 个人时间段摘要 Markdown：`personal_chat_exports/<开始日期>_to_<结束日期>-<联系人>-personal-summary.md`

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
- `run_group_daily_pipeline.py`：一键导出 + 一键总结，支持群聊和个人聊天模式
- `run_group_daily.bat` / `run_group_daily.sh`：Windows / Linux 入口脚本
- `wechat_core/`：直接读微信数据库的核心模块
- `prompts/`：AI prompt 模板

## 注意事项

- `config.yaml` 里包含 API Key，不要提交自己的真实 key 到公开仓库
- `markdown_exports/` 和 `group_daily_exports/` 属于运行产物，可以随时删除
- 如果导出失败，先检查微信数据目录、`wechat-decrypt` 配置和模型 API Key

## 许可证

保留原项目许可证或按你的仓库设置为准。
