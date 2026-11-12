---
type: API
title: SGLang LaserAttention 的FP16和形状硬边界
description: 说明新原生la的FP16与形状边界，并区分旧attentions::la的四维校验、双FP32输出与动态ACLNN调用合同。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/laser_attention.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/laser_attention/op_kernel/laser_attention.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/laser_attention/op_kernel/CubeForward.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/laser_attention/op_kernel/VectorForward.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/laser_attention/op_host/laser_attention_tiling.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/la.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/la.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/register_ops.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/pytorch_npu_helper.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/find_op_path.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/find_op_path.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/CMakeLists.txt
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_plugin.sh
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_ops.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_ascendc_ops.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/setup.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/attentions/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/attentions/env.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/attentions/lib.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/build.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/laser_attention/torch_adapter.cpp
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
aliases:
- la
- LaserAttention
---

# SGLang LaserAttention 的FP16和形状硬边界

## 接口原型

```python
from sgl_kernel_npu.operators.attention import la

def la(
    query,
    key,
    value,
    *,
    atten_mask=None,
    alibi_mask=None,
    drop_mask=None,
    scale_value=1.0,
    head_num=2,
    input_layout="BNSD",
    keep_prob=1.0,
    pre_tokens=2147483647,
    next_tokens=1,
    is_highPrecision=True,
    impl="auto",
):
    ...
```

## 语义与约束

`la` 的原生Ascend C仅覆盖arch22。Q为 `[B,Nq,S,D]`，K/V为 `[B,Nkv,S,D]`，支持Nq是Nkv的整数倍的GQA；原生pre_tokens保持默认2147483647时，语义为稠密非因果`softmax(scale_value*QKᵀ)V`。Q/K/V运算数为FP16，Cube使用FP32累加，但QK分数以F322F16写回；Vector在half缓冲上缩放、减最大值和exp，softmax中间值仍写回half，再参与V乘法；最终输出为FP32。FP32累加/输出不等于全流程FP32计算。input_layout只能BNSD，keep_prob必须1.0。

原生实际仅实例化FP16：声明中BF16并不代表有匹配Kernel入口，BF16会在启动时报funcEntry错误。Kernel要求S是256倍数、D=128，其他shape可能不报错却给错误结果；S<128还存在AIC/AIV握手不匹配导致死锁的来源说明。因此必须在调用前守住shape条件，不能用“调用未抛异常”代替正确性判断。

原生Host把默认pre_tokens映射为windowLen=0；非默认值传入windowLen，Vector在非零windowLen下会改写末尾分数（例如pre_tokens=128屏蔽末尾块），不再适用上述全量稠密公式。要求全量稠密注意力时须保持pre_tokens=2147483647；独立参考实现忽略窗口参数，两者不能在非默认窗口下直接视为等价。

mask/alibi/drop_mask字段是兼容占位，稠密Kernel不使用，不应借此请求因果、ALiBi或dropout。head_num应等于Nq，scale默认1.0；调用方通常需显式D^-0.5。所有张量在同NPU，非连续输入内部连续化。

## 返回与参考边界

返回顺序为 `(softmax_log_max_sum,attention_out)`。第一个FP32 `[B,Nq,S]` 仅分配，Kernel从不写，内容未定义；精度只比较第二个FP32 `[B,Nq,S,D]`。它不能当作可用LSE、也不能用于下游归一化。

`auto`选Ascend C，无自动回退；arch35仅参考实现可用。参考允许FP16/BF16但仍只覆盖无mask、keep_prob=1的稠密BNSD，并忽略窗口属性。验证时选合法S/D与FP16，独立比较attention_out，另核查集成端是否误用了未写辅助tensor；本卡不提供运行该已知非法shape的建议。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 旧attentions命名空间的独立wrapper

以上FP16、S/D、mask占位、辅助输出未写与auto/reference结论限定新 `sgl_kernel_npu.operators.attention.la` 的自有原生实现；同仓旧 `torch.ops.attentions.la` 由独立插件注册，新桥接解析aclnnSglLaserAttentionGetWorkspaceSize/aclnnSglLaserAttention，旧插件解析aclnnLaserAttentionGetWorkspaceSize/aclnnLaserAttention，是两套不同符号，不能互相继承这些Device结论。旧schema没有impl参数、没有auto/reference选择，`la.cpp::la` 动态调用 `aclnnLaserAttentionGetWorkspaceSize/aclnnLaserAttention`。

| 旧schema参数 | 默认值/本地行为 |
| --- | --- |
| query/key/value | 必选Tensor；只对query显式检查rank==4，非4D先抛std::invalid_argument，错误文本含实际rank；本wrapper未验证K/V rank、S/D、GQA或同dtype/device |
| atten_mask/alibi_mask/drop_mask | 默认None，转未定义Tensor，再由helper转nullptr；有值原样转描述符，不由本wrapper计算mask |
| scale_value/head_num/input_layout | 1.0 / 2 / BNSD，原样转发；本wrapper未只允许BNSD，不能从默认值推导layout校验 |
| keep_prob/pre_tokens/next_tokens | 1.0 / 2147483647 / 1，原样转发 |
| is_highPrecision | True，原样转发，不按新原生无body/精度key推断旧外部实现 |
| 返回tuple顺序 | (softmax_log_max_sum,attention_out)，两者都强制FP32，format继承query |
| softmax_log_max_sum allocation | query前三维[Q0,Q1,Q2]，不是按head_num/input_layout重新推导 |
| attention_out allocation | query.sizes()，不按value的末维重建 |

旧wrapper仅分配输出后传给外部ACLNN，没有自身softmax或写辅助tensor的body；不能把新Kernel“第一个输出从不写”的事实移作旧动态库的结论，也不能反向把旧外部库行为补成新Kernel功能。本地缺少更宽shape/dtype检查，不等于外部ACLNN支持任意形状。此旧ABI的可核验平台/CANN版本未固定；本卡Frontmatter的A2/A3对应前文新原生证据，不扩大为旧动态库支持范围。

### 旧插件的加载、描述符与两段式边界

旧独立package名为attentions，import先将包内ops/vendors/aie_ascendc与customize目录置于原ASCEND_CUSTOM_OPP_PATH之前，再在NPU可用时加载plugin/libPTAExtensionOPS.so；TORCH_LIBRARY(attentions)与PrivateUse1注册暴露对应torch.ops.attentions接口。csrc/attentions/csrc/CMakeLists.txt显式编译六个wrapper（la、rain、ada、sparse estimate、layernorm、pool indexer）及注册/find_op_path，使用C++17，ABI宏取USER_ABI_VERSION（仅0/1，缺省0），链接torch/torch_npu/ascendcl/nnopbase/opapi。build_plugin.sh从已安装toolkit配置环境并复制so入Python包，build_ops.sh只选择laser_attention、ada_block_sparse_attention、sparse_block_estimate三项；这个列表不证明LayerNorm或Rain核心也随包提供。构建脚本未固定可核验的CANN版本，不能由其latest路径或其他新接口推导旧wrapper版本。

EXEC_NPU_CMD按“ASCEND_CUSTOM_OPP_PATH中各op_api/lib的libcust_opapi.so → ASCEND_OPP_PATH/vendors/config.ini的load_priority顺序 → 默认libopapi.so”逐符号查找API及GetWorkspaceSize；两者各自解析，未强制来自同一个so。路径列表在共享库初始化时保存，函数指针为模板静态缓存，不会逐次重新探测环境。缺符号TORCH_CHECK失败，没有Python参考fallback。

Tensor转换保留sizes/strides/storage_offset和原storage指针，并按维数选ACL format：3D=NCL、4D=NCHW、5D=NCDHW、其余ND；storageDims为storage字节数/itemsize的一维容量。它不是按input_layout字符串重新转形、转置、连续化或重排数据。未定义Tensor/缺省optional Tensor转nullptr；IntArrayRef调用aclCreateIntArray转换为AclIntArray，空数组也经该创建函数，而非同义的null tensor。包装层支持的dtype映射不单独证明外部算子支持该dtype。

调用顺序为可选InitHugeMemThreadLocal → 转换参数并调用GetWorkspaceSize得workspaceSize/executor → size>0分配Byte NPU workspace（0为nullptr）→ 取当前NPU stream → OpCommand自定义handler调用第二阶段 → 正常返回时ReleaseConvertTypes/ReleaseHugeMem → cmd.Run后UnInitHugeMem。非零两阶段状态用aclGetRecentErrMsg抛错；源码未用RAII覆盖所有异常清理路径，handler按值捕获描述符裸指针但不捕获workspaceTensor本体，不能仅凭本地代码宣称异步或异常生命周期已验证。executor、底层Host/Device算法与流完成语义依赖实际安装库及torch_npu；本卡只记录wrapper，不提供源码级完整Operator闭包或运行通过结论。

旧wrapper证据为[la.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/la.cpp)、[register_ops.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/register_ops.cpp)与[pytorch_npu_helper.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/pytorch_npu_helper.h)。本增量只闭合接口与分配/调用事实，未执行编译、插件加载、真机、数值或性能测试，无verified事件。

## 约束与接入的固定源码

- [torch_adapter.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/laser_attention/torch_adapter.cpp)：新aclnnSglLaserAttention符号解析。
