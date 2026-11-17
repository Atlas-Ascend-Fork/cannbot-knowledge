---
type: Runbook
title: "VectorPadding 是 DataBlock 内邻近值填充：不能做 16→32 零扩展"
description: "VectorPadding 在 310P + CANN 9.1.0 实测可用，语义是 DataBlock 内邻近值复制/镜像/偏移对称（与官方文档逐例吻合），不含 16→32 位零扩展形态——用它做零扩展用途必然无效果；16→32 扩展改用 Gather + host 交织表。曾据六组参数输出逐字节相同误判为'空操作'，干净语境复验不可复现，已作废。"
tags: [task.debugging, topic.programming_model.execution_unit.vector, topic.implementation.api_layer]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_padding/VectorPadding_ISASI.md
    role: constraint
created_at: "2026-10-28T09:52:17Z"
updated_at: "2026-11-09T03:19:04Z"
platforms: ["310p"]
---

# VectorPadding 是 DataBlock 内邻近值填充：不能做 16→32 零扩展

## 现象

bf16 输入要在向量管线里做位级 32 位扩展（16 位原始位型放到 f32 槽的低/高半字，另一半补零）。除 `Gather` 与 `Scatter` 之外试了 `VectorPadding`：探针把 `padMode ∈ {0,1,2}` × `padSide ∈ {lo,hi}` 六种组合各跑一遍后，host 位级比对得到的 dump **六组逐字节相同**、且与任何零扩展位型都对不上——当时据此判定该 API 为"空操作"。

**该判定后被证伪**（2026-11-05 复验）：带 8 区段哨兵 + MTE2_V 同步的干净探针重跑，六种组合输出**两两不同**，且逐例吻合官方文档语义（见根因）。原"六组相同"的观察疑为原探针 dump/区段管线自身缺陷，在干净语境不可复现。本卡结论修正为：**API 可用，但语义不含零扩展，零扩展用途必然无效果**。场景：kernel 直调、Ascend310P3（dav-m200/DAV_2002）、CANN 9.1.0。

## 适用场景

- 工程形态：kernel 直调；需要在 UB 内做 16→32 位零扩展/交织的 dtype 转换路径。
- API 路径：`VectorPadding`（LocalTensor 版），与 `Gather`/`Scatter` 互为候选。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.1.0。
- 适用粒度：`platform_wide`——限"零扩展用途判定"（语义层结论）；API 可用性与逐 padMode 语义仅在本平台实测。
- 路线优先级：零扩展用途 `banned`（语义不匹配，换参数也不会出现零扩展位型）；替代路线 `recommended_fastpath`（`Gather` + host 交织表）。
- 明确不适用 / 未验证场景：count 与 mask 连续两种重载上板确认真实写入，mask[] 逐 bit 重载经源码核对转发到同一内建（未单独上板）；除零扩展外的其他用途（按文档语义做边界填充等）未在本轨迹使用；其他平台未实测。

## 根因

`VectorPadding` 的文档语义是**按 DataBlock 做邻近值/对称填充**，从来不含"16→32 位零扩展"：

- `padMode=0, padSide=lo`：每 16 元素块复制**块首**值（`aaa|abc` 型）；
- `padMode=0, padSide=hi`：每 16 元素块复制**块尾**值；
- `padMode=1`：块内**镜像**（`cba|abc` 型）；
- `padMode=2`：偏移一位的对称填充，越界处填 0。

复验证据（310P 上板 + CANN 源码）：

1. CANN 9.1.0 实现真实调用 `vpadding` 内建，非空壳：`impl/basic_api/dav_m200/kernel_operator_vec_vpadding_impl.h:36,40`，内建声明在 `cce_aicore_intrinsics.h:2715`；count / mask 连续 / mask[] 逐 bit 三个重载都转发到该内建。
2. 上板六种组合输出两两不同，且与上述文档语义逐例吻合（语义对表探针 `vp_sem.py`）；无 V_MTE3 握手的 dump 也正确。

因此"想做零扩展却得不到零扩展"是**用法与语义不匹配**：换任何 padMode/padSide 组合都不会产生零扩展位型，这一点看文档语义即可预判，与平台支持与否无关。

判别手段（可复用，含本次误判的教训）：

1. 让每个参数组合写到**不同**的目标地址，避免"都写同一块"掩盖问题；
2. 比对时用位级直方图（`==src` / `==0` / `==0xFFFF` 的比例）而不是肉眼；
3. 若所有组合的比例完全相同，**先怀疑"没写"，再用带哨兵区段与同步的干净探针复现**——干净语境复现之前不得下"API 空操作"结论（本卡第一次就是在这一步误判）；
4. 判定 API 行为前先读官方文档语义：用途不在语义内即可直接排除，不必上板试探。

## 设计决策

- 放弃 `VectorPadding`（语义不匹配），改用 `Gather` + host 预生成交织表：`tab3[i] = (i 为奇数) ? 32 + i - 1 : 0`（字节偏移），原始 16 位数据放在缓冲的 slot 16 之后，偶槽指向零源、奇槽指向真实数据——一次 `Gather(dst16, raw, tab3, 0, 2*cnt)` 完成"零 + 数据"的交织，等价于零扩展。
- 另一候选是 `Scatter`（把数据散射到奇槽），实测可用但更慢（性能结论仅作为设计取舍的定性依据，本轨迹未给成对计时）。
- 选择 Gather 交织表的副作用：`rawBuf/raw2Buf` 各要 16 个 int16 零源槽 + Q 个数据元素（共 `(Q+16)*2` 字节；如需对齐余量另行标注），且该零源必须在每量子内幂等重置（V 管内序），不能占用"首量子免等"的事件。

## 系统信息

- 工具链：CANN 9.1.0，Ascend310P3（dav-m200）；kernel 直调 + torch 扩展，`BUILD_OK: build/lib<generic>_ops.so`。
- 涉及文件：`kernel/<generic>.cpp`（bf16 入口）；host 侧位级比对探针（临时）；复验探针（哨兵区段 + MTE2_V 同步 + 语义对表）。

## 完整代码

探针（host 侧按位比对，六组参数写到六个不同区段）：

```python
PC = 256
src = dy.flatten()[:PC].view(torch.int16).numpy().view(np.uint16)
raw = out.cpu().flatten()[:6 * 2 * PC].view(torch.int16).numpy().view(np.uint16)
for k in range(6):
    w = raw[k * 2 * PC:(k + 1) * PC].copy().view(np.uint32)
    lo = (w & 0xFFFF).astype(np.uint32)
    hi = (w >> 16).astype(np.uint32)
    pm, ps = k % 3, "hi" if k >= 3 else "lo"
    m0 = (hi == src.astype(np.uint32)).mean()
    m1 = (hi == 0).mean()
    m2 = (hi == np.uint32(0xFFFF)).mean()
    print(f"padMode={pm} padSide={ps}: hi==src {m0:.2f} hi==0 {m1:.2f} hi==FFFF {m2:.2f} | "
          f"lo==src {(lo == src.astype(np.uint32)).mean():.2f} lo==0 {(lo==0).mean():.2f} "
          f"lo==FFFF {(lo==np.uint32(0xFFFF)).mean():.2f}")
    print("   sample:", [hex(x) for x in w[:4]], " src:", [hex(x) for x in src[:4]])
```

替代实现（Gather + host 交织表，定版形态的关键结果）：

```cpp
            LocalTensor<int16_t> d16 = dF.ReinterpretCast<int16_t>();
            LocalTensor<int16_t> y16v = yF.ReinterpretCast<int16_t>();
            Gather<int16_t>(d16, rawBuf.Get<int16_t>(), tab3, 0, 2 * cnt);
            Gather<int16_t>(y16v, raw2Buf.Get<int16_t>(), tab3, 0, 2 * cnt);
```

（`tab3` 为 host 预生成常量交织表；`rawBuf` 前 16 个 int16 为零源槽，真实数据从 slot 16 起装载。该段所在的转换分支按 dtype 分流，f16 走 `Cast<half,float>`、bf16 走本交织路径。）

## 预防

- 用途不在文档语义内的 API，直接排除，不进入生产路径；确需试探时先写独立探针：每个参数组合写到**不同**目标地址，用位级直方图判决。
- 位级转换类 API 的验收必须含"输出既不等于源、也不等于期望模式"的判定分支，才能区分"写错"与"没写"。
- "所有参数组合输出相同"只证明与参数无关，不证明"没写"：下"空操作/未实现"结论前必须用带哨兵区段与同步的干净探针复现（本卡第一次探针即在此翻车，复验推翻）。
- 16→32 位扩展优先用 `Gather` + host 交织表这条已验证形态，并记得零源槽每量子幂等重置。

## 验证信号

- 复验（2026-11-05，310P chip 2）：六种 `padMode×padSide` 组合输出**两两不同**，逐例吻合文档语义（`aaa|abc`/块尾复制/`cba|abc` 镜像/偏移对称+越界 0）；count 与连续 mask 重载真实写入（mask[] 逐 bit 重载未单独上板，见适用场景）；无握手 dump 亦正确（来源平台：310P；证据等级：tool_observed，日志存复验档案）。
- CANN 9.1.0 源码：`kernel_operator_vec_vpadding_impl.h:36,40`（dav_m200）真实调用 `vpadding` 内建（来源平台：CANN 9.1.0 源码；证据等级：artifact_verified）。
- 原探针“六组逐字节相同”（2026-10-28）：已被复验作废，仅作为误判过程记录保留（来源平台：310P；证据等级：tool_observed）。
- 改用 Gather 交织表后：14 个用例全部 PASS，含 bf16/fp16/f32、H128、H16、变长、dead row、seqCap 路径与奇数总行；bf16 误差为 7.097e-04 / 7.679e-04 / 4.413e-04 / 5.552e-04 / 7.167e-04 / 3.774e-03 / 7.606e-04 / 1.724e-03 / 2.059e-05（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- "零扩展用途不成立"是语义层结论（文档语义 + 本平台实测双重支撑）；其他平台/CANN 版本同样可直接按文档语义排除，无需实测。
- API 逐 padMode 语义与"可用"结论仅针对 Ascend310P3（dav-m200）+ CANN 9.1.0 实测；文档产品支持表对 310P 的"AI Core 支持 / Vector Core 不支持"分支标注与实测形态的对应关系未在机制层裁定（实测内核为 DAV_2002 向量形态且实现文件就在 dav_m200 目录）——不影响本卡用途级结论。
- 即使某平台上 `VectorPadding` 可用，也要先做位级直方图确认语义（padMode/padSide 的组合含义在不同版本可能不同）。
- Gather 交织表要求：零源槽每量子幂等重置、raw 数据装载与 Gather 之间有 MTE2→V 事件（本例由既有 evA 对保证）；否则会读到上一量子的残留。

## 坏实践

- 六个参数组合都写同一目标地址再比对：得到"六组一致"会误判为"参数无影响"，实际可能是"根本没写"——必须先分开目标地址。
- 用肉眼/单值判断扩展是否正确：位级转换要统计比例。
- 从"各组输出相同"直接跳到"API 空操作/未实现"：必须先用带哨兵区段与同步的干净探针复现，并对照文档语义（本卡曾在此误判，复验才纠正）。
- 用途不在文档语义内的 API 仍上板逐一试探：先读语义可直接排除。

## 误诊

- 误诊一（agent_reported，已由复验纠正）：最初以为"六组输出相同"是 padMode/padSide 对零扩展不起作用（选错参数），打算换参数；改成"每组写不同地址"后六组仍相同，又据"无写入证据"判定 API 为空操作——该判定在干净语境（哨兵区段 + 同步）不可复现，属探针缺陷导致的误判。最终结论：API 可用、语义为块内填充，零扩展用途语义层不成立。
