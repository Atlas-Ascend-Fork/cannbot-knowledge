---
type: API
title: Utils APImax
description: 比较相同数据类型的两个数，返回最大值。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/algorithms/max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# max

比较相同数据类型的两个数，返回最大值。

函数原型：template <typename T, typename U>；__host__ __aicore__ inline constexpr auto max(const T& src0, const U& src1)

参数：T：输入数据src0的数据类型。当前支持的数据类型为bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t。；U：输入数据src1的数据类型。当前支持的数据类型为bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t。<br><br>预留类型，当前必须与T保持一致。；src0（输入）：源操作数。参与比较的输入。；src1（输入）：源操作数。参与比较的输入。

返回值：两个输入数据中的最大值。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：两个源操作数的数据类型必须相同。

<!-- cannbot:related:start -->
## 相关

- [__aicore__ 内 std::min/max 编译失败](../../../../runbooks/compilation/aicore_avoid_host_std_minmax.md)（`exemplifies`）：Runbook 记录 `__aicore__` 中 `std::max(32KB,D*sizeof(float))` 只暴露 initializer_list 候选而编译失败；Utils `max` 卡定义了 device 可调用的二元最大值接口和同类型限制，直接补足该故障的受支持接口边界。
- [Utils APImin](min.md)（`related`）：Utils APImin 与《Utils APImax》的实质衔接是：Utils min 与 Utils max 是同一比较模板的成对边界：输入类型约束相同，只把返回选择从较小值切换为较大值；未将算法目录中的所有成员相连。
<!-- cannbot:related:end -->
