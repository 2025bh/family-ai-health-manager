# 家医 · 家庭健康管家（FamilyCare AI V0.2 开发版）

当前可恢复稳定基线仍为：**家庭AI健康管家 V0.1版**（Git 标签：`v0.1.0`）。V0.2 第一轮在独立开发分支 `agent/v0.2-health-guard` 增量开发，不改变 V0.1 标签。

后续功能继续在主分支上增量更新；无论后面增加多少功能，`v0.1.0` 标签都保留当前稳定代码，不随主分支变化。

需要临时查看或恢复本版本时：

```powershell
# 仅查看 V0.1，不改动当前分支
git switch --detach v0.1.0

# 从 V0.1 建立一个可继续修改的恢复分支（推荐）
git switch -c restore-v0.1 v0.1.0
```

本版本仓库备份代码、配置模板和项目文档；包含个人健康信息的 SQLite 数据库、病历原图、上传文件和真实密钥继续只保存在本机，不进入 GitHub。恢复代码前如需同时回退个人数据，应另外备份 `backend/data/` 与 `data/uploads/`。

> **聊天产生数据，而不是为了数据聊天。**
>
> **让老人负责说，让 AI 负责记，让医生更容易看懂。**
>
> **AI 不是替家人治病，而是帮助一个家庭更好地记录、沟通、提醒和管理健康。**

## 这是什么

这是一个可以在 Windows 本机运行的家庭长期健康记录 Demo。老人只要自然说话，系统会保留原话、整理健康信息、形成长期时间线，并在看医生前通过一次一个问题的对话生成《就医摘要》。

它不是 AI 医生：不诊断疾病、不开药、不建议停药或调整剂量。出现可能紧急的描述时，系统会停止普通聊天并提示尽快联系家人或专业医疗机构。

## 能做什么

- 支持“我、爸爸、妈妈、爷爷”等家庭成员；当前本机优先测试用户为黄金周。
- 用文字模拟语音，走与未来小智设备相同的 Agent 和数据库链路。
- 保存老人原话和 AI 结构化结果，形成长期健康时间线。
- 对话后展示结构化提取结果，并允许当场修改刚才的健康日志。
- 记录睡眠、饮食、运动、情绪、症状、血压、血糖、体温和体重。
- 血糖缺少空腹/饭后信息时只追问一个问题，再保存测量。
- 完成看医生模式、就医摘要、A4 打印版和就医回来模式。
- 看医生前先区分原医生复诊或新医生初诊；复诊生成近期精简版，新医生生成详细版。
- 健康时间线支持搜索、分类、日期范围、异常筛选、按日折叠和分批显示。
- 检查资料提供中文标题、自动归类和本地原图预览；健康任务可标记完成或恢复。
- 把患者转述的医生意见明确标注来源，并根据复查时间建立任务。
- 联系人解析和电话二次确认；开发环境只模拟拨号。
- 家属通知必须二次确认；开发环境使用 Mock，不会真的发到手机或飞书。
- 本地保存检查资料；飞书只同步摘要和索引。
- 主动询问时间可配置，并支持 `skip_today` 和 `snooze_until`。
- 提供 Mock 与真实 LLM、飞书、小智、Android、OCR、视频 Provider 边界。
- 首页新增“今日健康守护”，保留今天记录、健康趋势、中药疗程、准备看医生四个主要入口。
- 现代医学健康守护默认开启，支持最近 7 天/30 天与上一周期的透明比较。
- 风险分为数据暂不足、继续观察、值得关注、建议及时处理/就医，并保留规则版本、证据、不确定性和升级动作。
- 医疗安全层区分当前/历史、否定、恢复、他人、假设、提问和转折；基础安全检测始终优先。
- 中医健康守护默认关闭，首次开启必须明确确认；当前只提供基础架构，不提供完整辨证或处方能力。
- 用户纠正健康日志时保留修改前版本，并重新计算 7 天和 30 天分析。

## 如何安装

需要：

- Windows 10/11
- Python 3.12 或更高
- Node.js 22 或更高
- Git

打开 PowerShell，进入项目目录：

```powershell
cd "F:\codex-me\智能管家\familycare-ai"
```

第一次运行时执行：

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\start-windows.ps1
```

脚本会自动创建 Python 隔离环境、安装前端依赖，并在后台启动两个服务。

## Windows 如何手动运行

如果一键脚本失败，打开两个 PowerShell 窗口。

第一个窗口启动后端：

```powershell
cd "F:\codex-me\智能管家\familycare-ai\backend"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

看到 `Application startup complete` 代表后端成功。

第二个窗口启动网页：

```powershell
cd "F:\codex-me\智能管家\familycare-ai\frontend"
npm install
npm run dev
```

看到 `Local: http://localhost:5173/` 代表网页成功。

## 如何打开网页

浏览器打开：

- 家庭首页：<http://127.0.0.1:5173>
- 后端接口文档：<http://127.0.0.1:8000/docs>
- 后端健康检查：<http://127.0.0.1:8000/api/health>

## 如何测试看医生模式

1. 首页默认进入当前主测试用户黄金周；需要演示其他成员时再切换。
2. 在“模拟老人说话”里输入：`最近十来天老是头晕。`
3. 系统保存原话，并告诉你是否找到以前的同类记录。
4. 点击“我要去看医生”，发送预填的：`我准备去医院看看。`
5. 先说明是原医生复诊还是新医生初诊，再依次回答近期问题。每次只会出现一个问题。
6. 完成后在核对页逐项检查或修改，确认后生成《就医摘要》，需要时打印 A4 版。
7. 返回首页输入：`我看完医生了。`
8. 下一句输入：`医生说继续观察血压，两周后复查。`
9. 系统会把来源标为“患者转述医生意见”，并生成复查任务。

其他完整 Demo：

- 输入 `今天血糖8.1。` → 系统追问空腹还是饭后 → 回答 `空腹测的。` → 保存 Measurement。
- 输入 `给儿子打电话。` → 系统要求确认 → 回答 `确定。` → 返回“模拟拨号成功”。
- 输入 `我突然呼吸困难，喘不上气。` → 系统停止普通聊天并显示紧急联系提示。

## 如何运行自动测试

```powershell
cd "F:\codex-me\智能管家\familycare-ai"
pwsh -ExecutionPolicy Bypass -File .\scripts\test-windows.ps1
```

成功信号：后端显示 `passed`，前端显示 `built in ...`。

## Docker 如何运行

项目已提供 `docker-compose.yml`。当前电脑尚未检测到 Docker；安装 Docker Desktop 后执行：

```powershell
cd "F:\codex-me\智能管家\familycare-ai"
Copy-Item .env.example .env
docker compose up --build
```

然后打开 <http://127.0.0.1:5173>。Docker 只是另一种启动方式，不影响 Windows 原生运行。

## 如何配置 AI

默认 `MockLLMProvider`，没有 Key 也能完成全部 Demo。要使用 OpenAI 兼容接口：

1. 把 `.env.example` 复制为 `.env`。
2. 修改下面四项：

```text
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=你的兼容接口地址
LLM_API_KEY=你的密钥
LLM_MODEL=模型名称
```

不要把 `.env` 发给别人或提交到 Git。业务写入始终通过 `CareTools`，不会把数据库修改权直接交给模型自由发挥。

## 如何配置飞书

飞书不是核心数据库。默认 `MockFeishuProvider` 会验证六张表的同步映射和条数，但不联网写入。

真实多维表格已按指定位置创建：[09 家医·家庭健康管家 V0.1](https://xas44uebnwx.feishu.cn/wiki/YjymwyvsMipaaTknR62cECuFn0b)。

目标六张表：家庭成员、健康日志、健康测量、就医记录、健康任务、检查资料索引。原始体检报告、医疗图片和处方不会上传，只同步摘要和索引。

真实同步启用前需要：

1. 在上述知识库节点下创建 Base。
2. 读取线上真实 `base_token`、表 ID、字段 ID。
3. 用一条纯演示记录测试写入并回读。
4. 在 `.env` 填写 `FEISHU_BASE_TOKEN` 等配置，再把 `FEISHU_PROVIDER` 改为 `feishu`。

如果缺少凭证，系统继续使用 Mock，不会中断其他功能。

## 如何接小智

当前已有 `XiaozhiVoiceGateway`。未来让 `xiaozhi-esp32-server` 把识别后的文本发送到：

```text
POST http://后端地址/api/voice/message
```

请求中的 `gateway` 设为 `xiaozhi`。小智只负责语音入口，不保存家庭健康主数据。正式部署前必须补充设备身份、鉴权、HTTPS 和网络安全审核。

## Android 端如何运行

1. 安装 Android Studio。
2. 选择“Open”，打开 `android-companion` 文件夹。
3. 等待 Gradle 同步。
4. 连接模拟器或真机，点击运行。

V0.1 默认 `mockMode = true`，即使点“确定”也不会真实拨号。真实拨号需要显式改为 `false`、授予电话权限，并保留手机端二次确认。

## 数据和隐私

- 初始化种子数据为虚构演示数据；当前这台电脑的本地数据库已经由用户主动录入个人健康资料，属于私人医疗数据。
- SQLite 默认保存在 `backend/data/familycare.db`。
- 原始文件默认保存在 `data/uploads` 或配置的 `UPLOAD_DIR`。
- `.env`、数据库、上传文件和缓存已加入 `.gitignore`。
- V0.1 不提供删除健康记录接口，避免误删。后续新增删除必须二次确认并保留审计记录。

## 项目结构

```text
familycare-ai/
├─ backend/              FastAPI、SQLAlchemy、Agent、Provider、测试
├─ frontend/             React + TypeScript 老人/家属网页
├─ android-companion/    Kotlin 设备执行器基础项目
├─ docs/                 架构、数据库、安全、飞书、小智说明
├─ scripts/              Windows 启动和验收脚本
├─ data/uploads/         私人医疗文件目录（内容不进 Git）
├─ .env.example
└─ docker-compose.yml
```

## 常见问题

### 网页打不开

先分别打开 <http://127.0.0.1:8000/api/health> 和 <http://127.0.0.1:5173>。前者打不开就检查后端窗口，后者打不开就检查前端窗口。

### PowerShell 不允许执行脚本

使用：

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\start-windows.ps1
```

### 端口被占用

后端改用 `--port 8001` 时，还要把前端环境变量 `VITE_API_BASE_URL` 改为 `http://127.0.0.1:8001`。

### 为什么 AI 不直接判断是什么病

这是安全边界。V0.1 的任务是整理、发现变化、帮助沟通和提醒，不代替专业医疗判断。

### 为什么 Docker 命令不能用

说明电脑还没安装或启动 Docker Desktop。先按“Windows 如何手动运行”操作，功能不受影响。

## 当前实现状态

真实可用：本地数据库、家庭成员、健康原话记录、结构化提取展示与纠错、测量追问、可筛选时间线、复诊/初诊报告分流、报告核对修改与就医标记、就医摘要、A4 打印、就医后记录、可完成的健康任务、安全拦截、检查资料分类与原图预览、中药疗程、主动询问逻辑。

当前 Mock：大模型生成、Android 真拨号、飞书真实写入、小智硬件、OCR、多模态文档分析、家庭视频和外部家属通知。它们都有可替换 Provider/Adapter，不会与核心业务绑死。
