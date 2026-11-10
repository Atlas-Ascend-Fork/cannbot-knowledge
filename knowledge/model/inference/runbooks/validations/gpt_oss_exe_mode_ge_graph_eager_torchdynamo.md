---
{
  "type": "Runbook",
  "title": "gpt_oss exe_mode=ge_graph 违反“仅支持 eager”约束时报 TorchDynamo 深层错误（与根因脱节）",
  "description": "gpt_oss 样例 YAML 注释声明仅支持 exe_mode=eager，但框架级白名单（inference_config.py:220）允许 ge_graph 通过且无模型级拦截，权重加载后的 warm-up 图捕获阶段崩溃于 TorchDynamo 内部错误 PendingUnbackedSymbolNotFound（堆栈指向 npu_fused_infer_attention_score_v2），报错与约束完全脱节。对照 deepseek_v4 在模型级 check_model_settings 拒绝 ge_graph（ValueError 直接指向约束），判别要点是模型级校验的有无。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-09T09:37:53Z",
  "platforms": [
    "a3"
  ]
}
---

# gpt_oss exe_mode=ge_graph 违反"仅支持 eager"约束时报 TorchDynamo 深层错误（与根因脱节）

## 适用场景

- 模型/框架：cann-recipes-infer `models/gpt_oss`（GPT-OSS-20B bf16），统一推理入口；gpt_oss 样例 YAML 第 4 行注释声明唯一合法执行模式（`exe_mode: "eager"       # ["eager"]`）。
- 平台/版本：Atlas A3（Ascend 910_9362 ×16）宿主机直跑，CANN 9.2.0，torch 2.10.0+cpu、torch_npu 2.10.0.post7（两条轨迹分别为 2026-10-14 dev20260924 构建 / 2026-10-16 dev20261016 构建）、transformers 5.0.0、Python 3.11.15。对照模型 deepseek_v4（容器内 torch 2.9.0 / transformers 5.0.0 / CANN 9.2.0）。
- 工作负载：对 exe_mode 声明约束做负向验证（配置越界时的报错可定位性）。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${RECIPES_ROOT}` 为cann-recipes-infer 源码根；`${SITE_PACKAGES}` 为当前 Python 解释器的 site-packages 目录。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发：把 gpt_oss_20b.yaml 的 `exe_mode: "eager"` 改为 `"ge_graph"`（其余不变）。

观测（逐字客观输出）：

- 来源记录 T 221（2026-10-14，运行 tc_gegraph.yaml）：
```
  File "${SITE_PACKAGES}/torch/fx/experimental/symbolic_shapes.py", line 1380, in compute_unbacked_bindings
    raise PendingUnbackedSymbolNotFound(
torch._dynamo.exc.InternalTorchDynamoError: PendingUnbackedSymbolNotFound: Pending unbacked symbols {u0, u1, u3, u2} not in returned outputs (FakeTensor(..., device='npu:0', size=(1, 64, 64), dtype=torch.bfloat16), FakeTensor(..., device='npu:0', size=(0,))) .
Did you accidentally call new_dynamic_size() or item() more times than you needed to in your fake implementation?
For more help, see https://docs.google.com/document/d/1RWrH-3wLEpzR9kCS6gGBNen_-Fs-8PVbWWFE5AcgeWE/edit

from user code:
   File "${RECIPES_ROOT}/executor/core/model_worker/model_worker.py", line 47, in main_decode
    return self.forward(**kwargs)
  File "${RECIPES_ROOT}/models/gpt_oss/models/modeling_gpt_oss.py", line 395, in forward
    attn_output, attn_weights = torch.ops.npu.npu_fused_infer_attention_score_v2(

[ERROR] 2026-10-14-19:22:23 (PID:2812126, Device:0, RankID:-1) ERR99999 UNKNOWN applicaiton exception
```
- 来源记录 T 246（2026-10-16，同一用例重跑，从 res 日志 grep）：
```
    raise InternalTorchDynamoError(
torch._dynamo.exc.InternalTorchDynamoError: PendingUnbackedSymbolNotFound: Pending unbacked symbols {u1, u0, u3, u2} not in returned outputs (FakeTensor(..., device='npu:0', size=(1, 64, 64), dtype=torch.bfloat16), FakeTensor(..., device='npu:0', size=(0,))) .
```
（T 239 显示崩溃发生在权重加载完成后的 warm-up 首次前向（model_worker.py:47 main_decode → modeling_gpt_oss.py:395），报错中无任何 "exe_mode"、"eager"、"gpt_oss only supports" 字样。）

## 探针与操作

探针 YAML（来源记录 C 218 写入 `tc_gegraph.yaml`，逐字；来源记录 C 209 用 `sed 's/exe_mode: "eager"/exe_mode: "ge_graph"/'` 从官方 gpt_oss_20b.yaml 派生同型用例）：

```
model_config:
  model_name: "gpt_oss"
  model_path: "${LOCAL_PATH_1}"
  exe_mode: "ge_graph"
  enable_profiler: False

data_config:
  dataset: "default"
  input_truncated_len: 4096

parallel_config:  # Set the values of attn_tp_size, moe_tp_size, and lmhead_tp_size to be the same.
  world_size: 1
  attn_tp_size: 1
  moe_tp_size: 1
  lmhead_tp_size: 1

scheduler_config:
  batch_size: 1
  max_new_tokens: 100
```

运行命令：`bash executor/scripts/infer.sh --model gpt_oss --yaml tc_gegraph.yaml 2>&1 | tail -30`；随后 `RES=$(ls -td models/gpt_oss/res/20261016/gpt_oss_tc_gegraph* | head -1); grep -E "Error|error|Exception" $RES/log_0.log | grep -v "ERR99999" | head -8` 取真实异常。

## 机制与判别

机制（框架级 exe_mode 白名单，来源记录 T 92 读取 `executor/core/config/inference_config.py` 原文，行 218-224）：

```
218:         """Validate model configuration consistency."""
219:         self.platform_version = PlatformVersion.from_value(self.platform_version)
220:         if self.exe_mode not in ["eager", "ge_graph", "npugraph_ex"]:
221:             raise ValueError(
222:                 f"exe_mode={self.exe_mode} is not supported, expected one of ['eager', 'ge_graph', 'npugraph_ex']"
223:             )
224:         if self.enable_static_kernel and self.exe_mode != "npugraph_ex":
```

- 结论 1：gpt_oss 仅支持 exe_mode=eager（YAML 注释 `exe_mode: "eager"       # ["eager"]`），但框架级校验（inference_config.py:220）白名单允许 eager/ge_graph/npugraph_ex 三值且不含模型维度，ge_graph 通过配置校验后无任何模型级拦截，权重加载完成的 warm-up 图捕获阶段崩溃于 TorchDynamo 内部错误 InternalTorchDynamoError: PendingUnbackedSymbolNotFound（from user code: modeling_gpt_oss.py:395 npu_fused_infer_attention_score_v2），报错与 exe_mode 约束完全脱节（报错中不出现约束相关信息），最终仅以 `ERR99999 UNKNOWN applicaiton exception` 收尾。
  - 信号：来源记录 T 221（完整报错原文）、T 220/C 209（探针）；来源记录 T 239（warm-up 阶段崩溃堆栈）、T 243（同型堆栈）、T 246（InternalTorchDynamoError 原文）。
- 结论 2：报错脱节的根因是两级白名单不一致——框架级白名单（上述 inference_config.py:220-223 原文）不感知模型差异，gpt_oss 模型侧又没有 check_model_settings 之类的模型级 exe_mode 拦截；对照 deepseek_v4：同样设 exe_mode=ge_graph（且 enable_static_kernel=False 避开 config 级 static_kernel 校验）时，deepseek_v4 在模型级 `check_model_settings` 明确拒绝（`[rank0]: ValueError: exe_mode='ge_graph' does not supported!`，来源记录 T 270），报错直接指向约束本身。
  - 信号：来源记录 T 270（ct5_exe_mode_gegraph 负向用例）。
  - 判别：同为"ge_graph 越界"，gpt_oss 报 TorchDynamo 内部错误（无法定位约束）、deepseek_v4 报模型级 ValueError（可直接定位约束）——差异不在 torch/dynamo 版本，而在模型级是否存在 exe_mode 校验；两模型在同仓库、同统一入口下行为不同支持该判别。
- 未验证推断（轨迹内未实施修复）：在 gpt_oss 模型加载时增加模型级校验（如 `ValueError: gpt_oss only supports exe_mode='eager', got 'ge_graph'`）可在权重加载前快速失败；两条轨迹报告均如此建议，未验证。

## 验证信号

- 来源记录 T 221：tc_gegraph 运行的完整报错原文（含 user code 堆栈指向 modeling_gpt_oss.py:395 与末行 ERR99999，2026-10-14 19:22:23）。
- 来源记录 T 239/T 243/T 246：同一用例 2026-10-16 重跑，崩溃堆栈一致、InternalTorchDynamoError 原文一致。
- 机制原文：来源记录 T 92（inference_config.py 行 220-223 白名单代码）。
- 对照组：来源记录 T 270（deepseek_v4 ct5_exe_mode_gegraph → `ValueError: exe_mode='ge_graph' does not supported!`）。
- 平台与证据等级：Atlas A3；以上均为工具结果原文；gpt_oss 场景跨两天、两个 torch_npu 构建各 1 次（共 2 次），报错逐字一致；deepseek_v4 对照 1 次。

## 适用与失效边界

- 适用：cann-recipes-infer 统一入口下 gpt_oss（含 20B；120B 未单独测 ge_graph，但模型代码同源）；判读规则：遇到 `InternalTorchDynamoError: PendingUnbackedSymbolNotFound` 且堆栈指向 modeling_gpt_oss.py 的 npu_fused_infer_attention_score_v2 时，优先检查 YAML 的 exe_mode 是否偏离 eager。
- 失效边界/未知：
  - 失败发生在约 1 分钟量级的权重加载之后（20B 39GB；120B 218GB 场景代价更高，未测），浪费排查时间；
  - npugraph_ex 对 gpt_oss 是否同样未拦截未测试（仅测了 ge_graph）；
  - PendingUnbackedSymbolNotFound 本身也可能是真实算子符号化缺陷（非配置问题）——本组来源观测仅在"配置越界"语境下观测到该错误，eager 下未复现（两样例 PASS），但不应把该错误一律归因于 exe_mode；
  - deepseek_v4 的模型级报错文案有语法瑕疵（"does not supported"，本卡来源记录 T 270），但能直接指出 exe_mode 约束；`check_model_settings` 在权重加载后的调用位置及加载先后日志，见 [deepseek_v4 纯配置校验发生在权重加载之后](deepseek_v4_custom_params.md)。
  - 修复（模型级校验）未实施，版本更新后需重新验证两级白名单是否仍不一致。
