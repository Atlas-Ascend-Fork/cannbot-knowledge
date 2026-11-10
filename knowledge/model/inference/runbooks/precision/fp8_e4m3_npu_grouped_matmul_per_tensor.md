---
{
  "type": "Runbook",
  "title": "FP8(E4M3) npu_grouped_matmul 静态 per-tensor 激活 scale 的接入语义与前置校验",
  "description": "在 Ascend950PR_9589 / torch_npu 2.12.0 / CANN 9.1.0 上实测 npu_grouped_matmul 的 FP8 反量化链为乘法：out[m,n] = (xq[m] @ w[e]) × scale[e,n] × per_token_scale[m]（对乘法参考 max_abs 0.0266，对加法形式偏差 1.4356，排除加法解释）。静态 per-tensor 激活方案接入：每条路由行的 per_token_scale 取该行所属专家的 input_scale，per-N 反量化 scale 由 weight_scale 广播（w13 两个 [gate|up] 半区分别取 gate/up 的 weight_scale）；前置校验确认该 checkpoint 全部 2048 个专家的 gate/up input_scale 两两相等，w13 合并后可共享一行 scale。FP8 grouped_matmul（含静态 per-tensor 变体）在该设备可执行，文档 dtype 列表未列 FP8 属文档滞后。",
  "tags": [
    "task.implementation",
    "topic.precision",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# FP8(E4M3) npu_grouped_matmul 静态 per-tensor 激活 scale 的接入语义与前置校验

## 适用场景

- 模型/框架：W8A8 FP8（E4M3 权重 + 静态激活）MoE 模型在 torch_npu 上接入 `npu_grouped_matmul` 做专家批量计算（本轨迹为 Hunyuan-A13B-Instruct-FP8 的 64 专家 bank，w13=[E,H,2I]、w2=[E,I,H]）。
- 平台/版本：Ascend950PR_9589 单卡，torch_npu 2.12.0，CANN 9.1.0。
- 目标：确认 FP8 grouped_matmul 的反量化语义（scale / per_token_scale 如何组合）并给出静态 per-tensor 激活 scale 的正确接线方式；单算子冒烟 + 语义探针 + checkpoint 全量前置校验。
- 缺失信息：官方文档 dtype 列表未列 FP8，语义结论来自本机单算子实测；其他 CANN 版本未验证。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

- 触发：模型激活量化为静态 per-tensor（`input_scale`），而 `npu_grouped_matmul` 的量化参数有 `scale`（per-N/per-channel）与 `per_token_scale`（per-token）两路，文档未直接给出静态方案的接法，且 x/weight 支持列表未含 FP8。
- 客观观测一（冒烟）：analyzer 在设备上以 E=64、H=4096、N=6144、R=168 复现 FP8 GMM，输出 `FP8 GMM w13 OK (168, 6144)`、`FP8 GMM static OK (168, 6144)`——含与本模型一致的静态 per-tensor scale 变体可跑通。
- 客观观测二（语义探针，implementer）：4 专家、per-expert 计数 [2,1,0,3] 的最小用例，输出 `max abs diff vs (xq@w)*scale*pts: 0.026586242020130157`、`diff vs additive form: 1.4356098175048828`——乘法解释成立、加法解释被排除。
- 客观观测三（前置校验）：对 checkpoint 全部 32 层 × 64 专家的 gate_proj/up_proj `input_scale` 逐对比较，输出 `experts checked 2048 gate!=up count 0`。

## 探针与操作

FP8 GMM 语义探针（逐字，${LOCAL_PATH_1} 核心）：

```
out = torch_npu.npu_grouped_matmul([xq_d],[w13],scale=[sc],per_token_scale=[pts],
    group_list=gl, split_item=3, output_dtype=torch.float32, group_type=0, group_list_type=1, tuning_config=[0])[0]
ref=torch.zeros(M,N); o=0
for e,c in enumerate(tokens):
    for i in range(c):
        m=o+i
        ref[m] = (xq[m].float() @ w_bf[e]) * scale[e] * row_scale[m]
    o+=c
```

静态 per-tensor 方案的生产接线（`HunYuanMoE.fuse_experts()` 内 per-N 反量化 scale 构造，逐字）：

```
            # per-N dequant scales consumed directly by npu_grouped_matmul
            I_ = I
            self.w13_scale_gmm = nn.Parameter(
                torch.cat([
                    self.w13_weight_scale[:, 0:1].expand(E, I_),
                    self.w13_weight_scale[:, 1:2].expand(E, I_),
                ], dim=1).contiguous(), requires_grad=False
            )                                    # [E, 2I]
            self.w2_scale_gmm = nn.Parameter(
                self.w2_weight_scale.view(E, 1).expand(E, H).contiguous(),
                requires_grad=False,
            )                                    # [E, H]
```

前向使用（见[Hunyuan-A13B FP8 在 Ascend950PR 上 A1–A5+M1–M3 融合算子全链路替换与端到端验证](../performance/hunyuan_a13b_fp8_ascend950pr.md) 的 `_fused_forward` 引文）：每条路由行先按所属专家的 `input_scale` 显式 `_quant_fp8` 量化，`per_token_scale=[row_is13/row_is2]` 传入同一 per-row scale，`scale=[w13_scale_gmm/w2_scale_gmm]` 传 per-N 权重反量化 scale，`group_list=tokens_per_expert`（count 模式，`group_list_type=1`）、`split_item=3`、`group_type=0`。

## 机制与判别

- 反量化链为乘法 `out[m,n] = (xq[m] @ w[e]) × scale[e,n] × per_token_scale[m]`：探针对乘法参考 max_abs=0.0266（E4M3 量化噪声量级），对加法形式偏差 1.4356（远大于量级），判别明确。
- 静态激活方案中 `per_token_scale` 的物理含义是「该行的激活量化 scale」：与显式 `_quant_fp8(x, input_scale)` 配对后，GMM 输出即反量化回 bf16；w13 合并 [gate|up] 后两半的 per-N scale 分别取 gate/up 的 `weight_scale`。
- gate/up `input_scale` 两两相等（2048/2048）使每行只需一个 per-row scale；若某 checkpoint 不满足该性质，w13 合并方案需改为两次独立 GMM 或按半区分 scale，否则量化语义漂移。
- 小模型上 fused（含 FP8 GMM 链）vs 原 per-expert dense 路径 `max abs diff 0.0`（argmax 一致），端到端 golden cosine 0.99989、token 全匹配——接线正确性的双重闭环。
- 未验证推断：`tuning_config=[0]` 的调优含义未深入测试；FP8 + NZ 格式的 GMM（参考实现 `Fp8PerTensorMoEGMMMethod` 注释称 NZ fp8 grouped matmul 在 per-tensor 专家下故障、须用 ND kernel）未在本轨迹复现。

## 验证信号

（平台：Ascend950PR_9589 / torch_npu 2.12.0 / CANN 9.1.0）

- c1：npu_grouped_matmul 的 FP8 反量化链为乘法：out[m,n] = (xq[m] @ w[e]) × scale[e,n] × per_token_scale[m]；实测对乘法参考 max_abs=0.0266，对加法形式偏差 1.4356，排除加法解释。〔signals：来源记录#173，单算子探针单次运行〕
- c2：静态 per-tensor 激活方案接入方式：每条路由行的 per_token_scale 取该行所属专家的 input_scale（gate/up 共享同一 input_scale，checkpoint 全量核对 32 层 × 64 专家 = 2048 对无例外），per-N 反量化 scale 由 weight_scale 沿 N 广播（w13 两半分别取 gate/up 的 weight_scale）。〔signals：来源记录#151（全量核对）、来源记录#248（tiny fused vs dense max_abs=0.0，单次运行）〕
- c3：FP8(E4M3) grouped_matmul（含与本模型一致的静态 per-tensor scale 变体）在 Ascend950PR/CANN 9.1.0 上可执行且输出 shape 正确（FP8 GMM w13 OK (168, 6144)；FP8 GMM static OK (168, 6144)）；官方文档 x/weight dtype 列表未列 FP8，属文档滞后，接入前须先做单算子冒烟。〔signals：来源记录#146，单算子冒烟单次运行〕

## 适用与失效边界

- 适用：静态 per-tensor 激活 scale 的 FP8 权重 MoE/多矩阵批量计算；per-expert 标量 weight_scale 可广播为 per-N scale 的场景。
- 失效/风险边界：文档 dtype 未列 FP8 意味着该能力非承诺契约，CANN/torch_npu 升级后可能变化，接入前必须重跑冒烟；`npu_grouped_matmul_finalize_routing`（GMM+finalize 融合版）weight 仅 int8/int4 且 a8w8 要求 NZ，FP8 权重不可用（见 [五类 torch_npu 融合算子对 FP8 GQA MoE 模型（Ascend950PR/torch_npu 2.12.0）的实测不适配边界](torch_npu_fp8_gqa_moe_ascend950pr.md)）；动态激活方案（npu_dynamic_quant 出 per-token scale）的接法未在本轨迹验证。
- 停止条件：若乘法语义探针失败（对乘法参考 max_abs 显著超出量化噪声量级）、或 gate/up input_scale 校验出现不等对，应停止 w13 合并接线并回到 per-expert 量化。
