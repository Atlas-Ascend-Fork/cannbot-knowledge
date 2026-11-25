---
{
  "type": "Runbook",
  "title": "DSV4-Flash LoRA SFT 发布迁移评分回退的否定性排查（代码/数据/合并逐项等价仍无法定位根因）",
  "description": "框架：MindSpeed-LLM（内部账号 私仓 `2453f645` 高分基线 vs `cann-recipes-train` 发布 patch 两版对照）。；任务：DeepSeek-V4-Flash-0731（DSV4）no-think LoRA SFT；数据 1,641 条 JSONL、CP16、历史/目标配置为双机A3。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# DSV4-Flash LoRA SFT 发布迁移评分回退的否定性排查（代码/数据/合并逐项等价仍无法定位根因）

## 适用场景

- 双机A3是历史/目标配置背景，本轨迹未核验对应训练实机；另一台评测机的型号不能传播为本卡此前训练和数据处理的设备范围。

- 框架：MindSpeed-LLM（内部账号 私仓 `2453f645` 高分基线 vs `cann-recipes-train` 发布 patch 两版对照）。
- 任务：DeepSeek-V4-Flash-0731（DSV4）no-think LoRA SFT；数据 1,641 条 JSONL、CP16、历史/目标配置为双机A3。
- 触发本排查的用户观测：按 recipes 发布版训练后的评分明显低于旧私仓 master 训练结果；随后用户补充固定长度（非 dynamic padding）版本也同样退分。
- 版本细节（用户报告等级）：两次训练 rank/alpha、GBS、epoch 相同；MindSpeed 版本相同；torch_npu 2.7 与 2.10 用户已各自跑过固定长度对照、分数接近（版本差异被用户排除，未在本轨迹内重跑）。

## 触发与观测

- 发布版 dynamic padding 训练评分回退；随后发布版固定长度训练评分同样回退，与 dynamic padding 版本接近（用户叙述，digest 级未深读；本卡锚定证据内以 source 0 seq 5146 的"本次退分"上下文与 source 0 seq 5888 的复核结论为准）。
- 保留的 NPU 小模型测试：固定长度与 dynamic padding 的有效 token、标签和监督数量一致，但梯度并非完全相同，整体相对差异约 2.8%——两种 padding 模式不能当作数值完全等价（source 0 seq 5146）。

## 探针与操作

逐项等价探针（均为实际执行，非只读 diff）：

1. 权重转换对照：同一组小规模权重分别走两版 HF→MCore 与 LoRA 合并，32 个 MCore 分片共 19,872 个 tensor、合并导出 34,223 个 HF tensor，名称/形状/dtype/数值全部一致（source 0 seq 5355）。
2. 真实数据对照：三份原始 JSONL 由两版完整脚本各自预处理，6 个 `.bin/.idx` 文件逐字节一致；1,641 条样本 token/label/mask 逐条检查通过；两版均过滤 5 条超长样本、样本顺序一致（source 0 seq 6455）。
3. 源码 parity：`mindspeed_llm/` 下 506/509 个 Python 文件与高分基线逐字节一致（source 0 seq 5360，探针命令见 source 0 seq 5356）。
4. LoRA 合并对照：同一组非零 LoRA 测试权重，`2453f645` 与发布版转换器分别导出，rank32/alpha64、rank64/alpha128 两组各 34,223 个 HF tensor 全部一致，配置/tokenizer/模板一致（source 0 seq 5888；保留分层与专家布局的缩小维度 CPU 测试，未用实际评分权重）。
5. 审计复核：`findings.json` 断言 `different_tensors==0`、`production_code_modified==false` 全部通过（source 0 seq 6460）。

## 机制与判别

- 假设 A「dynamic padding 数值差异导致退分」：被削弱——固定长度发布版同样退分（source 0 seq 5888 明确"不能用 dynamic padding 单独解释这次固定长度也退分"）；但 2.8% 梯度差异说明该模式并非与固定长度完全等价（source 0 seq 5146），不能反向证明完全无关。
- 假设 B「发布迁移改坏训练/合并主路径」：未获支持——训练核心、LoRA 前后向、优化器、数据加载、标签移位、checkpoint 保存/加载代码一致；固定长度启动参数（对齐 rank/alpha、GBS、路径后捕获）及环境变量一致；新增 mHC 动态通信分支的实际分支条件与注册结果检查确认不在固定长度训练中启用（source 0 seq 5888）。
- 假设 C「optimizer/RNG 保存差异」：对高分提交 `2453f645` 不适用（source 0 seq 5888）。
- 结论形态：**否定性诊断**——在相同输入、参数与环境前提下未发现迁移引入的代码 gap；退分根因仍未确定，既不能归咎 dynamic padding，也不能量化为随机波动（source 0 seq 5888）。建议路径：先用旧高分 checkpoint 做两版合并脚本逐 tensor 比较与同参数重复评测，再决定是否重训（source 0 seq 5888）。

## 验证信号

- tool_observed：19,872 MCore tensor + 34,223 HF tensor 逐项一致（source 0 seq 5355）。
- tool_observed：6 个 `.bin/.idx` 逐字节一致，1,641 样本 token/label/mask 逐条通过（source 0 seq 6455）。
- tool_observed：`mindspeed_llm` 506/509 Python 文件逐字节一致（source 0 seq 5360）。
- tool_observed：rank32/64 两组合并各 34,223 tensor 一致（source 0 seq 5888）。
- tool_observed：NPU 小模型固定长度 vs dynamic padding 梯度整体相对差异约 2.8%（source 0 seq 5146）。
- user_reported：发布版两轮（dynamic、固定长度）评分均低于旧版；torch_npu 2.7/2.10 固定长度分数接近。

## 适用与失效边界

- 适用：DSV4-Flash-0731 LoRA SFT 发布链路（HF→MCore→训练→mcore2hf 合并）的迁移等价性核对方法本身；两版仅脚本组织/默认值不同、核心代码一致时的排查顺序。
- 失效/限制：合并对照是保留分层与专家布局的缩小维度 CPU 测试，未覆盖实际评分权重的全尺寸数值；等价探针只能证明"未发现 gap"，不能证明两次生成效果必然相同（source 0 seq 5888）；梯度 2.8% 差异的长期训练放大效应未评估（source 0 seq 5146）。
- 停止条件：若旧 checkpoint 两版合并出现 tensor 差异，或同参数重复评测差距超过同模型重复评测波动范围，则本卡的"迁移无 gap"结论对该环境失效（source 0 seq 5888）。

## 附：断言存档

- DSV4-Flash-0731 LoRA SFT 发布版评分回退排查：tensor/数据/合并/源码逐项等价（19,872+34,223 tensor 一致、bin/idx 逐字节一致、506/509 文件一致）未发现迁移 gap；固定长度同样回退排除 dynamic padding 单独解释；根因未定，不可归为随机波动

```text
assert all(c['different_tensors']==0 for c in x['conversion']['merge_whole_shell'])
assert not x['production_code_modified']
```
