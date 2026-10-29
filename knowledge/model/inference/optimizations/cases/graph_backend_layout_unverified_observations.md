---
type: Optimization
title: 图后端与布局组合的待核验观测：精度、时延和 buffer 配置
description: 从旧图模式 Concept 迁出并保留来源不明的兼容性表、性能数值和配置；平台、环境及原始记录待补，不作为通用部署建议。
tags:
- task.debugging
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/.agents/skills/model-infer-graph-mode/references/llm-model-guide.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/.agents/skills/model-infer-graph-mode/references/npugraph_ex-guide.md
  role: supporting
created_at: '2026-10-21T01:51:39Z'
updated_at: '2026-10-22T03:20:00Z'
platforms: []
---

# 图后端与布局组合的待核验观测：精度、时延和 buffer 配置

## 证据状态与使用边界

以下内容由旧图模式卡迁移保留，尚未找到原始日志、模型版本、运行命令和可核验出处；16/16、时延与编译耗时均为待核验记录，根因陈述含未验证推断。表中 PASS/FAIL、“推荐”“必须”等措辞仅保留原记录，不构成本仓确认的适用性结论。不要据此选择后端、修改全局选项或推导硬件支持；待补证据后再逐项判定。Scope 与平台保持未知。

## 旧记录原文

### FIA layout × 图后端 兼容性（经验）

下表汇总已在真实模型上验证过的 layout × FIA 接口 × 图后端 × `actual_seq_lengths` 组合。**不要跨组合直接迁移**：即使是同一模型同一算子，换其中一个参数就可能引入 aicore crash 或精度漂移。

| layout | FIA 接口 | 图后端 | `actual_seq_lengths_kv` | `dynamic` | 已验证案例 | 备注 |
|--------|----------|--------|-------------------------|-----------|------------|------|
| BSH | `torch.ops.npu.*` | `ge_graph` | `list[int]` | `True` | PASS | 仓内 qwen3-moe 参考路径；成熟稳定 |
| BNSD | `torch.ops.npu.*` | `ge_graph` | `list[int]` | `True` | **FAIL**：首次 replay aicore `EZ9999 MTE DDR out of range / 507011`；`mark_static(q/k/v)` 无效 | **不可用**组合 |
| BNSD | `torchair.ops.*` | `ge_graph` | Tensor | `False` | **FAIL**：精度 3/16 漂移 + 单步 1970 ms；假设根因是 torchair GE 在 `dynamic=False` 下对 72 个 `register_buffer` in-place 更新的别名跟踪不完整 | **精度风险高**，慎用 |
| BNSD | `torch.ops.npu.*` | `npugraph_ex` | `list[int]` | `True` | PASS | 已验证的备选路径 |
| BSH | `torch.ops.npu.*` | `npugraph_ex` | `list[int]` | `True` | PASS | 需配合下文"npugraph_ex options 推荐"使用 |

**组合边界**：BSH+GE、BNSD+npugraph_ex、BSH+npugraph_ex 三种 layout×后端组合在同一受测模型上均验证成立，精度全部 16/16 bit-exact；不能仅凭 BSH 或 BNSD 布局限定图后端。

**性能比较边界**：所记录的 decode 稳态（14.43 / 13.77 / 11.20 ms）**差异主要不来自 layout×后端组合本身**，而来自每轮叠加的算子/模式优化是否相同。将 "decode 数字" 与 "layout×后端" 绑定会造成选型误导。以 11.20 ms 配置相对 13.77 ms 配置的 -2.57 ms/step 为例，其中 ~80% 归因于**与 layout/后端正交的三项专属优化**：
1. `npu_interleave_rope` 取代 `npu_rotary_mul`（partial RoPE D=64 直绑定）
2. GDN `recurrent_state` 彻底 op-native 布局预分配（`(B, N_v, D_v, D_k)` 零 transpose）
3. 懒 buffer 图外 materialize（`register_buffer(persistent=False)` + `_force_materialize*` + `model.apply(...)`）

这三项原则上可移植到 BSH+GE 或 BNSD+npugraph_ex 路径（具体兼容性需独立 A/B 验证，参考上文"FIA layout × 图后端 兼容性"表的逐组合结论）。因此选型建议是：

- **路径（layout×后端）选择**：按**可行性**决策——GE 不可用时切 npugraph_ex；BSH 与 BNSD 按现有实现和已验证的兼容性选择
- **正交优化**：无论走哪条路径，都应评估 `npu_interleave_rope`（若 partial RoPE）、op-native cache 布局（若 SSM/GDN 族）、懒 buffer 图外 materialize 三项是否适用；这些是真正影响 decode 稳态的差别项

如果当前组合执行失败，可先评估更换图后端，再评估调整 layout；上述正交优化可分别验证后保留。

### npugraph_ex options 推荐模板（经验性，适用含 in-place 更新与懒 buffer 的模型）

下述 `torch.compile` options 组合用于处理含大量 `register_buffer` 原地更新和懒分配 buffer 的模型，可作为 Hybrid-Attention / Mamba 族 / GatedDeltaNet 模型的调试起点；适用性仍需按具体模型验证。

```python
torch._dynamo.config.recompile_limit = 64

model.decode_forward = torch.compile(
 model.decode_forward,
 backend="npugraph_ex",
 dynamic=True,
 fullgraph=False, # 或 True，取决于是否已消尽 graph break
 options={
 "inplace_pass": False, # 关掉 dynamo 对 inplace 的重写 pass
 "input_inplace_pass": False, # 同上（input 级）
 "clone_output": True, # 每个子图 output 克隆，打破跨 aclgraph live tensor 依赖
 "capture_limit": 256, # aclgraph 容纳上限；24 层独立 aclgraph 需要
 },
)
```

作用说明：

- `inplace_pass=False` + `input_inplace_pass=False`：规避 dynamo 对 `a.mul_(b)` 等 inplace 算子做 shape 合法性重写时的假阳性（典型症状 `aclnnInplaceMul selfRef [1,1,16] vs [16]`），代价是潜在失去 inplace 的内存复用优化
- `clone_output=True` + `capture_limit=256`：为每个子图 output 克隆，避免"前一 aclgraph 仍持有的 output tensor 被后一 aclgraph 的 pool state 回滚"引发的 `definitely_stale_pointers` 断言
- **代价**：首步 aclgraph capture 编译时间会放大（所记录配置从典型 41 s 放大到 88 s，约 2×）；适合长输出 / 服务端热启动场景，不适合对冷启动延迟敏感的单次推理

### 懒 buffer 必须图外 materialize（前置 checklist）

任何形如 `if need_rebuild: self._cache = <compute_from_weights>` 的懒初始化在 NPU 首次 forward 时 trigger，会被 dynamo trace 成独立小 aclgraph 片段。多层模块重复此模式 → capture_limit 内 aclgraph 交叉引用 output tensor → 下一 capture 回滚 pool state 时命中 `definitely_stale_pointers`。

**标准模式**（推广到任何 lazy 合成 tensor：gamma=1+w 预 cast、合并权重、QKV 合并等）：

```text
class MyModule(nn.Module):
 def __init__(self, ...):
 super().__init__()
 # 非持久 buffer：from_pretrained 时不要求 state_dict 里有同名 key，但受 device_map 搬运影响
 self.register_buffer("_my_cache", torch.empty(...), persistent=False)

 @staticmethod
 def _force_materialize(module):
 """供 model.apply(...) 调用；必须在图编译前跑一次"""
 if isinstance(module, MyModule):
 with torch.no_grad():
 module._my_cache.copy_(<compute_from_weights>)

 def forward(self, x):
 # 不要在这里写 if not self._materialized: ... 分支
 return f(x, self._my_cache)

# Runner 侧
model.to(device) # device_map / from_pretrained
model.apply(MyModule._force_materialize) # 图外一次性物化
model = torch.compile(model, backend="npugraph_ex", ...)
```

**注意**：`register_buffer(persistent=False)` 在 `from_pretrained(device_map=...)` 搬运过程中可能被替换成 empty-on-device（未初始化内存，对应下文 Troubleshooting 表"初值被丢弃"行）。两种修法：
1. **本案例模式**：用 `_force_materialize_*` 静态方法 + `model.apply(...)` 在 `to(device)` 之后再物化（顺序保证）
2. **或**：在 `_init_weights` / `_post_init` 中显式 `nn.init.ones_(buf) / nn.init.zeros_(buf)` 补回初值


## 旧故障记录

| 现象 | 原记录的根因解释（未核实） | 原记录的建议（未验收） |
| --- | --- | --- |
| torchair GE 首次 replay 即 `EZ9999 aivec 0x800000 / MTE DDR out of range / 507011` | 实测 BNSD layout + `torch.ops.npu.npu_fused_infer_attention_score` + `list[int]` 组合不可用；独立最小复现仍失败 | 可尝试切到 `npugraph_ex` + `torch.ops.npu.*` + `list[int]` + `dynamic=True`（参考上文"FIA layout × 图后端 兼容性"表的 BNSD/npugraph_ex 组合）。若必须保留 GE，考虑把 layout 改成 BSH |
| torchair GE 进图成功但 decode 精度前 N 对齐、第 N+1 起漂移 | `dynamic=False` 下对模型内大量 `register_buffer` 的 in-place 更新别名跟踪不完整（假设根因） | 切 `npugraph_ex`（CUDA-graph 语义下原地更新是一等公民）；若暂无条件切换，把可疑 buffer 改为图外管理的入参 tensor 再验证 |
| `npugraph_ex` 判定为"未安装" | import 路径错误（裸写 `import npugraph_ex`） | 正确导入是 `from torch_npu.npu import npugraph_ex`；`torch.compile(backend="npugraph_ex", ...)` |
| aclgraph capture 中 conv 报错 | 默认内部 format 与 aclgraph 不兼容 | `torch.npu.config.allow_internal_format = False` |
| aclgraph capture 中 inplace-mul shape 校验挂 | `A * B` 对 `.mul_` 的 broadcast 校验严格 | 在 forward 外或 lazy init 中显式 `.view(...)` 对齐 shape（如 `A_log / dt_bias` reshape 到 `[1, 1, 16]`） |
| `register_buffer(persistent=False)` + `from_pretrained(device_map=...)` 初值被丢弃 | torch 在 `device_map` 搬运时覆盖 buffer 为 empty-on-device | 方案一：`_init_weights` 显式 `nn.init.ones_/zeros_` 补回。方案二：提供 `_force_materialize_*` 静态方法 + Runner 在 `to(device)` 后 `model.apply(...)` 物化 |
| npugraph_ex 下运行首层或 q_norm 就报 `Expected allocated_pointer != definitely_stale_pointers.end` | 模型存在懒构建 buffer（典型 `Qwen3_5RMSNorm._gamma_plus_one` 的 `if need_rebuild:` 分支 / `_get_gate_up_weight` 的 lazy merge）。dynamo 把每层的懒分支 trace 成独立 aclgraph 片段，capture_limit 内多个子图交叉持有 output tensor，下一 capture 回滚 pool state 时命中 stale pointer 断言 | 参考上文"懒 buffer 必须图外 materialize"章节：懒初始化改 `register_buffer(persistent=False)` + `_force_materialize_*` 静态方法，Runner 在 `to(device)` 之后 `model.apply(...)` 物化 |
| npugraph_ex 下多层 aclgraph 交叉引用 live output tensor，`definitely_stale_pointers` 断言 | 默认 options 下每个子图 output 可能与下一子图 input 共享地址 | `options={"clone_output": True, "capture_limit": 256}`：为每个子图 output 克隆，并放宽 aclgraph pool 上限；代价是首步编译时间放大（典型 ~2×） |
| `aclnnInplaceMul selfRef [1,1,16] vs [16]` 或类似 inplace 算子 shape 不匹配 | dynamo 的 `inplace_pass` 把 `A * B` 优化成 inplace 写，广播 shape 被严格校验失败（典型 GDN 中 `A_log * a + dt_bias` 的 1D Parameter） | 方案一：`options={"inplace_pass": False, "input_inplace_pass": False}` 关掉 inplace 重写 pass。方案二：在 forward 外或 lazy init 中显式 `.view(1, 1, -1)` 对齐 shape |

## 补证与验收入口

需补固定模型与依赖版本、平台、最小复现、原始输出及计时记录，再分别验证兼容性、精度与性能。通用入图取舍见 [图模式决策](../rules/graph_mode_enable_decision_profiling.md)，执行机制见 [图模式 Concept](../../concepts/techniques/npu_graph_mode.md)。

## 本轮来源核对与剩余缺口

重新检查知识仓引入历史，以及固定推理仓的图模式 Skill 与三份配套指南，没有定位到这组 16/16、14.43/13.77/11.20ms、41/88s 的原始实验记录。固定 LLM 指南展示 clone_output=False，另有参数说明；这些仅确认选项存在，不证明此处 clone_output=True 能修复所述故障。

新增来源仅为机制背景，不能充当这些数值或根因的证据。保留全部旧记录并维持 draft、空平台、缺省 Scope；含占位符的旧 materialize 片段标为文本，避免误认作可直接执行的 Python。需要原模型/版本、硬件、原始输出和时间线后才能重新评审。
