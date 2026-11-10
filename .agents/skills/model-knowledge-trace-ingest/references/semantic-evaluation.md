# 合成轨迹的语义对照记录

本记录来自 2026-11-06 的实际外层 OpenCode 调用，覆盖 normalize → mine → curate、独立审查、修订和新 subject 重审。全部输入和 ToyServe/ToyTrain/ToyNPU 均为虚构测试数据；卡片保留合成标签，未写入知识库，不构成设备验证或技术方案。

## 输入与版本

同一批 [7 个输入文件](semantic-evaluation/inputs.json) 共 31 个归一化事件，混合通用消息与工具 state 封装；a/g 为同源重复导出。每个挖掘会话处理整批，未逐轨迹启动 Agent。外层请求模型为 `cannbot/glm-5.3`，OpenCode 现场版本为 1.18.9；服务端权重版本和采样种子未固定。

- 旧快照：Git commit `c6248c95593537b12395b4e7be2486920cdf727c`，附[文件指纹](semantic-evaluation/baseline-skill-files.json)。
- 新快照首轮：[相对旧提交的补丁](semantic-evaluation/snapshots/proposed.patch)、[35 个文件的指纹](semantic-evaluation/proposed-skill-files.json)。
- 修订快照：[相对旧提交的补丁](semantic-evaluation/snapshots/revision.patch)、[46 个文件的指纹](semantic-evaluation/revision-skill-files.json)。

两份补丁已在临时目录从旧提交重建，逐文件匹配全部指纹，见[重建记录](semantic-evaluation/snapshot-reconstruction.json)。当前分支在快照之后补充了 URL 等确定性脱敏回归；当前归一化对这 7 条样本的重放 hash 与新快照一致。这组样本不覆盖真实身份信息和父会话关系，这些边界由本 Skill 的专门回归验证。

## 原始证据与实际去向

| 输入 | 原始片段/条件 | 实际去向 |
|---|---|---|
| [a](semantic-evaluation/inputs/a.json)、[g](semantic-evaluation/inputs/g.json) | `backend: cpu → toy_npu`；输出 `startup passed; one inference passed; shape=(2,4)`，exit=0 | 合并为一张修复配方，复现数 1 |
| [b](semantic-evaluation/inputs/b.json) | 独立 add_tile 随机张量微基准；背景提及 LLM，明确没有模型/框架集成 | out_of_scope |
| [c](semantic-evaluation/inputs/c.json) | before 配置 timeout_s=60，after=300；实际输出 `step 1: collective timeout at 300s`，exit=1 | negative_result，未证明修复 |
| [d](semantic-evaluation/inputs/d.json) | batch=1/input=16 与 batch=8/input=128；10 ms 与 6 ms；fast_mode 同时变化 | no_knowledge，不产生加速结论 |
| [e](semantic-evaluation/inputs/e.json) | 输出同时含 `PASS initialization` 和 `RuntimeError model did not initialize`，exit=1 | negative_result，拒绝 Agent 的 assume fixed |
| [f](semantic-evaluation/inputs/f.json) | 输出只有 initialization PASS、step 1 started，metadata.truncated=true；没有 cp=2 | deferred，不能推断全部训练步骤通过 |

两轮初始挖掘均得到 3 个候选（1 个修复、2 个失败边界），上述范围与去向一致。旧快照丢失 c/e 的退出码及 f 的截断元数据；新快照将 c/e 记为 error，f 保留 limitation。旧快照仍可根据正文中的 traceback、timeout 和 omitted 识别失败/不完整，故这组数据没有证明候选去向的质量增益。

## 独立审查与修订

首次审查实际把新快照训练组判为 NEEDS_REVISION：重建把 c 的 cp=2 填给 f，且卡片把 before 的超时配置值写成已经发生的超时观测。推理组初审记录为 PASS 并列出两项 clarity minor；另一独立会话按语义标准复核后，将未映射的通过侧判据、重建与 facts 冲突改判为 validation/evidence，新增 [NEEDS_REVISION 补充意见](semantic-evaluation/receipts/proposed-inference-addendum.json)。原始 receipt 全部保留。

Skill 随之加强同来源字段取证、配置与运行观测区分、正文额外判据的 claim 映射，以及语义 minor 不得放行。OpenCode 对完整批次修订候选、草稿、重建、账本和卡片，更新绑定 hash 后重新冻结。

| 阶段 | 推理组 | 训练组 |
|---|---|---|
| 旧快照初审 | [PASS，2 项 clarity minor](semantic-evaluation/receipts/baseline-inference-receipt.json) | [PASS，1 项 clarity minor](semantic-evaluation/receipts/baseline-training-receipt.json) |
| 新快照初审及补充意见 | [原 PASS](semantic-evaluation/receipts/proposed-inference-receipt.json) → [NEEDS_REVISION](semantic-evaluation/receipts/proposed-inference-addendum.json) | [NEEDS_REVISION](semantic-evaluation/receipts/proposed-training-receipt.json) |
| 修订后新会话重审 | [PASS，零 finding](semantic-evaluation/receipts/revision-inference-receipt.json) | [PASS，零 finding](semantic-evaluation/receipts/revision-training-receipt.json) |

重审实际逐项核对 27 个来源/产物文件的 hash、全部采用 claim/完整机制及标题摘要正文。调用方根据独立会话日志核对 sender，并用当前 review_cards.py 验证两份新 receipt 与真实 staged 字节绑定；验证器不认证运行时身份，也不替代独立阅读。

## 实际候选与最终卡

[results.json](semantic-evaluation/results.json) 保存每条输入的实际 disposition、候选 claims/角色/完整工件、来源编号映射、策展去向、复现数、验证报告及所有审查记录的 hash。以下文本文件逐字节复制实际 staged Markdown，保留历史输出以便比较：

- 旧快照 / trace-a-c1：[实际 staged 卡](semantic-evaluation/cards/baseline/inference/runtime/toyserve_backend_selection_device_mismatch.txt)，SHA-256 `3d6db8b7fc29bb86b5a41196312e3964bb23534534284198e6519e92e04b3592`。
- 旧快照 / trace-e-c1：[实际 staged 卡](semantic-evaluation/cards/baseline/inference/runtime/toyserve_adapter_initialize_negative.txt)，SHA-256 `f3d02c84f2628ea19560c5f41b7aac1577c7f3caa445c41047585d54bc7af3bb`。
- 旧快照 / trace-c-c1：[实际 staged 卡](semantic-evaluation/cards/baseline/training/runtime/toytrain_collective_timeout_raise_negative.txt)，SHA-256 `30f08d0ec663906bec8d0931a028b39f3b25a3e9aa27da3c3f2a5b8d9e5baf29`。
- 新快照首轮 / a-c1：[实际 staged 卡](semantic-evaluation/cards/proposed/inference/runtime/toyserve_backend_selection_device_mismatch.txt)，SHA-256 `9b85914426dc0c77dfb8bce326edaf6ff7f72c95dce47bd3a1dcefb61d137c2f`。
- 新快照首轮 / e-c1：[实际 staged 卡](semantic-evaluation/cards/proposed/inference/validations/toyserve_adapter_initialize_verification.txt)，SHA-256 `604d0a82f021effabff847ab244dd3401991c6c721ad66ae4ae6a3acd296a1cb`。
- 新快照首轮 / c-c1：[实际 staged 卡](semantic-evaluation/cards/proposed/training/runtime/toytrain_offload_cp2_collective_timeout.txt)，SHA-256 `ab78fac1de876980bd9c5324c54eb64255f765615463e7fe62269320b6fa6ee3`。
- 修订后 / a-c1：[实际 staged 卡](semantic-evaluation/cards/revision/inference/runtime/toyserve_backend_selection_device_mismatch.txt)，SHA-256 `9b85914426dc0c77dfb8bce326edaf6ff7f72c95dce47bd3a1dcefb61d137c2f`。
- 修订后 / e-c1：[实际 staged 卡](semantic-evaluation/cards/revision/inference/validations/toyserve_adapter_initialize_verification.txt)，SHA-256 `e3cb8a7c8da583f17541e7dda02394496148104622ddcf1fe58b159e0472227b`。
- 修订后 / c-c1：[实际 staged 卡](semantic-evaluation/cards/revision/training/runtime/toytrain_offload_cp2_collective_timeout.txt)，SHA-256 `f27a54a9347550f68c4e11f75d4b15868ec07a9134f51af488043eb58d614e1f`。

完整私有账本包含调用方绝对工作路径，公开材料使用合成来源 ID 和证据映射。公开 receipt 保持原始字节；重放没有重定位账本后冒充原 receipt，也没有把 pending 标记改成作者自授 PASS。

## 调用与用量

完成的外层会话共 5 个：旧/新两批挖掘、初审、整批修订、新会话重审。模型工具循环步数与客户端进程数分别统计：

| 会话 | 模型步骤 | input | output | reasoning | cache read |
|---|---:|---:|---:|---:|---:|
| 旧快照挖掘 | 64 | 721,503 | 23,816 | 48,304 | 6,073,984 |
| 新快照首轮挖掘 | 59 | 135,476 | 25,000 | 28,531 | 4,583,616 |
| 首次独立审查 | 50 | 754,963 | 14,589 | 30,330 | 5,236,800 |
| 批次修订 | 60 | 611,139 | 15,648 | 39,341 | 5,206,400 |
| 新会话独立重审 | 24 | 469,852 | 8,193 | 32,367 | 1,162,624 |

OpenCode 可见字段的保守累计为 **25,222,476** token（含 cache read/write，并直接累加 reasoning）。这不是费用估计；一次中断续跑没有返回可统计字段，其服务端用量未知。前置的本地模型提供方识别失败不计作完成实验。初始工作区首次建立检索索引，现场没有可比的端到端计时；本报告不提出速度、费用或生产准确率改善结论。

## 离线复核与重新实验

```bash
python3 .agents/skills/model-knowledge-trace-ingest/scripts/verify_semantic_fixture.py --output .build/model-trace-semantic-replay
```

离线入口核对已打包快照补丁的记录 hash、合成输入、实际去向覆盖、最终卡/receipt 字节及当前归一化重放；它不调用模型、不写知识，不签发语义批准，也不代替下面的 Git 快照重建。补丁与指纹用于在完整 checkout 的临时工作树重建固定 Skill 快照：

```bash
git worktree add --detach <temporary-checkout> c6248c95593537b12395b4e7be2486920cdf727c
git -C <temporary-checkout> apply <absolute-snapshot-patch>
```

由外层调用方将公开 inputs.json 中的文件位置转换为本地批输入，使用相同客户端设置，对每个快照各执行一次整批 Skill 工作流，再由独立会话审查新 subject。新的挖掘必须保留实际差异、未决项和真实审查结果；不要求复制本次候选措辞或 PASS。Skill 内不保存客户端调度命令和任务提示模板。

本次仅为一次小型合成试验。它展示了范围排除、失败/截断处理、重复归并、不可比性能抑制，以及自动通过后仍由语义审查拦截错误的实际过程；没有覆盖真实轨迹分布、所有 Agent 版本或独立硬件实验。
