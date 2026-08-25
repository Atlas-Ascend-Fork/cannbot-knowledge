---
type: API
title: Kernel Tiling
description: Kernel Tiling 宏与接口集，包含 GET_TILING_DATA、TILING_KEY_IS、REGISTER_TILING_FOR_TILINGKEY 等 Tiling 数据获取与注册接口。
tags: [task.lookup, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/Kernel-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Kernel Tiling

-   **GET_TILING_DATA**

-   **GET_TILING_DATA_WITH_STRUCT**

-   **GET_TILING_DATA_MEMBER**

-   **GET_TILING_DATA_PTR_WITH_STRUCT**

-   **COPY_TILING_WITH_STRUCT**

-   **COPY_TILING_WITH_ARRAY**

-   **TILING_KEY_IS**

-   **TILING_KEY_LIST**

-   **REGISTER_TILING_DEFAULT**

-   **REGISTER_TILING_FOR_TILINGKEY**

-   **REGISTER_NONE_TILING**

-   **设置Kernel类型**

<!-- cannbot:related:start -->
## 相关

- [ACLNN 507035 — stub kernel tiling 数据未初始化](../../../../runbooks/compilation/aclnn_507035_stub_tilingfunc_must_init_tiling_buffer.md)（`exemplifies`）：正式 tiling API 说明 GET_TILING 前 Host 必须写入有效数据。
- [GET_TILING_DATA 首参传类型名致变量遮蔽类型](../../../../runbooks/compilation/get_tiling_data.md)（`exemplifies`）：GET_TILING_DATA 首参传类型名致变量遮蔽类型说明GET_TILING_DATA(<类型名>, tiling) 把类型名作宏首参，宏展开声明同名变量遮蔽类型，致 InitTilingData<HistogramTilingData> 模板实参 T 无法匹配 InitTilingData(const __gm__ uint8_t*, T*) 签名，报 candidate template ignored: invalid explicitly-specified argument for template parameter 'T'；判别依据为编译错 expanded from macro 行 &tiling_data 取首参地址，证明首参为变量名。
- [GM_ADDR 标量不可解引用为 tiling 结构体指针](../../../../runbooks/compilation/gm_addr_tiling.md)（`exemplifies`）：GM_ADDR 标量不可解引用为 tiling 结构体指针 与《Kernel Tiling》的实质衔接是：GM_ADDR 在该入口是 __gm__ uint8_t 标量而非结构体指针；typed __gm__ tiling 指针、Kernel Tiling/GET_TILING_DATA 和地址空间案例给出正确入口与强转边界。
- [Host 缺 SetDataSize 致 TilingData 截断](../../../../runbooks/precision/host_setdatasize_tilingdata.md)（`exemplifies`）：Host 缺 SetDataSize 致 TilingData 截断说明ACLNN 算子 op_host TilingFunc 填完自定义 TilingData 字段后未调用 rawTilingData->SetDataSize(sizeof(<TilingData>))，框架按默认小 data_size 从 GM 搬运 tiling，只传结构体头部，kernel 侧 GET_TILING_DATA 解析出 perCoreCount 等关键字段为 0/垃圾，DMA 循环零次执行，输出保持框架初始化状态、ST 全红。
- [TilingData 须 host 与 kernel 各定义一份](../../../../runbooks/compilation/tilingdata_host_kernel.md)（`exemplifies`）：TilingData 须 host 与 kernel 各定义一份说明新增 TilingData struct 只写进 kernel 侧 struct.h 时 host 编译报 does not name a type；须在 host 可见头内同 namespace 重新定义一份，字段与 kernel 侧逐字一致，仿 SIMT 双定义模式。
- [rebase 引入新 kernel 文件旧 tiling 类型致编译失败](../../../../runbooks/compilation/rebase_kernel_tiling.md)（`exemplifies`）：rebase 引入新 kernel 文件旧 tiling 类型致编译失败说明Conv3DBackpropInputV2/Conv3DTransposeV2/ExtendConvTranspose arch35 tiling data 框架迁移分支 rebase 上游后，新增 kernel 文件 conv3d_dx_small_kernel.h 仍引用已删除的旧 tiling 类型 conv_bp_v2_kernel::TConv3DInputV2Tiling 和旧嵌套访问 conv3DDxTiling，入口宏传新类型引用而 SmallKernel::Init 收旧类型指针，类型不匹配致编译失败；grep 可定位未适配文件。
- [手动 tiling 头遮蔽自动生成类致 no member 判别](../../../../runbooks/compilation/tiling_no_member.md)（`exemplifies`）：手动 tiling 头遮蔽自动生成类致 no member 判别说明JOIN_OP_DEF True 工程里，op_host 用 BEGIN_TILING_DATA_DEF 定义 TilingData 后构建系统会自动生成 kernel 侧同名类并经 kernel_tiling/kernel_tiling.h 注入；若 kernel 又手动 #include <op>_tiling.h 定义同名类、并 REGISTER_TILING_DEFAULT + reinterpret_cast 直接访问字段，编译报 no member named 'minBits'/'maxBits'/'scaleBits'。判别=核 kernel 是否同时存在手动 tiling 头与自动生成头、是否绕开 GET_TILING_DATA。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`exemplifies`）：直调不可用 GET_TILING_DATA_WITH_STRUCT 宏说明`<<<>>>` 直调工程无法使用自定义算子编译期生成的 GET_TILING_DATA_WITH_STRUCT/REGISTER_TILING_DEFAULT 宏，需逐字段从 __gm__ 拷贝 tiling 到 local；其它 void*→GM_ADDR、std::string、goto 限制为次要附带项，见对应卡。
- [kernel侧获取Tiling信息不正确](../../../../guides/programming_guide/appendix/faq/kernel_tiling_info_incorrect.md)（`explains`）：kernel侧获取Tiling信息不正确说明通过算子在kernel侧实现代码中添加PRINTF打印发现kernel侧获取的Tiling信息不正确。
- [高级编程基本流程](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/kernel_operator_implementation.md)（`explains`）：高级编程基本流程说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。
- [GET_TILING_DATA_WITH_STRUCT](get_tiling_data_with_struct.md)（`related`）：GET_TILING_DATA_WITH_STRUCT说明使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。
- [RegisterNoneTiling](register_none_tiling.md)（`related`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《Kernel Tiling》补充：Kernel Tiling 宏与接口集，包含 GET_TILING_DATA、TILING_KEY_IS、REGISTER_TILING_FOR_TILINGKEY 等 Tiling 数据获取与注册接口。
- [COPY_TILING_WITH_STRUCT](copy_tiling_with_struct.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；Kernel Tiling正文说明“Kernel Tiling 宏与接口集，包含 GET_TILING_DATA、TILING_KEY_IS、REGISTER_TILING_FOR_TILINGKEY 等 Tiling 数据获取与注册接口”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
<!-- cannbot:related:end -->
