# WeChat Suite

WeChat Suite 是一个面向本地微信聊天记录的整理工具包。它把两个能力组合到一个仓库里：先从真实微信数据库导出聊天记录，再用大模型按天生成 Markdown 群聊日报。

## 功能特性

- 从本地微信数据库导出指定群聊记录
- 按日期生成群聊日报 Markdown
- 支持 DeepSeek、NewAPI 以及 OpenAI 兼容接口
- 保留 `wechat-daily` 原有的控制台输出、Markdown 输出和 Notion 流程
- 将导出文件、日志、密钥和本地配置默认排除在 Git 之外

## 项目结构

```text
wechat-suite/
├── run.sh                    # 根目录一键运行入口
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
生成 Markdown 群聊日报
```

## 环境要求

- Linux / Ubuntu
- Python 3.12+
- 已登录且有本地数据的微信客户端
- 可用的 DeepSeek、NewAPI 或其他 OpenAI 兼容模型 API Key
- 已完成 `wechat-decrypt` 所需的微信数据库密钥提取

## 安装依赖

分别进入两个子目录安装依赖。

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

然后填写你的微信数据目录、密钥文件路径等信息。也可以按 `wechat-decrypt` 原项目 README 的方式生成 `all_keys.json`。

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
```

说明：

- `group_daily.chat_name`：要总结的群聊名称
- `group_daily.date`：要总结的日期，格式为 `YYYY-MM-DD`
- `ai.api_key`：你的模型 API Key
- `group_daily.decrypt_repo`：默认是 `../wechat-decrypt`，通常不用改

## 一键运行

在仓库根目录运行：

```bash
./run.sh
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
```

示例文件名：

```text
wechat-daily/markdown_exports/Walk_AI_Coding-export.json
wechat-daily/group_daily_exports/2026-06-23-Walk_AI_Coding-summary.md
```

## 常用命令

只改日期运行：

```bash
cd wechat-daily
./run_group_daily.sh config.local.yaml
```

使用原 `wechat-daily` 控制台输出：

```bash
cd wechat-daily
.venv/bin/python main.py --console --chat "群名" --date 2026-06-23
```

只生成 Markdown，不写 Notion：

```bash
cd wechat-daily
.venv/bin/python main.py --output-dir group_daily_exports --chat "群名" --date 2026-06-23
```

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
