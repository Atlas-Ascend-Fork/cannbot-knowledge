---
type: API
title: 旧attentions RainFusionAttention 的布局与输出分配
description: 说明旧Rain接口的TND与BNSD字符串检查、Host序列数组、两输出shape及dtype分配和外部动态核心边界。
tags:
- task.implementation
- topic.attention
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/rainfusionattention.cpp
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/rainfusionattention.h
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
created_at: '2026-11-09T17:53:10Z'
updated_at: '2026-11-09T17:54:19Z'
platforms: []
aliases:
- torch.ops.attentions.rainfusionattention
- rainfusionattention
---

# 旧attentions RainFusionAttention 的布局与输出分配

## 接口与注册

固定提交将 `rainfusionattention` 注册到 `torch.ops.attentions.rainfusionattention` 的PrivateUse1实现，动态调用外部 `aclnnRainFusionAttentionGetWorkspaceSize/aclnnRainFusionAttention`。本卡保存旧Torch wrapper事实，不把相近稀疏注意力API或新命名空间的Device当作其核心。

```python
torch.ops.attentions.rainfusionattention(
    query, key, value, select_idx, select_num_idx, blockshape,
    attn_mask=None, actual_seq_qlen=None, actual_seq_kvlen=None,
    block_table=None, q_input_layout="TND", kv_input_layout="TND",
    head_num=1, mask_type=0, scale=1.0, inner_precise=1, block_size=0,
)  # (attentionOut, softmaxLse)
```

| 参数 | 默认值、转换与本地限制 |
| --- | --- |
| query/key/value/select_idx/select_num_idx | 必选Tensor；wrapper不验证shape/dtype、select范围、计数含义或同device |
| blockshape | 必选Host int64数组，原样转AclIntArray；本层不校验长度/取值 |
| q_input_layout | 默认TND；显式TORCH_CHECK只允许TND或BNSD |
| kv_input_layout | 默认TND；独立TORCH_CHECK只允许TND或BNSD；本地未要求与Q相同，混用是否可接受仍由外部核心决定 |
| attn_mask/block_table | 默认None，变成未定义Tensor，再由helper转nullptr；本地不生成mask或block table |
| actual_seq_qlen/actual_seq_kvlen | optional Host int64数组，None先规范为空IntArrayRef，再调用aclCreateIntArray；不是device Tensor |
| head_num/mask_type | 1 / 0，原样转发，无头数自动推导或mask枚举检查 |
| scale/inner_precise/block_size | 1.0 / 1 / 0，原样转发，无本地数值/范围校验 |

除这两个layout字符串guard外，不从未见校验推导宽输入支持。query至少前三个维度会在输出分配中直接读取；没有独立query rank==3/4检查，不能依赖后续ACLNN检查保护此前的索引。文件中EXPECTED_TENSOR_DIMENSION=3常量未被用于guard，也不能视为真实维数校验。

## 输出与参数顺序

| 输出 | 实际分配 | tuple位置与边界 |
| --- | --- | --- |
| attentionOut | query.sizes()，query.options()、query NPU format | 第一项；不根据value末维重建 |
| softmaxLse | [query.size(0),query.size(1),query.size(2)]，同query options/format | 第二项；没有强制FP32，也没有按TND/BNSD或head_num另推shape |

因此TND三维query的softmaxLse分配会等于query三个维度的组合；BNSD四维则取前三维。这里只陈述wrapper literal shape，不以变量名保证外部核心写入的LSE语义、内容、布局或精度。输出由ATen新allocation持有，是否所有有效元素均写入依赖匹配的外部核心。

两段式查询的业务实参依次为Q、K、V、select_idx、select_num_idx、blockshape、attenMask、actualSeqLengths、actualSeqLengthsKv、blockTable、Q layout字符串指针、KV layout字符串指针、head_num、mask_type、scale、inner_precise、block_size、attentionOut、softmaxLse；helper再追加workspaceSize/executor指针。执行阶段只传workspace/size/executor/currentStream。optional张量与空Host数组的槽位不同，不应在调用适配中合并或交换。

## 动态库与版本范围

### 旧插件的加载、描述符与两段式边界

旧独立package名为attentions，import先将包内ops/vendors/aie_ascendc与customize目录置于原ASCEND_CUSTOM_OPP_PATH之前，再在NPU可用时加载plugin/libPTAExtensionOPS.so；TORCH_LIBRARY(attentions)与PrivateUse1注册暴露对应torch.ops.attentions接口。csrc/attentions/csrc/CMakeLists.txt显式编译六个wrapper（la、rain、ada、sparse estimate、layernorm、pool indexer）及注册/find_op_path，使用C++17，ABI宏取USER_ABI_VERSION（仅0/1，缺省0），链接torch/torch_npu/ascendcl/nnopbase/opapi。build_plugin.sh从已安装toolkit配置环境并复制so入Python包，build_ops.sh只选择laser_attention、ada_block_sparse_attention、sparse_block_estimate三项；这个列表不证明LayerNorm或Rain核心也随包提供。构建脚本未固定可核验的CANN版本，不能由其latest路径或其他新接口推导旧wrapper版本。

EXEC_NPU_CMD按“ASCEND_CUSTOM_OPP_PATH中各op_api/lib的libcust_opapi.so → ASCEND_OPP_PATH/vendors/config.ini的load_priority顺序 → 默认libopapi.so”逐符号查找API及GetWorkspaceSize；两者各自解析，未强制来自同一个so。路径列表在共享库初始化时保存，函数指针为模板静态缓存，不会逐次重新探测环境。缺符号TORCH_CHECK失败，没有Python参考fallback。

Tensor转换保留sizes/strides/storage_offset和原storage指针，并按维数选ACL format：3D=NCL、4D=NCHW、5D=NCDHW、其余ND；storageDims为storage字节数/itemsize的一维容量。它不是按input_layout字符串重新转形、转置、连续化或重排数据。未定义Tensor/缺省optional Tensor转nullptr；IntArrayRef调用aclCreateIntArray转换为AclIntArray，空数组也经该创建函数，而非同义的null tensor。包装层支持的dtype映射不单独证明外部算子支持该dtype。

调用顺序为可选InitHugeMemThreadLocal → 转换参数并调用GetWorkspaceSize得workspaceSize/executor → size>0分配Byte NPU workspace（0为nullptr）→ 取当前NPU stream → OpCommand自定义handler调用第二阶段 → 正常返回时ReleaseConvertTypes/ReleaseHugeMem → cmd.Run后UnInitHugeMem。非零两阶段状态用aclGetRecentErrMsg抛错；源码未用RAII覆盖所有异常清理路径，handler按值捕获描述符裸指针但不捕获workspaceTensor本体，不能仅凭本地代码宣称异步或异常生命周期已验证。executor、底层Host/Device算法与流完成语义依赖实际安装库及torch_npu；本卡只记录wrapper，不提供源码级完整Operator闭包或运行通过结论。

本地构建脚本虽编译Rain wrapper，但build_ops.sh没有选择Rain自定义核心；它可能解析到安装环境的vendor或默认opapi，本次来源未把该外部核心绑定到唯一实现/版本。故平台范围未确认，保留draft、platforms为空且不填写cann_versions，不把aclnnRainFusionAttention调用名冒充完整Host/Device闭包或正式支持证明。

## 来源与提取状态

主来源为[rainfusionattention.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/rainfusionattention.cpp)，声明见[rainfusionattention.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/rainfusionattention.h)，注册见[register_ops.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/register_ops.cpp)。同名底层API知识不能替代旧wrapper的默认值、输出顺序及分配合同。

本次未执行上游、构建、插件加载、通信、真机、数值、性能或测试，无verified事件；没有为外部核心补造数学、shape支持或异常结果。
