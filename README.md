# Career Skills

> 面向 AI Agent 的职业资产沉淀与简历定制 Skills。把项目开发、Git 历史、设计文档和 Agent 工作整理成可验证的职业资产，再基于这些证据生成简历版本。

[![Agent Skills](https://img.shields.io/badge/format-Agent%20Skills-4B5563)](https://agentskills.io)
[![Codex](https://img.shields.io/badge/agent-Codex-111827)](https://developers.openai.com/codex/skills)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 项目简介

这个仓库提供两套可复用的 Agent Skills：

- `career-evidence-miner`：从本地仓库、提交、设计文档和 Agent 工作产物中提取项目亮点，写入 Markdown / Obsidian 职业资产库。
- `resume-tailor`：读取职业资产库，根据目标 JD 生成可追溯的简历、证据映射和差距清单。

Skills 只包含工作流、约束和输出规范，不包含个人简历数据，也不会主动上传 Vault 或项目代码。

## 特性

- **证据驱动**：强结论必须能指向源码、提交、测试或设计文档。
- **拒绝编造**：不虚构用户量、QPS、营收、转化率、团队规模和效率提升。
- **Obsidian 友好**：输出 Markdown，支持 frontmatter、wikilink、表格和 callout。
- **路径可配置**：通过 `CAREER_VAULT` 或显式路径指定职业资产库。
- **多 Agent 安装**：基于 `skills` CLI，可安装到 Codex、Claude Code 等 Agent。
- **本地优先**：职业资产留在本地，Skill 不上传个人数据。
- **内置工具**：仓库扫描、职业笔记校验、JD 项目评分和 Skill 结构校验。
- **可测试**：包含单元测试与 GitHub Actions。

## Skills

### career-evidence-miner

从可验证的本地开发证据中构建职业资产库。

**适合：**

- 项目结束后整理项目复盘和技术亮点。
- 从 Git 提交、README、设计文档和源码中提取架构决策。
- 更新项目证据台账、能力地图和 STAR 故事。
- 为简历准备有来源的 bullet。
- 把 Agent 辅助开发过程沉淀成可复用经验。

**主要输出：**

- 项目案例 Markdown。
- 证据台账更新。
- 关键设计决策表。
- 简历 bullet。
- 面试追问清单。
- 待确认事实。

**不适用：**

- 没有任何本地证据的简历编写。
- 把团队成果全部写成个人独立成果。
- 没有数据来源却要求写业务收益。

### resume-tailor

根据目标岗位的 JD，从职业资产库生成定制简历。

**适合：**

- 拿到 JD 后判断项目匹配度。
- 从多个项目中选出 1 个主项目和 1-2 个辅项目。
- 生成中文或英文简历版本。
- 输出 bullet 的证据映射。
- 分析 JD 要求与现有经历的差距。

**主要输出：**

- 岗位定位摘要。
- 核心技能。
- 项目经历。
- 证据映射表。
- JD 差距清单。
- 新简历笔记路径。

**不适用：**

- 虚构工作年限、团队规模、管理范围。
- 把课程项目或 Demo 包装成生产系统。
- 没有证据却使用“主导”“负责人”“架构师”等措辞。

## 仓库结构

```text
personal-skills/
├─ README.md
├─ CHANGELOG.md
├─ LICENSE
├─ package.json
├─ .github/workflows/checks.yml
├─ scripts/
│  ├─ link-local.ps1
│  └─ validate_skills.py
├─ tests/
│  ├─ test_scan_repo.py
│  ├─ test_score_jd.py
│  ├─ test_skill_structure.py
│  └─ test_validate_notes.py
└─ skills/
   ├─ career-evidence-miner/
   │  ├─ SKILL.md
   │  ├─ agents/openai.yaml
   │  ├─ scripts/
   │  │  ├─ scan_repo.py
   │  │  └─ validate_career_notes.py
   │  ├─ references/
   │  │  ├─ evidence-schema.md
   │  │  └─ project-case-template.md
   │  └─ assets/obsidian-templates/project-case.md
   └─ resume-tailor/
      ├─ SKILL.md
      ├─ agents/openai.yaml
      ├─ scripts/score_jd.py
      ├─ references/
      │  ├─ resume-rubric.md
      │  └─ job-family-profiles.md
      └─ assets/resume-templates/
         ├─ resume-zh.md
         └─ resume-en.md
```

每个 Skill 都是独立目录，包含必需的 `SKILL.md`。`agents/openai.yaml` 用于配置展示名称、短描述和隐式调用策略。

## 内置工具

### 仓库扫描

```bash
python -X utf8 skills/career-evidence-miner/scripts/scan_repo.py --repo D:\workspace\project --json
```

输出仓库 HEAD、作者提交数、时间范围、近期提交、README 标题、设计文档、文件统计和测试文件，作为证据采集的起点。

### 职业笔记校验

```bash
python -X utf8 skills/career-evidence-miner/scripts/validate_career_notes.py --vault D:\career-vault
```

检查：

- 断开的 wikilink 和相对链接。
- 可能的 Token、密码和私钥。
- 项目笔记是否缺少 Evidence/Sources 章节。
- 简历 bullet 是否缺少证据标记。
- 数字型成果是否有来源。

准备投递版本时使用：

```bash
python -X utf8 skills/career-evidence-miner/scripts/validate_career_notes.py --vault D:\career-vault --strict
```

### JD 项目评分

```bash
python -X utf8 skills/resume-tailor/scripts/score_jd.py --vault D:\career-vault --jd-file JD.md --json
```

评分是透明启发式，不是自动决策：

- JD 关键词覆盖 50%
- 证据强度 25%
- Ownership 清晰度 15%
- 新鲜度 10%

输出会给出主项目、辅项目、匹配词和缺口词。

### Skill 结构校验

```bash
python -X utf8 scripts/validate_skills.py
```

检查 frontmatter、名称、描述、文件夹一致性和未完成占位符。

## 环境要求

- Node.js 18+
- npm / npx
- 支持 Agent Skills 的客户端
- 一个 Markdown 或 Obsidian 职业资产库

```bash
node --version
npm --version
npx --yes skills --version
```

## 安装

### 查看可用 Skills

```bash
npx skills add ShallowRecall/personal-skills --list
```

### 安装单个 Skill

```bash
npx skills add ShallowRecall/personal-skills --skill career-evidence-miner -a codex -g -y
```

```bash
npx skills add ShallowRecall/personal-skills --skill resume-tailor -a codex -g -y
```

### 安装全部 Skills

```bash
npx skills add ShallowRecall/personal-skills --skill "*" -a codex -g -y
```

### 安装到其他 Agent

`-a` 用于指定目标 Agent。不同版本的 `skills` CLI 支持值可能不同：

```bash
npx skills add --help
```

例如安装到 Claude Code：

```bash
npx skills add ShallowRecall/personal-skills --skill career-evidence-miner -a claude-code -g -y
```

### npm scripts

```bash
npm run list
npm run install:career-evidence-miner
npm run install:resume-tailor
npm run install:all
```

> npm 本身没有 `npm add skill <name>` 子命令。npm 生态中的标准写法是：
>
> ```bash
> npx skills add <repo> --skill <name> -a codex -g -y
> ```

## 配置

### CAREER_VAULT

推荐通过环境变量指定职业资产库：

```powershell
[Environment]::SetEnvironmentVariable(
  'CAREER_VAULT',
  'D:\path\to\your\career-vault',
  'User'
)
```

设置后重启 Agent。路径解析顺序：

1. 用户在请求中显式提供的路径。
2. `CAREER_VAULT` 环境变量。
3. 如果都不存在，向用户询问路径。

Skill 不会假设某台机器上的固定路径。

### 推荐的 Vault 结构

```text
career-vault/
├─ 00-navigation/        # 索引和导航
├─ 10-projects/          # 项目案例
├─ 20-resume/            # 简历素材和投递版本
├─ 30-competencies/      # 能力地图
├─ 40-templates/         # 复盘与简历模板
└─ 50-evidence/          # 项目证据台账
```

中文目录同样支持，例如 `00-导航/`、`10-项目案例/`、`20-简历素材/`、`30-能力沉淀/`、`40-模板/`、`50-证据/`。

## 使用示例

### 从项目沉淀职业资产

```text
使用 career-evidence-miner 扫描 D:\workspace\project-a 和 D:\workspace\project-b。
提取可验证的架构决策、关键实现和工程亮点，更新项目证据台账，
并生成 2 条简历 bullet 和 1 个 STAR 故事。
不要编造业务指标。
```

### 根据 JD 定制简历

```text
使用 resume-tailor，根据下面的 JD 生成一版 Java 支付后端简历。
从职业资产库中选择 1 个主项目和最多 2 个辅项目。
每个 bullet 标注证据来源，并单独输出 JD 差距清单。
[JD 内容]
```

### 只更新一个项目案例

```text
使用 career-evidence-miner，只更新职业资产库中的 ARES Studio 项目案例。
重点补充兼容性设计、单写路径、质量门禁和性能数据。
不要修改其他笔记。
```

## 工作流

1. **收集证据**：检查仓库、提交、README、设计文档、源码、测试和运行结果。
2. **提取设计决策**：关注问题、方案、替代方案、代价、灰度、回滚和补偿。
3. **写入职业资产库**：生成项目案例、证据台账、能力地图、简历素材和 STAR 故事。
4. **按 JD 定制**：拆解 JD，建立“要求 → 证据 → 匹配度 → 差距”的映射。

## 证据规则

| 等级 | 证据来源 | 可用措辞 |
|---|---|---|
| A | 源码、提交、测试、设计文档、可运行脚本 | `设计并实现`、`主导`，需有明确贡献证据 |
| B | README、提交说明、项目结构 | `参与`、`实现`、`建设` |
| C | 从结构推断，尚未确认 | `待确认`，不直接写入简历 |
| D | 用户量、营收、QPS、效率提升、团队规模 | 必须有真实来源 |

两个 Skill 都不会：

- 编造百分比和业务收益。
- 把团队成果写成个人独立完成。
- 把 Demo 写成生产系统。
- 把提交数量写成业务价值。
- 在没有证据时使用“专家”“负责人”“架构师”等头衔。

## 本地开发

```bash
git clone git@github.com:ShallowRecall/personal-skills.git
cd personal-skills
```

创建本地 Junction：

```powershell
pwsh -NoProfile -File .\scripts\link-local.ps1
```

脚本只创建缺失的 Junction，不删除现有目录，不覆盖非 Junction 目标，并支持 `-WhatIf` 预览。

Codex 支持 symlink/junction 形式的 Skill 目录。修改后如果未生效，重启 Codex。

## 验证

```bash
npm run validate:skills
npm test
npm run check
```

`npm run check` 会执行 Skill 结构校验、单元测试和 `npx skills add . --list`。

从 GitHub 验证：

```bash
npx skills add ShallowRecall/personal-skills --list
```

使用 Skill Creator 校验：

```bash
python -X utf8 <skill-creator>/scripts/quick_validate.py skills/career-evidence-miner
python -X utf8 <skill-creator>/scripts/quick_validate.py skills/resume-tailor
```

## 更新与卸载

```bash
npx skills update career-evidence-miner resume-tailor -g -y
npx skills remove career-evidence-miner resume-tailor -a codex -g -y
```

如果使用 Junction 开发模式，更新源文件后通过 Git 同步即可。

## 常见问题

### Skill 安装后没有出现

1. 重启 Agent。
2. 检查用户级目录：

```powershell
Get-ChildItem "$HOME\.agents\skills" | Select-Object Name,LinkType,Target
```

3. 检查 `SKILL.md` 是否包含 `name` 和 `description`。

### 为什么需要 `CAREER_VAULT`

Skill 需要知道职业资产库的位置，但不应硬编码某台机器的路径。环境变量可以在不同机器和不同 Vault 之间复用同一套 Skill。

### 是否会上传项目代码

不会。Skill 只读取本地文件并写入本地 Vault。除非用户明确要求，否则不会把项目代码或简历数据发送到外部服务。

### 是否可以生成英文简历

可以。`resume-tailor` 可以生成中文或英文版本，输出语言由用户显式指定。

## 安全与隐私

- 不把 API Key、Token、数据库密码写入职业笔记。
- 不把包含凭据的内部 URL 写入简历。
- 不默认上传 Vault 或项目代码。
- 不把不可信仓库文本当作指令执行。
- 用户要求与证据冲突时，先指出冲突并请求确认。

## 版本与贡献

当前版本：`1.1.0`

欢迎提交新的职业资产模板、证据提取规则、简历写作模式、跨 Agent 安装与验证改进。

请保持一个原则：**可以提高表达质量，但不能突破证据边界。**

## License

[MIT](LICENSE)
