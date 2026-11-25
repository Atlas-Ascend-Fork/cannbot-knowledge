---
type: Optimization
title: "F21: int8 grouped GEMM 的 fixpipe 是 L0C 读侧固定地板——C 面格式/布局/NZ/直通全闭"
description: "int8 grouped GEMM 的 C 面（fixpipe）方向被多点探针逐条走死：格式/布局/NZ/步长/写策略均为噪声级；固定地板在 L0C 源侧读带宽，不在任何格式变换。dbL0C 与 L0C→UB 直通在 910B 的 API/架构层不存在，应停止排这类节点。"
tags:
  - task.debugging
  - topic.compute.neighborhood.convolution
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
status: draft
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToGM.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/appendix/cube_instruction_theoretical_perf_summary.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f21_fixpipe_l0c_read_floor_and_closed_c_plane_levers_910b2c.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---
> 证据：基线/变体与逐 case 数据见 [证据包 cases/f21_fixpipe_l0c_read_floor_and_closed_c_plane_levers_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f21_fixpipe_l0c_read_floor_and_closed_c_plane_levers_910b2c.json)。

> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F21: int8 grouped GEMM 的 fixpipe 是 L0C 读侧固定地板——C 面格式/布局/NZ/直通全闭

## 现象
本例算子（M=16384, K=4096, N=8192, E=8, M_g=2048）在 Ascend910B2C 上，
**多个变体与独立探针**把 C 面（fixpipe）方向的每一条路都走死。结论是墙钟由
`aic_mac`（接近峰值的地板）与 `aic_fixpipe` 相加支配。

### fixpipe 代价的定点分解（同一二进制、同仪器）
| C 面形态 | 观测 | 结论 |
|---|---|---|
| ND fp16 + DEQF16（基线） | 基准 | — |
| ND int32 无 quant（去转换，字节×2） | 固定项随字节增长 | 成本 = 存储项 + 每 drain 固定项 |
| NZ fp16（去 16x16→ND 转置） | 与基线噪声级差异 | 转置几乎不占成本 |
| 全部 drain 别名到同一 L2 热窗口 | 与基线噪声级差异 | L2 写分配 ≈ 0 |

⇒ 地板在 **L0C 源侧读带宽**（每个 drain 必读满 int32 累加器），不在格式变换。

### 被实测关闭的 C 面路线
| 路线 | 关闭理由 |
|---|---|
| C 面块连续（大块连续 drain） | 行距变化只值噪声级 |
| NZ 输出 | `aic_fixpipe_ratio` 不变；消费侧 32B 碎片反而抬高 `aiv_mte2` |
| 按 n-tile 拆子平面自定义行距 | 同 NZ；且 A 面板常驻被破坏，A 重读增加 |
| 减 drain 数（改 baseM/baseN） | drain 数 = M·N/(baseM·baseN)，L0C 容量把乘积锁死；改小 baseM 使 B 回填翻倍 |
| dbL0C 让 fixpipe 与 MAC 重叠 | 字段存在但在本几何的实例化路径不生效（见下） |
| L0C→UB 直通 | 架构不存在：`ifSupportL0CToUB=false`，dav-c220 仅有调试桩 |

## 根因
1. **L0C 单 tile**：int32 累加器容量固定，baseM·baseN 被锁死，drain 数固定；每次 drain 必须读满
 整个累加器，因此 `aic_fixpipe` 的不变项不可压。
2. **C 写字节受 L1 约束**：单个 C 平面需要的 singleCoreK 很大，导致 singleCoreM 受限、B 回填成为
 第二条等高的墙；双平面是 L1 预算下的折中。
3. **`l0_c_to_ub_rate` 是纸面字段**：platform_config 的通用每核速率，树内唯一消费者是 conv tiling
 代价模型，与是否真有该数据通路无关。**不要拿它当能力位。**

## Resolution
- **不要**再在 int8 GEMM 上排「C 面布局/格式/NZ/步长/描述符/写策略」类节点——收益为噪声级。
- **不要**再排 dbL0C / L0C→UB 节点（API/架构层不存在）。
- 判据：先按 L0C 容量算 drain 数与每次 drain 的固定读量，得到 fixpipe 的固定地板；叠加 MAC 地板
 与 A/B 回填地板，得到该几何的墙钟下界。目标低于它时直接判定不可达，而不是继续投变体。
- 真正有效的方向是**尾残差**：协作式尾部 drain、rb_ 提升、C 读描述符合并。

## 证据
（PipeUtilization + L2Cache + compare-batch）。定量结果未附公开原始记录，待复核；
本卡保留可复用的判据与架构级结论。

## 追加（架构级结论）
- **编译期 dbL0C 不存在**：`MatmulConfig` 没有 `dbL0C` 成员；真正的门是 `IsSupportMNL0DB()` →
 `scheduleType == OUTER_PRODUCT`，而 OUTER_PRODUCT 要求 `singleCoreK <= baseK`，本几何非法。
 同几何下 OUTER 比 INNER 快，但会把 B 重读翻倍，净负。
- **手写 cube + L0C 两半 ping-pong 在本机架构级不可用**：L1→L0A 必须走 DataCopy；手写 cube 需要
 超过本机可用 event id 数量的握手（本机只有 0..5，且 8 个 id 共用一个计数空间）→ 结构性死锁。
- **C 面行距的合法解耦点是 `orgKc`**，不是 `orgN`；用 `orgKc` 调整行距对 fixpipe 只有噪声级收益。
- **修正后的天花板**：即使 fixpipe 完美重叠，B 回填的 `aic_mte2` 仍是第二条等高的钉子，

**仍然有效且已证实的方向**：C 面在 GM 上按 expert 做 512B 基址错位，可把 fixpipe 写与 B 流的
L2 set 冲突打散（fixpipe 不变，但 epilogue 侧 `aiv_mte2` 下降），见 F 系列同族卡。

## 追加（ISA 级关闭）
- `get_buf/rls_buf` 在 dav-c220（910B）上不存在：内建在该 target feature 下被后端拒绝；
 AscendC 封装 `kernel_event.h` 的 buffer-id 路径整段限定在 `__NPU_ARCH__ == 3101 || 5102`。
- **坑**：`-fsyntax-only` 对 dav-c220-cube 退出码为 0，只有真实 codegen 才报错——只做语法检查的
 探针会给出假阳性。

## 验证状态

本卡为 `status: draft`：结论来自特定运行条件下的失败观测，不应外推为通用结论；定量结果与运行标识见证据包 `cases/f21_fixpipe_l0c_read_floor_and_closed_c_plane_levers_910b2c.json`。
