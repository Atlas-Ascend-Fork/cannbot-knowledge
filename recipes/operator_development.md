# 使用知识库进行算子开发

本 Recipe 介绍了使用知识库进行算子开发的路径：安装知识库，检索算子设计、API 与调试轨迹知识，把命中的知识落实到实现和验证中。

## 目标

使用知识库辅助完成算子需求理解、路线选择、API 使用、问题诊断和迭代验证，减少重复翻阅资料和无证据试错，并让最终实现能够说明采用了哪些知识、适用于什么范围、经过了哪些验证。

## 适用场景

- 从零开发 ACLNN 或 Direct Ascend C 算子，需要了解算子语义、主要路线和边界处理；
- 已有实现存在编译、精度、运行时或性能问题，需要结合 API 与历史轨迹定位；
- 需要针对特定硬件平台、CANN 版本、数据类型或布局选择实现方案；
- 需要把算子设计知识、API 知识和 runbook/轨迹知识组合进同一开发过程；
- 需要让开发 Agent 在编码前检索知识，并在交付时说明知识依据和验证范围。

## 不适用场景

- 知识根不可用、知识卡校验失败，或目标技术、平台和算子模式尚未明确；
- 需要逐行阅读官方原始文档、源码或补丁历史，知识卡的摘要粒度无法满足任务；
- 需要证明某个实现已经正确或性能达标——知识只能辅助设计，不能替代真实编译和评测；
- 目标算子和相关 API 尚未收录，且任务不允许使用官方资料、源码或实验进行补充；
- 多张知识卡在相同适用范围内冲突，而现有证据无法消除冲突。

## 前置条件与输入

- Python 3.10 或更高版本；
- 可访问的 `cannbot-knowledge` 仓库，以及可用的 `knowledge-query` Skill 或 `knowledge_query.py`；
- 已存在的算子开发项目和真实开发验证入口；
- 目标算子名、`aclnn`/`direct` 调用方式、目标平台和已知 CANN 版本；
- 输入输出语义、数据类型、布局、形状范围、精度要求和性能目标；
- 若为问题修复，还应准备最小失败现象、发生阶段、日志和当前实现路线。

## 步骤

### 1. 安装知识库

克隆知识仓并安装运行依赖：

```bash
git clone https://gitcode.com/cann/cannbot-knowledge.git
cd cannbot-knowledge
python3 -m pip install -r requirements.txt
```

将查询 Skill 安装到已有的算子项目。日常开发使用 `consumer` 模式即可：

```bash
bash init.sh claude /path/to/operator-project consumer
# 也可以将 claude 替换为 opencode 或 agents
```

安装器只在目标项目中创建项目级 Skill 符号链接，不复制知识正文，也不修改全局配置。知识仓移动后，先移除或改正目标项目中原有的 `knowledge-query` 链接，再从新仓库位置运行 `init.sh`；只更新 `CANNBOT_KNOWLEDGE_ROOT` 只能改变查询器的知识根定位，不能修复已经失效的 Skill 链接。

### 2. 初始化与验证

先确认 Python 版本不低于 3.10，再用 `discover` 检查知识根、知识卡和查询器是否可用：

```bash
export CANNBOT_KNOWLEDGE_ROOT=/path/to/cannbot-knowledge
export KNOWLEDGE_QUERY="$CANNBOT_KNOWLEDGE_ROOT/.agents/skills/knowledge-query/scripts/knowledge_query.py"

python3 "$KNOWLEDGE_QUERY" \
  --knowledge-root "$CANNBOT_KNOWLEDGE_ROOT" \
  discover
```

开发直调或 ACLNN 算子时，可以只检查对应的算子子树：

```bash
python3 "$KNOWLEDGE_QUERY" \
  --knowledge-root "$CANNBOT_KNOWLEDGE_ROOT" \
  discover --operator-mode direct
```

正常输出应包含实际知识卡数量及 domain、technology、OKF type、路径 Profile、Operator mode 和 status 等统计。查询器会在检索前严格加载并校验当前作用域内的知识卡；命令报知识根不可用或卡片不合法时，应先修复仓库状态，不要继续解释查询结果。

### 3. 基本查询操作

查询时使用“实体 + 关键约束”，并保留真实的平台、技术和调用方式。以下三类查询覆盖算子开发中最常见的知识需求。

查询算子设计与可选路线：

```bash
python3 "$KNOWLEDGE_QUERY" \
  --knowledge-root "$CANNBOT_KNOWLEDGE_ROOT" search \
  --query "Softmax layout dtype route" \
  --domain ops --technology ascendc --type operators \
  --operator-mode direct --platform 950 --limit 10
```

查询 API 的签名、约束与平台支持：

```bash
python3 "$KNOWLEDGE_QUERY" \
  --knowledge-root "$CANNBOT_KNOWLEDGE_ROOT" search \
  --query "DataCopyPad GM UB 非对齐搬运" \
  --domain ops --technology ascendc --type apis \
  --platform 950 --limit 10
```

查询已沉淀的验证轨迹、故障模式和处理经验：

```bash
python3 "$KNOWLEDGE_QUERY" \
  --knowledge-root "$CANNBOT_KNOWLEDGE_ROOT" search \
  --query "DataCopyPad sub-32B blockLen validation" \
  --domain ops --technology ascendc --type runbooks \
  --platform 950 --limit 10
```

搜索结果只用于选择候选卡。选中结果后必须打开其 `local_path` 阅读正文，核对适用条件、限制和 `sources`；不要直接把摘要当作实现依据。`--type` 过滤的是路径 Profile，例如 `operators`、`apis` 和 `runbooks`。

范围过滤还需注意：

- `--platform` 接受仓库已注册的平台 ID，例如 `a2`、`a3`、`950`，不能直接填写任意产品名称；
- 已知目标版本时可以增加 `--cann-version <版本>`。显式版本只匹配声明了该版本的卡片，重复的版本条件使用 AND；零命中后应检查卡片正文的版本边界，不应直接改用其他版本结论；
- `--operator-mode` 只用于 Operator Profile。查询 API 或 runbook 时不要附加该参数；这两类查询仍会触发全仓严格校验；
- 选择候选卡时同时查看 `status` 和 `trust_tier`。`stable` 表示生命周期状态，不等同于人工复核；关键结论仍需阅读正文并核对来源。

### 4. 在算子开发中使用知识

一次完整的使用过程可以压缩为“检索、落地、验证、回查”四步：

1. **检索。** 先查询目标算子卡，确认语义、输入输出约束和按重要性排列的实现路线；再按路线涉及的操作查询 API 卡；遇到编译、精度、运行时或性能问题时，使用“错误现象 + 阶段 + 关键实体”查询 runbook 或轨迹知识。
2. **落地。** 从命中卡中整理本轮实现所需的最小信息：必须保持的语义、路线触发条件、关键 API 约束、边界处理以及已知风险。优先实现重要路线，但不能把某条路线的适用条件外推到全部输入。
3. **验证。** 在目标平台和真实工具链中完成编译、基础正确性、边界输入和性能验证。知识卡提供设计依据，不代替实际验证；卡片状态为 `stable` 也不表示实现天然正确。这里列出的验证只是通用最低证据，最终完成条件服从目标项目更严格的权威评测、精度口径、构建和交付门禁。
4. **回查。** 每次失败只围绕当前证据重新查询。先判断问题属于语义、路线选择、API 使用、资源安全还是性能，再阅读对应卡片并修改；不要在没有新证据时反复更换整体方案。

可以直接把下面的任务描述交给开发 Agent：

```text
使用 knowledge-query 完成 <算子名> 的 <aclnn/direct> 实现，目标平台为 <平台>。
开始编码前，分别检索并打开相关的算子设计、API 和 runbook/轨迹知识卡；
整理语义约束、重要路线及其触发条件、关键 API 限制和已知风险后再实现。
所有结论必须限定在知识卡声明的平台和版本范围内。
完成后在真实开发环境中验证，并报告使用的知识卡、采用的路线、验证结果和仍未覆盖的范围。
知识未命中或结论冲突时明确报告，不得用其他平台或其他技术路线代替。
```

建议保留一份简短的开发记录，至少包含：使用过的知识卡路径、当前实现路线及触发条件、关键 API 约束、验证结果、失败证据和下一步假设。这样后续迭代可以从证据继续，而不是重新猜测。

### 5. 更新与维护

知识仓更新前先确认本地没有需要保留的未提交修改，再同步远程：

```bash
cd /path/to/cannbot-knowledge
git fetch --all --prune
git pull --ff-only
python3 -m pip install -r requirements.txt
python3 "$KNOWLEDGE_QUERY" --knowledge-root "$PWD" discover
```

如果本地分支已经分叉或工作区有未提交修改，不要强行覆盖；先保存工作、确认上游分支，再选择合并或变基方式。Skill 仍通过符号链接指向同一知识仓时通常无需重新安装。

贡献或修改知识的维护者还应运行全仓门禁：

```bash
bash check.sh
```

新增知识的查重、来源、导航和治理要求见[贡献知识](contribute_knowledge.md)与 [CONTRIBUTING.md](../CONTRIBUTING.md)。

### 6. 常见问题

| 问题 | 处理方式 |
|---|---|
| `discover` 或 `search` 报知识根不可用 | 显式传入 `--knowledge-root`，并检查路径是否为知识仓根目录。 |
| 查询被其他知识卡的校验错误阻断 | 修复报错卡片或缩小到查询器真实支持的作用域；不能把校验失败当作零命中，也不能给 API/runbook 错加 `--operator-mode` 绕过。 |
| 搜索结果为零 | 检查知识覆盖、技术、平台、Profile、调用方式和关键词；零命中表示当前条件下未找到知识，不表示相关能力不存在。 |
| 结果很多但不相关 | 缩短为“实体 + 关键约束”，增加真实的平台、Profile 或 `--operator-mode` 过滤，不要堆叠描述性句子。 |
| 多张卡片结论冲突 | 比较平台、版本、路线触发条件、更新时间和来源；冲突未消除前保留多个结论。 |
| 命中其他平台或其他技术的卡片 | 不直接迁移结论；重新按真实范围查询，确需类比时明确标注为待验证假设。 |
| 找到路线但实现仍失败 | 继续查询路线涉及的 API 约束和对应故障轨迹，并用真实错误证据缩小问题范围。 |
| 更新后查询异常 | 重新安装依赖并运行 `discover`；维护者再运行 `bash check.sh` 检查知识卡、查询回归和治理规则。 |

## 预期产物

一次完成的知识辅助算子开发至少应产生以下内容：

```text
任务范围：<算子、aclnn/direct、平台、版本、dtype、layout 和 shape 范围>
知识依据：<实际打开的算子、API、runbook/轨迹知识卡路径>
实现方案：<采用的路线、触发条件、关键 API 与边界处理>
验证结果：<编译、正确性、边界、性能、真实验证入口及目标项目门禁>
未覆盖范围：<未实现路线、未验证输入域、知识冲突或外部依赖>
下一步：<由失败证据支持的下一项修改或验证>
```

代码或交付件之外，还应保留这份简短记录。它用于解释实现选择和继续迭代，不用于替代源码、构建产物或评测报告。

## 效果对比

在 [CANNBench](https://cannbench.com/leaderboard) `official-tasks 1.1.0`、Ascend 950PR 的公开基础与隐藏用例上，对比榜单方案 `direct-invoke@CANNBot GLM-5.2 OpenCode` 与 `CANNBot-Knowledge GLM-5.2`。两组均使用 GLM-5.2 和 `ops-direct-invoke-flash` 工作流；`CANNBot-Knowledge GLM-5.2` 在此基础上额外检索、阅读和使用算子知识，因此两组分别记为“Flash”和“Flash + 知识库”。比较只纳入两个方案都同时具有非零基础分和隐藏分的 11 个算子，并使用各算子的正式评测最好成绩，数据快照时间为 2026-09-03。

| 算子 | Flash 基础分 | Flash + 知识库 基础分 | Flash 隐藏分 | Flash + 知识库 隐藏分 | 总差值 |
|---|---:|---:|---:|---:|---:|
| ForeachAddcdivScalar | 83.2427 | 82.7596 | 92.0382 | 91.1486 | -1.3726 |
| SwiGlu | 75.5598 | 72.2842 | 87.7836 | 86.4726 | -4.5866 |
| ApplyRotaryPosEmb | 55.3480 | 76.0208 | 36.4166 | 22.4226 | +6.6788 |
| Cummin | 51.8063 | 59.4043 | 52.2107 | 55.7290 | +11.1164 |
| Gather | 57.9525 | 68.4756 | 20.6664 | 72.6754 | +62.5321 |
| RmsNorm | 58.2058 | 67.0300 | 60.2407 | 80.3099 | +28.8935 |
| Scatter | 53.4305 | 55.9836 | 29.6039 | 52.4031 | +25.3523 |
| Softmax | 58.2838 | 61.6525 | 42.5964 | 69.9853 | +30.7576 |
| AddRmsNormDynamicQuant | 60.6270 | 69.4774 | 62.0218 | 69.3871 | +16.2157 |
| DequantSwigluQuant | 69.5210 | 65.7826 | 80.0826 | 67.6962 | -16.1249 |
| Transpose | 50.9898 | 50.0820 | 36.7934 | 49.1205 | +11.4193 |

在这 11 个共同算子上，基础分合计由 `674.9671` 提升到 `728.9526`（`+8.00%`），隐藏分合计由 `600.4543` 提升到 `717.3503`（`+19.47%`），两项合计由 `1275.4214` 提升到 `1446.3029`（`+13.40%`）。

## 验证方式

- `discover` 能在目标知识根上成功执行，并确认目标技术和算子模式确有正文覆盖；
- 实际执行了与任务有关的算子、API、runbook/轨迹查询，而不是只浏览目录或搜索摘要；
- 已打开候选卡的 `local_path`，采用的结论没有超出卡片声明的平台、版本和路线触发条件；
- 关键 API 的签名、约束和边界处理能在知识卡正文及其来源中找到依据；
- 实现已在目标工具链中完成编译和正确性验证，性能结论来自实际采集而不是知识卡推断，并满足目标项目规定的权威验收与交付门禁；
- 开发记录中的知识卡、实现路线和验证载荷与最终代码一致；
- 仓库维护者新增或修改知识后已运行 `bash check.sh`。

## 失败或停止条件

- 知识根不可用、知识卡校验失败或查询器契约不匹配：停止检索，先修复仓库或查询配置；
- 目标范围零命中：记录知识缺口，必要时降级到官方文档、源码或受控实验，不把零命中解释为能力不存在；
- 平台、版本、语义或来源冲突：停止给出确定性路线，保留冲突并补充证据；
- 知识路线无法覆盖当前输入域：缩小适用范围或实现其他可达路线，不把局部路线强行泛化；
- 实现未通过真实环境的编译或正确性验证：只能保留为候选，不能因为知识逻辑自洽而标记完成；
- 连续迭代没有新增失败证据或可验证假设：停止盲目改动，重新确认任务语义、验证口径和知识覆盖。

## 相关规则和延伸阅读

- [知识库用户指南](../docs/user_guide.md)
- [使用知识库查询 API](api_search.md)
- [形成可追溯回答](answer_with_evidence.md)
- [`knowledge-query` Skill](../.agents/skills/knowledge-query/SKILL.md)
- [`knowledge-query` CLI 参考](../.agents/skills/knowledge-query/references/cli.md)
- [贡献知识](contribute_knowledge.md)
- [知识库贡献规范](../CONTRIBUTING.md)
