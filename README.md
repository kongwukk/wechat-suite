# WeChat Suite

WeChat Suite 是一个面向本地微信聊天记录的整理工具包。它把两个能力组合到一个仓库里：先从真实微信数据库导出聊天记录，再用大模型按天生成 Markdown 群聊日报或个人聊天摘要。

## 功能特性

- 从本地微信数据库导出指定群聊或联系人聊天记录
- 按日期生成群聊日报 Markdown
- 按日期生成个人聊天摘要，分析对方态度、建议、需求与关键信息
- 支持 DeepSeek、NewAPI 以及 OpenAI 兼容接口
- 保留 `wechat-daily` 原有的控制台输出、Markdown 输出和 Notion 流程
- 将导出文件、日志、密钥和本地配置默认排除在 Git 之外

## 项目结构

```text
wechat-suite/
├── run.bat                   # Windows 11 一键运行入口
├── run.sh                    # Linux / Ubuntu 一键运行入口
├── setup_win11.bat           # Windows 11 首次依赖安装
├── wechat-daily/             # 聊天总结、Markdown 生成、Notion 写入
└── wechat-decrypt/           # 微信数据库解密、会话查询、聊天导出
```

## 工作流程

```text
wechat-decrypt 导出指定群聊 JSON
  ↓
wechat-daily 读取 JSON 并筛选指定日期
  ↓
调用 DeepSeek / NewAPI / OpenAI 兼容模型
  ↓
生成 Markdown 群聊日报或个人聊天摘要
```

## 环境要求

- Windows 11 或 Linux / Ubuntu
- Python 3.12+
- 已登录且有本地数据的微信客户端
- 可用的 DeepSeek、NewAPI 或其他 OpenAI 兼容模型 API Key
- 已完成 `wechat-decrypt` 所需的微信数据库密钥提取

## 安装依赖

### Windows 11

在仓库根目录双击或运行：

```bat
setup_win11.bat
```

脚本会分别为 `wechat-decrypt` 和 `wechat-daily` 创建 `.venv`，并安装各自的依赖。

### Linux / Ubuntu

分别进入两个子目录安装依赖：

```bash
cd wechat-decrypt
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

```bash
cd ../wechat-daily
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

如果 `wechat-decrypt` 的完整依赖在你的环境里安装失败，可以先安装导出所需的最小依赖，例如 `pycryptodome`、`zstandard`、`tqdm`、`mcp`。

## 配置说明

### 1. 配置 wechat-decrypt

复制或编辑：

```bash
cp wechat-decrypt/config.example.json wechat-decrypt/config.json
```

Windows CMD 可用：

```bat
copy wechat-decrypt\config.example.json wechat-decrypt\config.json
```

然后填写你的微信数据目录、密钥文件路径等信息。也可以按 `wechat-decrypt` 原项目 README 的方式生成 `all_keys.json`。

Windows 上如果密钥提取或读取微信进程失败，请用管理员权限打开终端后重试。

### 2. 配置 wechat-daily

公开模板是：

```text
wechat-daily/config.yaml.example
```

本地私有配置建议放在：

```text
wechat-daily/config.local.yaml
```

`config.local.yaml` 已经被 `.gitignore` 忽略，不会提交到仓库。

Windows CMD 可用：

```bat
copy wechat-daily\config.yaml.example wechat-daily\config.local.yaml
```

最常改的是这几项：

```yaml
ai:
  provider: "deepseek"
  api_key: "YOUR_DEEPSEEK_API_KEY"
  model: "deepseek-chat"

# 使用 NewAPI 时：
# ai:
#   provider: "newapi"
#   api_key: "YOUR_NEWAPI_API_KEY"
#   model: "gpt-4o-mini"
#   base_url: "http://127.0.0.1:3000/v1"

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

- `group_daily.chat_name`：要总结的群聊名称
- `personal_chat.chat_name`：要总结的联系人显示名、备注名或 wxid
- `group_daily.date`：要总结的日期，格式为 `YYYY-MM-DD`
- `personal_chat.date`：个人聊天单日摘要日期
- `personal_chat.start_date` / `personal_chat.end_date`：个人聊天时间段摘要，格式为 `YYYY-MM-DD` 或 `today`
- `ai.api_key`：你的模型 API Key
- `group_daily.decrypt_repo`：默认是 `../wechat-decrypt`，通常不用改

## 一键运行

Windows 11 在仓库根目录运行：

```bat
run.bat
```

Linux / Ubuntu 在仓库根目录运行：

```bash
./run.sh
```

生成个人聊天摘要：

```bat
run.bat --mode personal
```

```bash
./run.sh --mode personal
```

脚本会自动优先读取：

```text
wechat-daily/config.local.yaml
```

如果没有本地配置，则回退到：

```text
wechat-daily/config.yaml
```

## 输出位置

运行后会生成两个目录：

```text
wechat-daily/markdown_exports/       # 中间 JSON 导出文件
wechat-daily/group_daily_exports/    # 最终 Markdown 日报
wechat-daily/personal_chat_exports/  # 最终个人聊天摘要
```

示例文件名：

```text
wechat-daily/markdown_exports/Walk_AI_Coding-export.json
wechat-daily/group_daily_exports/2026-06-23-Walk_AI_Coding-summary.md
wechat-daily/personal_chat_exports/2026-06-23-张三-personal-summary.md
wechat-daily/personal_chat_exports/2026-06-01_to_2026-06-23-张三-personal-summary.md
```

## 常用命令

只改日期运行：

```bat
cd wechat-daily
run_group_daily.bat config.local.yaml --date 2026-06-23
```

```bash
cd wechat-daily
./run_group_daily.sh config.local.yaml --date 2026-06-23
```

临时指定联系人生成个人摘要：

```bash
cd wechat-daily
./run_group_daily.sh config.local.yaml --mode personal --chat-name "张三" --date 2026-06-23
```

生成某段时间的个人摘要：

```bash
cd wechat-daily
./run_group_daily.sh config.local.yaml --mode personal --chat-name "张三" --start-date 2026-06-01 --end-date 2026-06-23
```

使用原 `wechat-daily` 控制台输出：

```bat
cd wechat-daily
.venv\Scripts\python.exe main.py --console --chat "群名" --date 2026-06-23
```

```bash
cd wechat-daily
.venv/bin/python main.py --console --chat "群名" --date 2026-06-23
```

只生成 Markdown，不写 Notion：

```bash
cd wechat-daily
.venv/bin/python main.py --output-dir group_daily_exports --chat "群名" --date 2026-06-23
```

Windows 计划任务可在 `wechat-daily` 目录右键管理员运行 `install_scheduler.bat`。

## 安全注意事项

- 不要提交真实的 `DeepSeek`、`NewAPI`、`OpenAI`、`Notion` API Key
- 不要提交 `all_keys.json`、`wxwork_keys.json`、微信数据库或导出的聊天记录
- `config.yaml`、`config.json`、`config.local.yaml`、导出目录和日志目录都已默认忽略
- 如果误把密钥提交过，请立即删除远端提交并轮换对应 API Key

## 已忽略的运行产物

- `wechat-daily/markdown_exports/`
- `wechat-daily/group_daily_exports/`
- `wechat-daily/logs/`
- `wechat-decrypt/decrypted/`
- `wechat-decrypt/wechat_files/`
- `all_keys.json`
- `config.yaml` / `config.json` / `config.local.yaml`

## 致谢

本仓库组合使用并保留了以下项目能力：

- `wechat-decrypt`：微信数据库解密与导出能力
- `wechat-daily`：聊天记录总结、任务提取与 Markdown / Notion 输出能力

请根据你使用到的上游项目许可证和要求保留相应署名。
