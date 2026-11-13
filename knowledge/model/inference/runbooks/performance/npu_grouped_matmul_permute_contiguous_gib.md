---
{
  "type": "Runbook",
  "title": "npu_grouped_matmul 直接消费 permute(0,2,1) 非连续转置视图，免除 [E,K,N] 专家权重的 contiguous 拷贝（约 10 GiB/4 层）",
  "description": "MoE 专家权重转置为 [E,K,N] 时无需 .contiguous() 拷贝：npu_grouped_matmul 直接接受 permute(0,2,1) 非连续视图，对同一 fp32 参考的汇总误差指标与 contiguous 拷贝相同（两者均 cos=0.999998；未直接逐元素对拍两路输出）、单层融合链路时延相同（T=13: 0.732 vs 0.735 ms），L=4（3 个稀疏层）额外显存从 9.99 GiB 降至 0.04 GiB，避免逐层双份专家权重。",
  "tags": [
    "task.implementation",
    "topic.model_serving",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# npu_grouped_matmul 直接消费 permute(0,2,1) 非连续转置视图，免除 [E,K,N] 专家权重的 contiguous 拷贝（约 10 GiB/4 层）

## 适用场景

- 模型/框架：MoE 推理中专家权重需以 `[E, K, N]` 布局喂 `torch_npu.npu_grouped_matmul`（见 [npu_grouped_matmul 权重布局必须为 [E,K,N]：[E,N,K] 布局报 aclnn 161002 错误的定位与转置修复](../runtime/npu_grouped_matmul_aclnn.md)），而 checkpoint/`F.linear` 习惯布局是 `[E, N, K]`，需要转置。
- 平台/版本：Ascend950PR_9589 单卡、CANN 9.1.0、torch_npu 2.12.0。
- 目标与工作负载：HBM 受限（单卡可用 123.25 GiB）时避免为 GMM 再复制一份转置专家权重；本例 HYV4 4 层（3 个稀疏层，256 专家 × 6.49M 参数/专家，bf16 约 5.06 B MoE 权重）。34 层完整配置下 contiguous 双份权重不可行（implementer 判断）。

## 触发与观测

初版实现对转置权重调用 `.contiguous()`（来源记录 事件 207 修改前状态，即 `gate_up.permute(0, 2, 1).contiguous()`），内存探针测得额外显存（事件 219，单次观测）：

```
{
  "used_after_eager_fusion_forward_gib": 17.9,
  "used_after_fused_forward_gib": 27.89,
  "gmm_transpose_extra_gib": 9.99
}
```

即 L=4 时 GMM 转置拷贝额外占用 9.99 GiB（约为 bf16 MoE 权重总量的两倍差值：gate_up+down 一份 ≈9.4 GiB，permute+contiguous 再复制一份）。

## 探针与操作

数值与时延对照探针（来源记录 事件 226 命令原文核心段，同一进程内对 contiguous 拷贝与纯视图做 A/B）：

```
gu_c=gate_up.permute(0,2,1).contiguous(); gu_v=gate_up.permute(0,2,1)
dn_c=down.permute(0,2,1).contiguous(); dn_v=down.permute(0,2,1)
def bench(fn,n=30):
    for _ in range(3): fn()
    torch.npu.synchronize(); t0=time.time()
    for _ in range(n): fn()
    torch.npu.synchronize(); return (time.time()-t0)/n*1000
```

（`run(gu,dn)` 内为完整五算子链路 init_routing_v2→grouped_matmul→clipped_swiglu→grouped_matmul→finalize_routing。）

最终实现改为惰性缓存非连续视图（`models/modeling_hy_v4.py`，来源记录 事件 281 原文）：

```
807:     def grouped_matmul_weights(self) -> tuple:
808:         """Transpose expert weights to the ``[E, K, N]`` layout expected by
809:         ``npu_grouped_matmul`` (``x[M,K] @ w_g``).
810:
811:         Returned as strided *views* of the live parameters
812:         (``gate_up_proj [E,2I,H] -> [E,H,2I]``, ``down_proj [E,H,I] -> [E,I,H]``);
813:         ``npu_grouped_matmul`` accepts the non-contiguous transpose directly
814:         (verified numerically identical to a ``.contiguous()`` copy and with the
815:         same latency), so **no extra weight copy is allocated**. Builds no RNG
816:         and leaves the eager path / CPU golden untouched.
817:         """
818:         gate_up = self.gate_up_proj
819:         cached = getattr(self, "_gmm_weights", None)
820:         if (
821:             cached is not None
822:             and cached[0].device == gate_up.device
823:             and cached[0].dtype == gate_up.dtype
824:             and cached[0].shape == (self.num_experts, self.hidden_dim, 2 * self.intermediate_dim)
825:         ):
826:             return cached
827:         weights = (gate_up.permute(0, 2, 1), self.down_proj.permute(0, 2, 1))
828:         self._gmm_weights = weights
829:         return weights
```

（失败/回退路线：若目标 CANN 版本不接受非连续权重，可切回 `.contiguous()`，代价约 10 GiB/L=4。）

## 机制与判别

- 结论一（数值/时延等价）：npu_grouped_matmul 接受 permute(0,2,1) 非连续转置视图：与 .contiguous() 拷贝对同一 fp32 参考的汇总指标一致（contig 与 noncontig 均 cos=0.999998、maxdiff=1.9037e-02），不能由两个汇总值推出两路输出逐位一致，单层 MoE 融合链路时延相同（T=1: 0.359/0.352 ms、T=13: 0.732/0.735 ms）。锚点：来源记录 事件 226（探针命令）；信号：事件 223（`contig: ok contig=True cos=0.999998 maxdiff=1.9037e-02` / `noncontig: ok contig=False cos=0.999998 maxdiff=1.9037e-02`，小尺寸 E=8 对照 fp32 参考）与事件 227（`T=1: contig=0.359 ms view=0.352 ms` / `T=13: contig=0.732 ms view=0.735 ms`，真实尺寸 E=256）。
- 结论二（显存收益）：改用非连续视图后，L=4（3 个稀疏层）GMM 权重额外显存从 9.99 GiB 降至 0.04 GiB（permute 为零拷贝视图，data_ptr 与原参数共享）。锚点：来源记录 事件 230（实现切换 edit）；信号：事件 246（`gmm_transpose_extra_gib: 0.04`）、事件 219（对照 9.99 GiB）、来源记录 事件 218（`gate_up view: True contig: False (256, 2816, 1536)` / `down view: True contig: False (256, 768, 2816)`，data_ptr 共享复核）。
- 可区分解释：非连续视图被算子正确消费而非静默错读——两路对同一参考的汇总误差接近，支持该视图在本例可用，但汇总指标不足以排除所有 stride 误读；时延相近也不能证明算子内部没有隐式转换或拷贝。已确认的是显式权重副本被移除、视图 data_ptr 与参数共享，以及显存探针的下降。
- 未验证推断：非连续视图在其它 CANN 版本/芯片上是否仍成立（implementer 自列 reviewer 检查项 2；reviewer 在同一环境复核通过，未跨版本验证）。

## 验证信号

本组来源观测轨迹内客观观测（Ascend950PR_9589 单卡、bf16、单次运行）：

- 来源记录 事件 223：小尺寸布局/数值对照——`contig: ok contig=True cos=0.999998 maxdiff=1.9037e-02`、`noncontig: ok contig=False cos=0.999998 maxdiff=1.9037e-02`（maxdiff 相对 fp32 参考为 bf16 舍入，两者一致）。
- 来源记录 事件 227：真实尺寸时延——`T=1: contig=0.359 ms  view=0.352 ms`、`T=13: contig=0.732 ms  view=0.735 ms`（bench 30 次取平均）。
- 来源记录 事件 219 vs 246：内存探针 `gmm_transpose_extra_gib` 9.99 → 0.04（改视图前后各一次单次观测；事件 242 一次运行中探针遇到瞬态设备错误 `TsdOpen failed`，单独重跑事件 246 成功）。
- 来源记录 事件 218：`gate_up view: True contig: False (256, 2816, 1536)`、`down view: True contig: False (256, 768, 2816)`（data_ptr 共享、非连续确认）。
- 回归佐证：改视图后模块级/整网精度数字与 contiguous 版本逐位一致（来源记录 事件 238 vs 143：moe_experts_decode 0.99998409 等完全相同）。

## 适用与失效边界

- 结论限定在 CANN 9.1.0 / torch_npu 2.12.0 / Ascend950PR 的非量化 bf16 GMM 路径（`split_item=3`、`group_list_type=1`）；量化 GMM（int8/int4、NZ 格式）对 weight 连续性/格式有额外要求，非连续视图未验证。
- 视图必须基于存活参数惰性构建并缓存（本例缓存 key 校验 shape/device/dtype）；权重加载后更新参数会使缓存失效，需重建。
- 若运行环境报不接受非连续权重（版本差异），回退 `.contiguous()` 的显存代价按专家权重总量近似翻倍（本例 ~10 GiB/4 层），34 层完整配置单卡不可行。
- permute 视图本身零拷贝，但后续若有算子要求连续输入（如 clipped_swiglu 输入），只影响激活不改权重；本链路 GMM 输出为连续新张量，不受影响。
