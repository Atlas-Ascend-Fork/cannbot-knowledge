---
type: Guide
title: INT8 NZ的CPU重排：准入、存储与同步成本
description: 解释主线INT8/c0=32的CPU重排、输出容量、同步H2D与stride/参数边界。
tags:
- task.optimization
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/experimental/inference.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_utils/npu_format_cast_via_cpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_utils/npu_format_cast_via_cpu_wrapper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_utils/npu_format_cast_via_cpu.h
  role: implementation
created_at: '2026-11-12T01:57:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# INT8 NZ的CPU重排：准入、存储与同步成本

主线92e1e967的 `npu_format_cast_via_cpu` 包含Host重排、同步和新存储写入：将INT8输入转到CPU、按NZ存储次序重排，再显式同步当前NPU流并把字节写入新输出存储。本文静态读取Python入口、原生实现和绑定，没有执行Tensor转换、SDK或设备；发布7c6c754b缺少所列三个原生文件路径；同一Python文件存在，但没有这里的npu_format_cast_via_cpu入口。

| 准入/参数 | 实际合同 |
| --- | --- |
| acl_format | 只允许29，输出格式固定FRACTAL_NZ |
| 输入 | 必须defined，rank>=2，末两维都>0，dtype必须Char（INT8） |
| customize_dtype | 接收可选整数，主体没有消费其值 |
| input_dtype | 不控制转换，仅在dtype拒绝时参与报错文本 |
| device/stride | 本地没有独立is_npu或is_contiguous断言；输出options来自self，不能据缺断言推广任意设备/布局可用 |

Python转发给 `_npu_utils.NpuFormatCastViaCpu`，绑定默认两个可选参数为None，并把 `torchair.core._npu_utils` 与 `torch_npu.dynamo.torchair.core._npu_utils` 两个sys.modules键设为同一原生模块对象。

| 数据阶段 | 行为与成本 |
| --- | --- |
| 输入准备 | `self.to('cpu').to(Byte)`，从CPU data_ptr起连续读取numel个uint8到vector；没有显式contiguous处理 |
| NZ几何 | 末两轴(k,n)映为(ceil(n/32),ceil(k/16),16,32)，前面维度按weight_array.size/(k*n)计batch |
| padding | 新vector按完整块大小零初始化，再逐元素写对应位置 |
| 输出申请 | empty_with_format使用原self逻辑sizes/options与NZ格式，再检查重排字节数<=输出storage.nbytes |
| 写入 | 同步当前NPU流，取输出storage.data并做HOST_TO_DEVICE的aclrtMemcpy |
| 包装 | 对输出set_(新storage,0,self.sizes(),self.strides())并返回，没有复用原输入storage的步骤 |

从data_ptr线性取numel个元素与最终恢复原stride不是完整非连续布局转换证明，需按真实输入存储核验。局部ceil_div只检查除数非0，NZ重排检查k/n/c0非0；中间加乘和batch取整没有另做逐步溢出/整除验证。输出字节容量检查发生在CPU vector重排与输出申请之后，不能替代前面全部资源预算。

`ACL_STREAM_TIMEOUT` 缺省为-1；存在时strtol按十进制解析，检查ERANGE、至少读到数字、完整消费和int32范围，否则抛RuntimeError。实现先同步流，再取输出指针并复制；同步、指针、容量或Memcpy失败均通过本地断言报错，没有统一重试或改走设备format_cast的fallback。

评估该入口时，应计算CPU中间Tensor、ND与padding后NZ两个vector、新设备输出及显式同步的成本，分别验证符号值、stride和padding内容。原注释中的INT8/c0=32合同不等于FP4/FP8或任意customize_dtype的编码实现；其他权重准备见[模型私有格式改写](torchair_weight_internal_format_preparation.md)。

## 实现来源

- [固定实现1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/experimental/inference.py)：127–133。
- [固定实现2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_utils/npu_format_cast_via_cpu.cpp)：1–173。
- [固定实现3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_utils/npu_format_cast_via_cpu_wrapper.cpp)：1–39。
- [固定实现4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_utils/npu_format_cast_via_cpu.h)：1–13。
