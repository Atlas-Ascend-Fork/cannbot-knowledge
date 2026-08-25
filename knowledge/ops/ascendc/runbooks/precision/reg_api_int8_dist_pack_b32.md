---
type: "Runbook"
title: "Reg API int8 DIST_PACK_B32 交错零"
description: "Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。"
tags: ["task.debugging", "topic.compute.quantization", "topic.implementation.api_layer.basic_api", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-18T15:55:13Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Reg API int8 DIST_PACK_B32 交错零

## 现象

在 Ascend950（dav-3510）上用 ops-direct-invoke-flash 从骨架优化 `AddRmsNormDynamicQuant`（Add + RmsNorm + AbsMax + 动态量化融合）算子。首版把 int8 量化写进一个 `__simd_vf__` Reg API 函数：对 fp32 buffer 做 `Muls(invScale)` → `Reg::Cast<half,float>` → `Reg::Cast<int8_t,half>` → `Reg::StoreAlign<int8_t, Reg::StoreDist::DIST_PACK_B32>`，mask 用 `Reg::UpdateMask<float>(rem)`（float 元素粒度）。kernel 编译通过、xOut/scaleOut 全对，但 int8 输出 `y` 严重错位：每隔一个有效值插一个 0——`[value, 0, value, 0, ...]`，像是每个 int8 元素被按 4 字节（float 宽度）间距落盘，而不是 1 字节紧挨。

## 适用场景

- **工程形态**：ops-direct-invoke-flash Kernel 直调核函数构建（`op_kernel/*.cpp` 内 `__simd_vf__` Reg API + `asc_vf_call` 调用）。
- **API 路径**：`AscendC::Reg::StoreAlign<int8_t, AscendC::Reg::StoreDist::DIST_PACK_B32>` + `AscendC::Reg::UpdateMask<float>` + `AscendC::Reg::Cast<int8_t, half, ...>`；对照路线为经典 `AscendC::Muls/Maxs/Mins` + `AscendC::Cast<half>` + `AscendC::Cast<int8_t>`。
- **验证过的平台与版本**：Ascend950（dav-3510），CANN 版本未在 trace 中显式记录（评测在 device 0 上板跑通）。
- **适用粒度**：`operator_family`——任何在 Ascend950 Reg API 里做 fp32→int8 量化落盘的算子。
- **路线优先级**：`recommended_fastpath`——经典 AscendC Cast 链（verbatim 修复代码未从 trace 恢复）。
- **不适用或未验证场景**：a2/a3 平台未验证，推断可迁移；非 Ascend950 Reg API 编程模型不适用。

## 判别方法

### 触发（trigger）

用 Reg API 链（`Reg::Cast<int8_t, half>` → `Reg::StoreAlign<int8_t, DIST_PACK_B32>`）做 fp32→int8 量化落盘，且整条链路的 mask 与寄存器元素粒度挂在 float 上（`UpdateMask<float>(rem)`、`RegTensor<float>` 输入）。kernel 编译通过、fp32/half 中间结果与 scaleOut 全对，唯独 int8 输出 `y` 大面积错位：mismatch 469/512（91.6%）、max_diff=214，`y[0]` 呈 `[-13, 0, 17, 0, 14, 0, -11, 0, ...]` 的交错零形态。

### 探针（probe）

用小 shape（M=8 N=64）fp16 随机输入跑 debug 脚本，单独打印 int8 输出 `y[0]` 与 torch 参考实现逐元素对照，并统计 mismatch 数与 max_diff。重点看 `y[0]` 是否呈 `[value, 0, value, 0, ...]` 的交错零（每隔一字节插零），以及 mismatch 比例是否远高于舍入边界（>50% 而非个位数）。xOut/scaleOut 全对、仅 int8 `y` 错位即可锁定到 int8 落盘环节。

### 观测（observation）

- 修复前 debug 脚本 stdout：`y[0]: [-13, 0, 17, 0, 14, 0, -11, 0, -24, 0, -2, 0, 75, 0, -7, 0, 32, 0, 6, 0]`，参考 `[-13, 17, 14, -11, -24, -2, 75, -7, 32, 6, ...]`，`y mismatch: 469/512 (91.6%)`，`y max_diff: 214`。每隔一个有效值插一个 0。
- 修复后（改走经典 AscendC Cast 链）debug 脚本 stdout：`y mismatch: 3/512 (0.6%)`，`y max_diff: 1`，`y[0]: [-13, 17, 14, -11, -24, -2, 75, -7, 32, 6, -7, -24, 19, 30, 18, 3, 4, -78, -2, 18]`，与参考逐元素一致；残留 3/512 mismatch、max_diff=1 属 int8 舍入边界差。

### 判读（interpretation）

`StoreAlign<int8_t, DIST_PACK_B32>` 的 pack 分布与整条链路的 mask/寄存器元素粒度（float，4 字节）不匹配：寄存器里 int8 数据没有按 1 字节紧挨 pack 到目标 UB，而是每个 int8 结果值按 float 元素间距（4 字节）写入，相邻 3 字节被零填充，落盘后在按 int8 视角读取时即 `[value, 0, value, 0, ...]` 的交错零。即 **int8 store 的 pack 分布与 mask/寄存器链的 float 元素粒度不匹配**是交错零的根因。注意：trace 未做对照实验隔离"改 mask 为 `UpdateMask<int8_t>`"与"换经典 Cast"两个变量，agent 直接整体替换为经典 AscendC Cast 链后精度恢复，因此 mask 粒度 vs pack 分布谁是主因未单独验证；此处判读为 agent 的根因分析，非单独探针验证的结论。

## 验证信号

- 修复前 debug stdout：`y[0]: [-13,0,17,0,14,0,-11,0,-24,0,-2,0,75,0,-7,0,32,0,6,0]`，参考 `[-13,17,14,-11,-24,-2,75,-7,32,6,...]`，`y mismatch 469/512 (91.6%)`，`max_diff=214`，呈交错零（来源平台:950；证据等级:tool_observed）
- 修复后 debug stdout：`y mismatch 3/512 (0.6%)`，`max_diff=1`，`y[0]` 与参考逐元素一致（来源平台:950；证据等级:tool_observed）
- kernel 编译通过、xOut/scaleOut 全对，仅 int8 输出 `y` 错位（来源平台:950；证据等级:tool_observed）

<!-- cannbot:related:start -->
## 相关

- [AscInt82int16](../../apis/simd_api/c_api/reg/data_type_convert/asc_int82int16.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《AscInt82int16》说明将int8类型数据转换为int16类型。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [AscStore](../../apis/simd_api/c_api/reg/reg_store/asc_store.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《AscStore》说明从矢量数据寄存器搬出数据到UB，不区分是否对齐，对齐场景推荐使用asc_storealign接口。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [AscStorealign](../../apis/simd_api/c_api/reg/reg_store/asc_storealign.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《AscStorealign》说明将矢量数据寄存器或掩码寄存器中的数据以32B对齐方式搬出到UB，支持连续、偏移、非连续等多种搬出模式。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [AscUpdateMask](../../apis/simd_api/c_api/reg/reg_data_types/asc_update_mask.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《AscUpdateMask》说明根据元素个数生成mask并自动扣减当前向量处理单元元素数，支持b8、b16、b32位宽模式。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [Pack](../../apis/simd_api/basic_api/reg_vector_compute/data_compression/pack.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《Pack》说明将源操作数元素的低位部分写入目的寄存器的低半部分或高半部分，实现数据位宽压缩。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [Store](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《Store》说明从RegTensor搬出至非32字节对齐的UB地址，支持搬出VL或指定count个数据。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [类型转换](../../apis/simd_api/c_api/reg/data_type_convert/data_type_convert.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《类型转换》说明寄存器侧类型转换类接口汇总，覆盖bfloat16、half、float、int等数据类型间的相互转换及取整操作。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [LoadDist 错用 DIST_NORM_B32 导致编译失败](../compilation/reg_load_and_store_use_distinct_dist_enums.md)（`related`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《LoadDist 错用 DIST_NORM_B32 导致编译失败》说明Reg LoadAlign 误用 StoreDist 风格枚举 DIST_NORM_B32 时编译失败；fp32 常规加载应使用 LoadDist::DIST_NORM。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [fp32 UB 非 VL 拷贝须用带掩码 Reg](non_vl_fp32_ub_copy_needs_masked_reg_load_store.md)（`related`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《fp32 UB 非 VL 拷贝须用带掩码 Reg》说明fp32 UB 局部 DataCopy 在非 vector-length 元素数上产生轴相关错误；使用 UpdateMask 的 Reg load/store 复制尾块。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换](b16_reg_cast_layout_should_convert_at_localtensor_boundary.md)（`same_topic`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换》说明dav-3510/CANN 9.0.1 的已测 DIST_UNPACK_B16→Reg::Cast→UB 中间组合产生系统性偏差；classic AscendC::Cast 边界转换建立了正确性基线，不代表所有 Reg Cast 组合失效。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
<!-- cannbot:related:end -->
