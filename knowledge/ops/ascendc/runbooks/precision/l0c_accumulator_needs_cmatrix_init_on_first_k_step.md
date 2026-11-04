---
type: Runbook
title: "S 累加跨 tile 残留 - 每 tile 清零 L0C"
description: "Cube 累加器在 fixpipe 读出后仍保留旧值；靠“读出清零”做跨 kt 累加会把上一 tile 结果抄进新结果，改为每个 kt 首个 Mmad 都清零起步。"
tags: [task.debugging, task.migration, topic.precision, topic.programming_model]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/Mmad.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/include/basic_api/kernel_struct_mm.h
    role: header
created_at: "2026-10-28T09:51:47Z"
updated_at: "2026-10-28T09:51:47Z"
platforms: ["310p"]
---

# S 累加跨 tile 残留 - 每 tile 清零 L0C

## 现象

把一个 910B 上跑通的 Cube/Vector 融合 attention 类算子（Q@Kᵀ 得分数矩阵，门控激活后与 V 做第二个 Mmad，L0C 上跨 k 方向分块累加）迁到 Ascend310P3 后，出现一种很有辨识度的误差形状：

- **序列长度只占一个 64 列 tile 的用例全对**，一旦 key 方向跨到第 2、第 3 个 tile（`t>=1`），误差就从噪声级跳到 1e-1 量级，且**误差随 tile 序单调变大**；
- 按行看，**第一个 tile 覆盖的行（0..63）逐位正确**，从第 64 行起整块偏离；
- 失败用例的实测/参考误差对比：实测最大误差 0.1158，而参考实现与高精度金标的误差只有 5e-4 量级，门限是 1e-3 —— 不是精度退化，是内容错。

关键判别信号（无需上板再猜）：用 numpy 写两份模拟，一份假设"L0C 读出会清零"，一份假设"读出不影响 L0C"：

```
ours vs 正确模拟   = 0.115777
ours vs 累积bug模拟 = 0.000969   <-- 与实测逐位同级
```

第二行落在 f16 模拟噪声里，等于把"读出非破坏性"这件事钉死。

## 适用场景

- **工程形态**：kernel 直调（raw launch），Cube 手写数据流（Nd2Nz 搬入 L1、LoadData2D/LoadData3D 进 L0A/L0B、Mmad 到 L0C、fixpipe/DataCopy 从 L0C 读出）。
- **API 路径**：`Mmad(dstL0C, a, b, MatmulParams)` 的 `cmatrixInitVal` / `cmatrixSource` 语义（CANN 9.1 `kernel_struct_mm.h`）；`DataCopy(L0C → UB)` 读出。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.1.0。
- **适用粒度**：`operator_family` —— 凡是"L0C 上做跨 kt/跨分块累加，并在每个 kt 内先读出再复用同一个 L0C 缓冲"的手写 Cube 算子都适用；不限于某个具体算子。
- **路线优先级**：`recommended_fastpath` —— 每个分块都清零起步，代价只是一次 C 初始化，不赌硬件读出行为。
- **不适用/未验证**：未在 910B(DAV_2201) 与其它代际上验证"读出是否破坏性"；如果某代际确实破坏性清零，本配方仍然正确（只是多一次清零），但"必须清零"的强制性未在该平台验证。

## 根因

`cmatrixInitVal` 有两位语义：1 = 本次 Mmad 先把 C 清零再算；0 = 在 C 的当前值上累加。旧代码写的是

```cpp
mpS.cmatrixInitVal = (kt == 0 && dh == 0);
```

注释里给出的理由是一条早期单 tile 实验的判决："L0C 读出是破坏性的（读后清零）"，因此认为 `kt>0` 时 L0C 已被清空，用累加模式等于从零开始。

这条判决的适用范围被误用了：早期实验的序列长度只有一个 tile，**`kt` 永远等于 0，从未走过 `kt>0` 分支**。在 310P 上实际行为是：

- fixpipe 读出 L0C **不破坏**内容；
- 于是 `kt=1` 的 Mmad 以 `cmatrixInitVal=0` 在"上一 tile 的 S 残值"上累加，读出得到 `S(kt=0)+S(kt=1)`；`kt=2` 再叠一层。

由此得到的所有可观测特征都与现象段一致：tile 序越大累的残值越多（误差随 t 增长）、第一个 tile 天然干净（行 0..63 全对）、序列长度单 tile 的用例永远不触发。

修复只要一行：**每个 kt 的第一个 dh 分块都清零起步**，`dh>0` 仍累加 D 半片：

```cpp
mpS.cmatrixInitVal = (dh == 0);
```

这样修复与"读出是否破坏性"完全解耦——两种硬件语义下都正确。顺带核对第二个 Mmad 链（PV 累加）的写法是 `mpP.cmatrixInitVal = (kt == 0)`，语义本来就对（每个 unit 的 kt 循环重新从 0 开始），不需要改。

## 设计决策

- **放弃"记住每个 L0C 缓冲的残留状态"**：另一种思路是维护"这个 L0C 上次写到哪、要不要清"，但 kt/dh/unit 三层循环下状态机极易漏；每 kt 清零的代价是一次 C 初始化，换来与硬件语义无关的正确性。
- **不采用"读出后显式清 L0C"**：多一条指令、多一个同步点，且同样依赖对读出语义的假设。
- 该修复属 `recommended_fastpath`：一次清零，无额外搬运。

## 系统信息

- 目标平台 Ascend310P3（DAV_2002 / m200），CANN 9.1.0，`__NPU_ARCH__ 2002`。
- 文件布局：单 kernel 源文件（Cube/Vector 同一 kernel 内），host 侧为 torch C++ 扩展 + `aclrtlaunch_*` 直调。
- 关键缓冲：L0A（Q 两个半片）、L0B（K/V 分块）、L0C（S 一个 + O 两个），UB 侧分数矩阵与输出暂存。

## 完整代码

以下是修复点的函数级 before/after（语句原样摘自开发轨迹；注释中只裁剪了源算子专有的探针编号与具体形状，语句未改）。

改前：

```cpp
                PipeBarrier<PIPE_ALL>();
                // CANN 9.1 头文件(kernel_struct_mm.h): cmatrixInitVal
                // 1=C 清零起步, 0=累加 C 现值。kt0dh0 清零; kt>0dh0 为累加,
                // 但 l0cS 读出是破坏性的（读后清零, 早期单 tile 探针判决）→ 累加到零=
                // 干净; dh>0 累加 D 半片和。
                mpS.cmatrixInitVal = (kt == 0 && dh == 0);
                Mmad(l0cS, (dh == 0) ? l0aQ0 : l0aQ1, l0b, mpS);
```

改后：

```cpp
                PipeBarrier<PIPE_ALL>();
                // CANN 9.1 头文件(kernel_struct_mm.h): cmatrixInitVal
                // 1=C 清零起步, 0=累加 C 现值。早期单 tile 实验曾判"l0cS 读出
                // 破坏性清零"故 kt>0dh0 用累加——但那是单 tile 时代, 从未覆盖
                // kt>0。多 tile 真实用例对拍铁证: 310P 上 fixpipe 读出非破坏性,
                // kt>0 残留 S_{kt-1} 被累进新 S（对角 tile 读出 ΣS）。
                // 修复: 每 kt 的 dh=0 一律清零起步, 不赌读出行为; dh>0 仍
                // 累加 D 半片和。O 路径 (kt==0 清零跨 kt 累加) 语义本就正确。
                mpS.cmatrixInitVal = (dh == 0);
                Mmad(l0cS, (dh == 0) ? l0aQ0 : l0aQ1, l0b, mpS);
```

对照（另一条链，无需修改）：

```cpp
                mpP.cmatrixInitVal = (kt == 0);   // kt=0 清零, kt>0 累加跨 kt
                Mmad((dv == 0) ? l0cO0 : l0cO1, l0aW, l0b, mpP);
```

## 预防

- 读 `cmatrixInitVal` 的既有注释时，先问"这条判决是在什么循环范围下得出的"：单 tile 实验只能证明 `kt==0` 分支。
- 新写累加链时，把清零条件写成**与本层循环对齐的最小周期**（例：`dh == 0`），不要依赖任何跨层残留假设。
- 迁移时把"读出是否破坏性"当成**未验证前提**列进检查表，而不是从源算子注释里继承。

## 验证信号

来源：本会话内的一次开发轨迹（单条轨迹，单次上板验证；证据等级均为 `tool_observed`）。

- 对拍判决：实测输出与"累积 bug 模拟"的最大误差 0.000969（f16 模拟噪声级），与"正确模拟"的最大误差 0.115777，且后者与修复前实测误差 0.1158 逐位吻合 —— 证明 kt>0 的 L0C 残值被累入。（来源平台：310P；证据等级：tool_observed）
- 修复后同一批真实用例（多 tile 形状）误差回到门限内；随后全量 50 例精度 50/50 PASS、探针（subnormal/f16/f32）全过。（来源平台：310P；证据等级：tool_observed）
- 优化轮次重编后再复验，仍是 50/50 PASS（说明修复没有被后续性能改动破坏）。（来源平台：310P；证据等级：tool_observed）

## 失效边界

- **失效于"跨 kt 有意累加"的场景**：如果某条链确实要在多个 kt 之间累加同一个 L0C（例如把 k 方向完全摊平成一个长累加），就不能每 kt 清零；此时必须显式跟踪残留。
- **未验证平台**：910B(DAV_2201)、A2/A3、950 均未验证；本轨迹只在 310P 上观测到"非破坏性"。若某平台确为破坏性清零，本配方仍安全但失去必要性。
- **未决项（优先）**：为什么同一个 kernel 里 S 链读出是分形 D 布局、O 链读出是行主序（两条 Mmad 链的分形类型差异），本轨迹只做到"按布局解码后逐位对上"，没有做到机制级解释；下一个 agent 若要复用读出解码逻辑，需先复现该差异并追到 fixpipe/Mmad 的输出布局参数层。
- 不适用于用高阶 Matmul API 自行管理 L0C 生命周期的实现（那些由 API 内部处置 init 标志）。

## 坏实践

- **把单点实验的结论当全局律**：单 tile 实验推出"读出清零"，再被注释抄进多 tile 代码，错误被"注释权威"保护了很久。
- **用累加模式省一次清零**：省下的是一次 C 初始化，付出的是一整条链的内容错，且错误形状（行 0-63 对、行 64+ 全错）会被误读成"搬运/存储问题"。

## 误诊

- **误诊 1（agent_reported）**：曾把"行 64+ 全坏"归因到多核互踩 / 逐行存储丢失；实际是 S 值本身已经错了，存储只是如实搬运了错值。判别方法：把 L0C 读出内容直接 dump 并按布局解码后与高精度模拟对比，若"计算侧就已经错"，就不必再查存储。
- **误诊 2（agent_reported）**：早期把误差随 t 增长解释成"f16 量化累积"，因此去调容差/换 accumulate 精度，方向错误；真正的判据是"t=0 的 tile 完美、t>0 整块偏"。
