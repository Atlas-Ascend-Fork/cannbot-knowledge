---
type: API
title: Utils APImin
description: 比较相同数据类型的两个数，返回最小值。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/algorithms/min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# min

比较相同数据类型的两个数，返回最小值。

函数原型：template <typename T, typename U>；__host__ __aicore__ inline constexpr auto min(const T& src0, const U& src1)

参数：T：输入数据src0的数据类型。当前支持的数据类型为<br><br>bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t。；U：输入数据src1的数据类型。当前支持的数据类型为<br><br>bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t。<br><br>预留类型，当前必须与T保持一致。；src0（输入）：源操作数。参与比较的输入。；src1（输入）：源操作数。参与比较的输入。

返回值：两个输入数据中的最小值。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：两个源操作数的数据类型必须相同。

<!-- cannbot:related:start -->
## 相关

- [__aicore__ 内 std::min/max 编译失败](../../../../runbooks/compilation/aicore_avoid_host_std_minmax.md)（`exemplifies`）：Runbook 复现了 bisheng `-xasc` 在 `__aicore__` 内无法解析 host `std::min` 两参数重载的精确诊断；Utils `min` 卡给出 device 可见的 `__host__ __aicore__` 二元比较接口及同类型实参合同，可用于区分“host std 重载不可见”和“设备侧 min 能力不存在”。
- [Utils APImax](max.md)（`related`）：Utils APImin 与《Utils APImax》的实质衔接是：Utils min 与 Utils max 是同一比较模板的成对边界：输入类型约束相同，只把返回选择从较小值切换为较大值；未将算法目录中的所有成员相连。
<!-- cannbot:related:end -->
