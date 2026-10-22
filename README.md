# Personal Skills

> 个人可复用 Codex Skills：把项目开发、Git 历史、设计文档和 Agent 工作沉淀为有证据的职业资产，并基于这些证据生成可追溯的简历版本。

![GitHub](https://img.shields.io/badge/GitHub-ShallowRecall%2Fpersonal--skills-181717?logo=github)
![Skills](https://img.shields.io/badge/format-agent%20skills-4B5563)
![License](https://img.shields.io/badge/license-MIT-green)

## 为什么单独建仓

这个仓库只放**个人职业资产和个人工作流**，不与团队 Cerberus 编码规范仓库混用：

- `cerberus-skills`：团队 Java 规范、代码评审、项目脚手架约定。
- `personal-skills`：职业证据采集、项目亮点沉淀、简历定制、面试故事。
- `C:\Users\zhuoz\.agents\skills`：Codex 的用户级 Skill 发现目录，通过 Junction 指向本仓库。

这样做的好处：

1. 团队仓库保持单一职责。
2. 个人职业工作流可以独立演进。
3. 多台机器可以只同步本仓库。
4. 不会因为 `--skill "*"` 把个人简历工具误装给团队成员。

## 包含的 Skills

| Skill | 解决的问题 | 主要输出 |
|---|---|---|
| [`career-evidence-miner`](skills/career-evidence-miner/SKILL.md) | 从本地仓库、Git 提交、设计文档和 Agent 工作里挖掘可验证的项目亮点 | Obsidian 项目案例、证据台账、STAR 故事、简历 bullet |
| [`resume-tailor`](skills/resume-tailor/SKILL.md) | 根据目标 JD，从职业资产库中挑选最匹配的项目并生成简历版本 | 一页简历、证据映射、JD 差距清单 |

### career-evidence-miner

适用场景：

- 完成一个项目或一段 Agent 开发后，整理成职业资产。
- 从 Git 历史、README、设计文档、源码中提取架构决策。
- 更新 Obsidian 里的项目案例和证据台账。
- 为面试准备 STAR 故事。

不适用：

- 没有本地证据的“帮我编一段简历”。
- 把团队成果直接写成本人独立成果。
- 没有数据来源却要求写“提升 30%”。

### resume-tailor

适用场景：

- 用户提供 JD，要求定制简历。
- 从已有项目中挑选主项目和辅项目。
- 生成个人摘要、核心技能、项目经历。
- 分析 JD 要求与现有证据的差距。

不适用：

- 虚构工作年限、团队规模、用户量、QPS、营收、转化率。
- 把课程项目包装成生产项目。
- 没有证据却声称“主导”“架构师”“负责人”。

## 仓库结构

```text
personal-skills/
├─ README.md
├─ LICENSE
├─ package.json
├─ skills/
│  ├─ career-evidence-miner/
│  │  ├─ SKILL.md
│  │  └─ agents/openai.yaml
│  └─ resume-tailor/
│     ├─ SKILL.md
│     └─ agents/openai.yaml
└─ scripts/
   └─ link-local.ps1
```

## 环境要求

- Node.js 18+
- npm / npx
- Codex、Claude Code 或其他支持 Agent Skills 的客户端
- Windows 用户级 Skills 目录：`C:\Users\<用户名>\.agents\skills`

检查环境：

```bash
node --version
npm --version
npx --yes skills --version
```

## 安装

> [!IMPORTANT]
> npm 本身没有 `npm add skill Xxx` 这个子命令。npm 生态里的标准安装器是 `skills` CLI，正确写法是：
>
> ```bash
> npx skills add ShallowRecall/personal-skills --skill <skill-name> -a codex -g -y
> ```
>
> 下面的命令就是“npm 安装 Skill”的实际可用形式。

### 查看仓库里的 Skills

```bash
npx skills add ShallowRecall/personal-skills --list
```

### 安装全部 Skills

```bash
npx skills add ShallowRecall/personal-skills --skill "*" -a codex -g -y
```

### 只安装一个 Skill

安装 `career-evidence-miner`：

```bash
npx skills add ShallowRecall/personal-skills --skill career-evidence-miner -a codex -g -y
```

安装 `resume-tailor`：

```bash
npx skills add ShallowRecall/personal-skills --skill resume-tailor -a codex -g -y
```

### 安装到其他 Agent

`-a` 指定目标 Agent。不同版本的 `skills` CLI 支持的值可能不同，先查看帮助：

```bash
npx skills add --help
```

然后替换 `-a codex`，例如 `-a claude-code`：

```bash
npx skills add ShallowRecall/personal-skills --skill career-evidence-miner -a claude-code -g -y
```

### 使用仓库内 npm scripts

克隆仓库后也可以使用：

```bash
npm run list
npm run install:career-evidence-miner
npm run install:resume-tailor
npm run install:all
```

这些脚本本质上仍然调用 `npx skills add`。

## 本地开发与 Junction

Windows 下推荐用 Junction 把当前仓库链接到用户级 Skills 目录，这样编辑仓库会立即生效，不需要复制文件。

```powershell
pwsh -NoProfile -File .\scripts\link-local.ps1
```

脚本行为：

- 只创建缺失的 Junction。
- 如果目标已经存在且不是 Junction，会报错退出，不会删除任何文件。
- 支持 `-WhatIf` 预览。
- 不修改仓库外的其他 Skill。

手动链接示例：

```bat
mklink /J "%USERPROFILE%\.agents\skills\career-evidence-miner" "D:\devTools\personal-skills\skills\career-evidence-miner"
mklink /J "%USERPROFILE%\.agents\skills\resume-tailor" "D:\devTools\personal-skills\skills\resume-tailor"
```

Codex 支持 symlink/junction 形式的 Skill 目录。更新后如果未立即出现，重启 Codex。

## 配置职业资产库

两个 Skill 默认查找：

```text
C:\Users\zhuoz\Documents\Obsidian Vault\note\职业资产库
```

更推荐的跨机器配置方式是设置环境变量：

```powershell
[Environment]::SetEnvironmentVariable(
  'CAREER_VAULT',
  'C:\Users\zhuoz\Documents\Obsidian Vault\note\职业资产库',
  'User'
)
```

Skill 的解析顺序：

1. 用户在对话里显式提供的路径。
2. `CAREER_VAULT` 环境变量。
3. 本机默认路径。
4. 如果都不存在，向用户询问路径。

如果你 fork 这个仓库，修改 `SKILL.md` 里的默认路径或设置 `CAREER_VAULT` 即可。

## 使用示例

### 从项目沉淀职业资产

```text
使用 career-evidence-miner，扫描 D:\workSpace\cerberus-app-mall 和
D:\workSpace\cerberus-app-subscribe，把最近的支付和订阅设计沉淀到职业资产库，
更新项目证据台账，并生成 2 条简历 bullet 和 1 个 STAR 故事。
```

### 为 JD 定制简历

```text
使用 resume-tailor，根据下面的 JD 生成一版 Java 支付后端简历。
每个项目 bullet 都要标注证据来源；没有证据的要求单独列差距，不要编造。
[JD 内容]
```

### 只更新一个项目案例

```text
使用 career-evidence-miner，只更新职业资产库里的 ARES Studio 项目案例。
重点补充字节级兼容、单写路径、五道门禁和性能巡检，不要改其他笔记。
```

## 输出位置

`career-evidence-miner` 默认写入：

```text
职业资产库/
├─ 00-导航/
├─ 10-项目案例/
├─ 20-简历素材/
├─ 30-能力沉淀/
├─ 40-模板/
└─ 50-证据/
```

`resume-tailor` 默认新建：

```text
职业资产库/20-简历素材/投递版本/简历-公司名-岗位-YYYYMMDD.md
```

不会覆盖已有版本，除非用户明确要求。

## 证据与真实性原则

两个 Skill 都遵循同一套规则：

| 等级 | 证据 | 可写的措辞 |
|---|---|---|
| A | 源码、提交、测试、设计文档、可运行脚本 | “设计并实现”“主导”需有清晰贡献证据 |
| B | README、提交说明、项目结构 | “参与”“实现”“建设” |
| C | 从结构推断，未确认 | “待确认”，不直接写入简历 |
| D | 用户量、营收、QPS、效率提升、团队规模 | 必须有真实来源 |

不会做：

- 编造业务指标。
- 把团队成果全部写成本人独立完成。
- 把 Demo 写成生产系统。
- 把“参与”写成“负责”。
- 把普通提交数量写成业务价值。

## 更新与卸载

### 更新

```bash
npx skills update career-evidence-miner resume-tailor -g -y
```

如果本机使用的是本文档中的 Junction 开发模式，更新源文件后执行 `git pull` 或 `git push` 即可；`npx skills update` 主要适用于通过 `npx skills add` 安装的副本。

### 卸载

```bash
npx skills remove career-evidence-miner resume-tailor -a codex -g -y
```

如果使用 Junction，删除用户级链接即可，不要删除仓库源文件：

```powershell
Remove-Item -LiteralPath "$HOME\.agents\skills\career-evidence-miner" -Force
```

> 仅当确认目标是 Junction 时执行。更安全的做法是用 `Get-Item` 检查 `LinkType`。

## 常见问题

### `npx skills add` 提示仓库不存在

确认仓库是 Public，或在私有仓库场景下先完成 GitHub 登录：

```bash
git ls-remote https://github.com/ShallowRecall/personal-skills.git
```

### Skill 安装后没有出现

1. 重启 Codex。
2. 检查用户级目录：

```powershell
Get-ChildItem "$HOME\.agents\skills" | Select-Object Name,LinkType,Target
```

3. 检查 `SKILL.md` 的 frontmatter 是否有 `name` 和 `description`。

### Junction 目标已存在

`link-local.ps1` 不会覆盖真实目录。先确认该目录是否是旧副本，再手动备份和移除；不要直接递归删除不确定的路径。

### `npm add skill Xxx` 不生效

这是 npm 语法问题。npm 没有 `add skill` 子命令，请使用：

```bash
npx skills add ShallowRecall/personal-skills --skill <name> -a codex -g -y
```

## 版本

当前版本：`1.0.0`（2026-10-22）

## 贡献

这是个人职业资产仓库，默认不接受团队规范类 Skill。团队 Cerberus 规范请继续维护在 `ShallowRecall/cerberus-skills`。

## License

[MIT](LICENSE)
