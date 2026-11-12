---
type: API
title: SGL SiTU 与 MXFP8 融合接口的固定宽度契约
description: 明确950专用 situ_mxfp8_quant 的6144输入宽度、BF16舍入边界、32元素scale和有效前缀。
tags:
- task.implementation
- topic.compute.quantization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/situ_mxfp8_quant.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/activation/situ_mxfp8_quant/op_kernel/situ_mxfp8_quant.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/situ_mxfp8_quant.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/situ_mxfp8_quant.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/activation/situ_mxfp8_quant/torch_adapter.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/activation/situ_mxfp8_quant/op_host/situ_mxfp8_quant.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/activation/common/kernel/mx_quant_kernel.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/situ_mxfp8_quant/op_host/situ_mxfp8_quant.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/situ_mxfp8_quant/op_kernel/situ_mxfp8_quant.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/adv_api/activation/sigmoid.h
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/dav_3510/kernel_tpipe_impl_c310.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/kernel_utils_base.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/adv_api/detail/activation/sigmoid/sigmoid_3510_impl.h
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T16:55:36Z'
platforms:
- '950'
aliases:
- situ_mxfp8_quant
---

# SGL SiTU 与 MXFP8 融合接口的固定宽度契约

## 调用入口

```python
from sgl_kernel_npu.operators.activation import situ_mxfp8_quant

def situ_mxfp8_quant(
    hidden_states: torch.Tensor,
    group_list: torch.Tensor,
    group_list_type: int = 1,
    beta: float = 4.0,
    linear_beta: float = 25.0,
    *,
    impl="auto",
) -> tuple[torch.Tensor, torch.Tensor]:
    ...
```

## 输入与输出

本接口仅支持 950（上游旧称 A5、arch35/3510）。arch22 不编译该算子，并在公开 Python 层对所有实现报不可用。输入是连续 NPU BF16 `hidden_states: [capacity,6144]`，capacity>0；前3072列为gate、后3072列为up。

返回两个新连续Tensor：FP8 E4M3FN payload `[capacity,3072]`，E8M0 scales `[capacity,48,2]`。每行96个scale字节，每32个payload值共用一个scale；最后两维仅是与厂商MX布局一致的视图。

## 精度边界

SiTU 使用 FP32 执行 gate/up 的 soft-saturation 与 sigmoid，默认 beta=4、linear_beta=25。激活先按 RNE 舍入为 BF16，再做MX量化；不能省略这次中间舍入。按组的BF16最大指数构造2的幂scale；量化值显式截断到±448后，RNE转换为E4M3FN。整组零的scale字节为0，含非有限值的组为255。

## 有效行与错误处理

同设备连续非空 int32/int64 `group_list:[E]` 的type=1表示计数求和，type=0表示末项累计总数；只使用总数，不根据各expert边界重排数据。仅当 int64 计数总数非负且可由 uint32_t 表示（type=1求和还须不发生int64溢出）时，最多写前 `min(valid_rows,capacity)` 行，超出容量按容量截断，其余payload/scale是未初始化padding。设备端不校验计数，GetValidRows 先把正的int64末项/计数和窄化为uint32_t，Process随后才按capacity截断；超过uint32_t范围没有上述截断保证，例如capacity=1、group_list=[4294967296]在两种编码下均会窄化为0有效行。

公开层检查固定宽度、类型、连续性、group元信息和正数界限；无效输入报错。auto/ascendc调用包内Torch原生算子，不自动回退，子集wheel还须实际包含此算子。显式torch_native是数学对照，不用于性能评估。验证应反量化有效前缀并设置容差，不能要求FP8逐位一致。

## 原生实现与旧入口边界

同一固定提交还保留旧 `activation/situ_mxfp8_quant.py`，只检查x二维/6144列及type属于0/1，默认属性同为1/4/25，再调用同名Torch schema。legacy构建绑定 `sglang::npu_kernel::situ_mxfp8_quant`，通过 `EXEC_KERNEL_CMD` 把四个GM和六个标量直接传给旧Device；refactor构建同名schema则绑定自有ACLNN adapter。二者是替代构建，不能把同名Torch入口当成相同Host ABI，也不能混装注册。

旧Direct与新原生body的SiTU、BF16中间舍入和三量化helper共用数学，但旧Host没有新adapter的NPU类型检查/DeviceGuard，也没有Tiling的C/E<=UINT32_MAX及double→float后正数复查。旧macro只capture转换后的指针/标量，没有新adapter的5个Tensor capture和record_stream，且没有传播launcher返回值；这些是可见生命周期/错误处理差异，不构成本次已观测UAF或运行故障。

refactor adapter初始化query的workspaceSize=0/executor=nullptr，检查query与execute状态；使用查询W字节workspace，5个Tensor均record_stream，排队lambda按值持有Tensor和4个ACL描述符。自有Tiling workspace[0]=0、Device不读workspace，不能推出生成框架查询总W必为0。返回输出仍为异步；调用方必须满足输入及下游stream依赖。

实际量化的缩放乘法仍以BF16执行，再显式±448夹取/扩宽FP32/RINT FP8。scale0还覆盖整组BF16指数域为0的subnormal，不应解释为仅数值全零。Host只用>0检查beta/L，正无穷或倒数溢出未被排除，不能据实数公式承诺全部非有限输入结果。

本次进一步读取SDK9.2.0的3510实例发现：entry保存并清CTRL60后才构造含TPipe的算子；TPipe→InitSocStateImpl把CTRL60重新置1，之后才Process，退出仅恢复saved bit60。因而不能声称整段计算在bit60=0下执行或完整CTRL恢复。SDK实际Sigmoid仍为FP32 exp/add/div序列；此源码顺序边界不等于真机数值故障结论。此外Process的u32向上取整和end加法须避免环绕，例如R<=UINT32_MAX−(P−1)是足够条件，现Host没有该检查。

完整资源、两编码及各int32/int64 selector、UB58848B、同步与上述静态条件见[950 ACLNN源码算子卡](../../operators/aclnn/nn/activation/sgl_situ_mxfp8_quant_950.md)。此处保留公开API合同，Operator的source_closed/draft表示实现可追溯，不能替代数值验证。


## 固定来源与验证状态

- [activation/situ_mxfp8_quant.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/situ_mxfp8_quant.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
