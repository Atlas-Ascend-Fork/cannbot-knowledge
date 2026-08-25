---
type: "Runbook"
title: "arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用"
description: "arch35 Select 模式0 VSEL_CMPMASK_SPR 的 selMask 有效位限 256/sizeof(T)=64，多轮迭代复用同一 64bit 掩码，count>64 时元素 p 实际取 bit(p%64)，导致跨 64 元素块掩码错配，sigmoid 区元素被误判为线性分支返回 gradOutput。"
tags: ["task.debugging", "topic.precision", "topic.implementation.masking", "topic.compute.elementwise.comparison_logic"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用

## 现象

在 `softplus_v2_grad` 算子（arch35/DAV_3510，Ascend950PR）修复 ACLNN 缓存键漏 scalar 之后，PyTorch ST 499/578 通过、79 失败。取 L1_018 用例（shape=(3,10,2,7,7,10,5,3)，self shape=(3,10,2,7,7,1,5,3) 广播，beta=17.0095，threshold=0.00401，grad=FLT_MAX）写探针 `/tmp/debug_l18e.py` 逐元素比对，观测到**同一 self 值在不同块位置输出不同**：

- block 0 pos 7（idx 7）：sf=-29.78，z=beta*sf=-506.5（< threshold，sigmoid 分支），actual=0（正确，sigmoid 下溢）。
- block 4 pos 7（idx 67）：sf=-29.78，z=-506.5（同一 sigmoid 分支），actual=FLT_MAX=3.4028235e+38（错误，线性分支值 gradOutput）。

4 次重跑结果完全相同（`run1/2/3 same as run0: True`），证明是确定性逻辑 bug，非竞态。

## 适用场景

- **工程形态**：kernel 实现（op_kernel/arch35/*.h），向量分支选择 `AscendC::Select` API。
- **API 路径**：`AscendC::Select<T, uint8_t>(dst, selMask, src0, src1, SELMODE, count)`；arch35 上 `Select.md` 声明"arch35 仅支持 VSEL_CMPMASK_SPR 模式"，但实测模式0有 count>64 限制，模式2（VSEL_TENSOR_TENSOR_MODE）可用。
- **验证平台与版本**：Ascend950PR（arch35/DAV_3510），CANN 9.0.0-beta.2。
- **适用粒度**：`operator_family`（所有 arch35 上用 `Select` 做逐元素分支、count 可能 >64 的 kernel）。
- **路线优先级**：`recommended_fastpath`（改用 VSEL_TENSOR_TENSOR_MODE）。
- **不适用或未验证场景**：count 恒 ≤64 的小块 kernel 不触发；非 arch35 平台（a2/a3）的 Select 语义未验证。

## 根因

arch35 `Select` API 的 `SELMODE` 三模式（引自 `ascendc-precision-debug/references/asc-devkit-api/basic-api/Select.md`）：

- 模式0 `VSEL_CMPMASK_SPR`：根据 selMask 在两个 tensor 中选取元素，**selMask 中有效数据的个数存在限制**（对 float 为 256B/4B=64 个）；**每一轮迭代中，根据 selMask 的有效位数据进行选择操作，每一轮迭代采用的 selMask，均为相同数值**，即多轮迭代复用同一 64bit 掩码。因此元素 p 实际取 bit(p%64)，当 `count_padded > 64` 时跨 64 元素块掩码错配：sigmoid 区（mask=false）元素若落在前 64 位恰好对应线性区（mask=true）的位置，会被误判为线性分支，返回 `gradOutput` 而非 `grad_sig`。
- 模式2 `VSEL_TENSOR_TENSOR_MODE`：selMask 无有效数据限制，**多轮迭代时每轮迭代连续使用 selMask 的不同部分**，每元素 p 取 bit p。

机制链：`Compare` 生成 bMask（uint8_t，每字节 1 bit 标记 bx>threshold）→ `Select` 模式0 只读前 64 bit 并在每 64 元素块复用 → count>64 时块 N 的元素 p 取 mask bit(p%64)（即块0对应位置的 mask）→ 块0的线性区元素 mask 恰为 true → sigmoid 区元素被当线性分支 → 返回 gradOutput（FLT_MAX）。block 0 本身不受影响（它就是掩码源），block N>0 受影响。

## 解决配方

**before**（`op_kernel/arch35/softplus_v2_grad_kernel.h` `ComputeFp32Core`，Select 用模式0）：

```cpp
    // Select: result = mask ? g : grad_sig
    //   mask=true (bx>threshold) → src0=g (线性分支)
    //   mask=false (bx<=threshold) → src1=grad_sig (sigmoid 分支)
    // arch35 仅支持 VSEL_CMPMASK_SPR 模式
    AscendC::Select<float, uint8_t>(bBx, bMask, bG, bThr,
                                    AscendC::SELMODE::VSEL_CMPMASK_SPR,
                                    static_cast<uint32_t>(count_padded));
    AscendC::PipeBarrier<PIPE_V>();
    // result 落在 bBx，由调用方 CopyOut
}
```

**after**（改用模式2，selMask 连续消耗，每元素 p 取 bit p；模式2 需预留 8K UB 临时区，已由 `kUbReserved` 保证）：

```cpp
    // Select: result = mask ? g : grad_sig
    //   mask=true (bx>threshold) → src0=g (线性分支)
    //   mask=false (bx<=threshold) → src1=grad_sig (sigmoid 分支)
    // 必须用 VSEL_TENSOR_TENSOR_MODE（模式2）：selMask 连续消耗，每元素 p 取 bit p。
    // VSEL_CMPMASK_SPR（模式0）selMask 有效位限 256/sizeof(T)=64，多轮迭代复用同一
    // 64bit mask → count>64 时元素 p 取 bit (p%64)，导致跨 64 元素块 mask 错配（实测
    // sigmoid 区元素被误判为线性分支，返回 gradOutput）。模式2 需预留 8K UB 临时区，
    // 已由 kUbReserved（UB 顶端 8192B 未分配给 TBuf）保证。
    AscendC::Select<float, uint8_t>(bBx, bMask, bG, bThr,
                                    AscendC::SELMODE::VSEL_TENSOR_TENSOR_MODE,
                                    static_cast<uint32_t>(count_padded));
    AscendC::PipeBarrier<PIPE_V>();
    // result 落在 bBx，由调用方 CopyOut
}
```

判别探针 `/tmp/debug_l18e.py`（逐块逐元素比对 actual vs golden，定位"同值异位"模式）：

```python
import torch
torch.ops.load_library("./build/libtorch_adapter.so")
from golden import compute_golden

beta=17.009491618554122
threshold=0.004012797157477129
go_shape=(3,10,2,7,7,10,5,3)
sf_shape=(3,10,2,7,7,1,5,3)
torch.manual_seed(0)
sf=torch.empty(sf_shape,dtype=torch.float64).uniform_(-100,100).to(torch.float32)
go=torch.full(go_shape,3.4028235e+38,dtype=torch.float64).to(torch.float32)
sf_b=torch.broadcast_to(sf,go_shape)
res=torch.ops.softplus_v2_grad.forward(go.to("npu"),sf.to("npu"),beta,threshold).cpu()
golden=compute_golden(go,sf,beta,threshold)
rf=res.flatten().float()
gf=golden.flatten().float()
sf_f=sf_b.flatten()
# block 0: idx 0..14 (dim0..5=0, dim6=0..4, dim7=0..2)
print("block 0 (idx 0-14):")
for i in range(15):
    z=beta*sf_f[i].item()
    branch = "LIN" if z>threshold else "sig"
    ok = "OK" if rf[i].item()==gf[i].item() else "BAD"
    print(f"  idx={i} dim6={i//3} dim7={i%3} sf={sf_f[i].item():.4f} z={z:.4f} {branch} actual={rf[i].item()} golden={gf[i].item()} {ok}")
print("sf[0,0,0,0,0,0]=\n", sf[0,0,0,0,0,0])
```

## 验证信号

- L1_018 探针观测：block 0 pos 7（idx 7）actual=0=golden（正确），block 4 pos 7（idx 67）actual=FLT_MAX≠golden=0（错误），同一 sigmoid 分支输入值（来源平台：950；证据等级：tool_observed）。
- 4 次重跑 `run1/2/3 same as run0: True`，idx67 恒为 FLT_MAX——确定性逻辑 bug，非竞态（来源平台：950；证据等级：tool_observed）。
- Select 改用 `VSEL_TENSOR_TENSOR_MODE`（模式2）后重建重测：565/578 通过（499→565，+66）（来源平台：950；证据等级：tool_observed）。
## 预防

- arch35 上 `Select` 凡 `count` 可能 >64 的逐元素分支，**默认用 `VSEL_TENSOR_TENSOR_MODE`（模式2）**，不要被"arch35 仅支持 VSEL_CMPMASK_SPR"的旧注释误导——该注释描述的是早期约束，模式2 在当前 CANN 已可用。
- 排查"同值异位"的确定性精度漂移时，优先怀疑 mask 类 API 的位宽/迭代复用语义。

## 误诊

- 早期曾怀疑 `count_padded` 对齐导致 padding 位掩码泄漏污染输出，但 `CopyOut` 只拷 `count` 个元素，padding 不写出，排除该假设。
- 曾怀疑多核竞态，4 次重跑结果一致（确定性）排除竞态。

## 失效边界

- Ascend950PR/arch35 实测；模式2 需预留 8K UB 临时区（本 kernel 由 `kUbReserved` 保证，UB 顶端 8192B 未分配给 TBuf）。
- 非 arch35 平台（a2/a3）的 `Select` 三模式语义未验证，推断可迁移但需查对应平台 Select.md。

<!-- cannbot:related:start -->
## 相关

- [AscSelect](../../apis/simd_api/c_api/reg/compare_and_select/asc_select.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用》补充：arch35 Select 模式0 VSEL_CMPMASK_SPR 的 selMask 有效位限 256/sizeof(T)=64，多轮迭代复用同一 64bit 掩码，count>64 时元素 p 实际取 bit(p%64)，导致跨 64 元素块掩码错配，sigmoid 区元素被误判为线性分支返回 gradOutput。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/mask_reg_compute/select.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用》具体提供“arch35 Select 模式0 VSEL_CMPMASK_SPR 的 selMask 有效位限 256/sizeof(T)=64，多轮迭代复用同一 64bit 掩码，count>64 时元素 p 实际取 bit(p%64)，导致跨 64 元素块掩码错配，sigmoid 区元素被误判为线性分支返回 gradOutput。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [arch35 count Compare Select 异步VF 存读 RAW](arch35_count_compare_select_vf_raw.md)（`related`）：该卡展示同一 VF 中计数 Compare/Select 生产消费的 RAW 风险；即使分段长度正确，也需保证每段 mask 在覆写前被消费。
- [基于全局掩码复用的计算性能优化](../../guides/operator_practice/simd_operator_optimization/vector_compute/mask_reuse_optimization.md)（`related`）：该卡证明错误跨 repeat 复用 cmpmask 会污染后续元素，给出复用边界。
- [Duplicate 全量清零 padding 覆盖有效区 banned](duplicate_padding_banned.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [Select CMPMASK_SPR 模式致混合分支误选](select_cmpmask_spr.md)（`same_topic`）：目标卡用 `bit(p%64)` 精确表达每 64 元素复用，本卡用 116→3 的 MODE A/B 闭环验证同一 CMPMASK_SPR repeat 偏移缺陷。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](select_vsel_cmpmask_spr_count_64.md)（`same_topic`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用”定义：arch35 Select 模式0 VSEL_CMPMASK_SPR 的 selMask 有效位限 256/sizeof(T)=64，多轮迭代复用同一 64bit 掩码，count>64 时元素 p 实际取 bit(p%64)，导致跨 64 元素块掩码错配，sigmoid 区元素被误判为线性分支返回 gradOutput。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [Select cmpmask 不偏移致分支反转诊断](select_cmpmask.md)（`same_topic`）：候选直接描述 count>64 后复用首块 mask，本卡确认 VselImpl 只偏移 dst/src 而不偏移 sel。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](arch35_select_cmpmask_spr.md)（`same_topic`）：arch35 Select cmpmask SPR 跨调用泄漏致非确定失败 与《arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用》的实质衔接是：这些卡都围绕 arch35 VSEL_CMPMASK_SPR 的生成、复用、偏移或跨调用污染；Set/GetCmpMask 是直接控制和观察该 SPR 状态的接口。
- [arch35 Select 异步SIMT同步失效致分支错选](arch35_select_simt.md)（`same_topic`）：arch35 Select 异步SIMT同步失效致分支错选 与《arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [arch35 Select 超64 cmpmask 残缺判别](arch35_select_64_cmpmask.md)（`same_topic`）：该卡验证 64 个 b32 lane 是一次安全上限，给出将循环按 64 分段的修复边界，与 focal 的 over-64 失真完全互补。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](arch35_vsel_cmpmask_spr_mask.md)（`same_topic`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
<!-- cannbot:related:end -->
