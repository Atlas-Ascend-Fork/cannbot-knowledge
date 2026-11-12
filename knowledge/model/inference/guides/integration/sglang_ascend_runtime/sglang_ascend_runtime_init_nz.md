---
type: Guide
title: SGLang NPU初始化与ND/NZ权重格式的分支守卫
description: 说明init_npu_backend对LLM/扩散导入的区别、ND/NZ对齐与packed-FP4例外、关闭格式转换的风险，以及ZBAL和辅助流只初始化边界。
tags:
- task.implementation
- topic.compilation
- topic.data_movement.layout_transform
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/model_runner_components/attention_backend_setup.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/environ.py
  role: supporting
created_at: '2026-11-08T11:53:39Z'
updated_at: '2026-11-09T04:33:25Z'
platforms: []
aliases:
- init_npu_backend
- npu_format_cast
- SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT
---

# SGLang NPU初始化与ND/NZ权重格式的分支守卫

## 初始化不能等同所有算子可用

init_npu_backend断言NPU，尝试导入custom_ops与sgl_kernel_npu，ImportError只告警后继续；后续实际算子仍可能缺失。LLM路径在sglang.multimodal_gen不在sys.modules时导入transfer_to_npu，再将torch.cuda.is_available重置为False并允许internal format；扩散路径避开这些会影响行为/性能的导入。两条路径都设置jit_compile=False。

_call_once装饰器在调用函数前就设置_has_been_called，异常后不会自行恢复；不能将它理解成“仅成功初始化后才缓存”。进程级导入状态也会影响该分支，混用SRT和扩散时必须核对实际启动顺序。

## 格式选择与对齐

npu_format_cast在非NPU、SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT开启、CPU或meta Tensor时直接返回原Tensor。CPU仅告警，不替调用者转设备。ND枚举为2、NZ为29。普通NZ预筛：最后两维K/N对FP16/BF16要求16/16整除，对INT8/E4M3要求16/32，对以uint8/int32承载的INT4要求16/64。未列dtype直接通过预筛，并非已证明合法；底层op仍是最终约束。

当传customize_dtype或input_dtype时转交底层unpack参数并跳过普通ND回退，因为packed-FP4 matmul要求NZ。全局禁用格式转换的早返回仍更早发生，不能把旧TP1 OOM规避不加条件套到packed-FP4。普通未对齐矩阵保留ND并告警，收益/正确性应按实际consumer核对。

## 其他初始化状态

is_npu_arch35只检查ACL设备0属性601是否恰为(3510,0)，缓存一次，未实现其他源码中的torch_npu SoC回退。wo_a的原生MXFP8还要求serialized block-FP8 checkpoint、128×128块及保留量化配置，不能凭arch35直接开启所有wo_a路径。

ZBAL只有正的SGLANG_ZBAL_LOCAL_MEM_SIZE才初始化。mix alloc模式切换allocator后延迟GVA初始化；helper 以固定61.2GiB减查询所得可用GiB估算 used_memory，再以配置预算 SGLANG_ZBAL_LOCAL_MEM_SIZE 减 int(used_memory*1024) 得到 GVA MiB，并按128MiB向下对齐；61.2GiB只参与已用量估算，GVA扣减基数是配置预算，不能当作任意设备自动探测总容量。非mix延迟初始化直接返回。辅助indexer/share/routed流是进程级惰性状态，等待函数仅在流存在时建立当前流依赖。

## 调试与回退

按import告警→目标torch.ops→参数解析→Tensor设备/dtype/布局→底层op要求检查。权重格式的具体历史OOM案例见[TP1规避](/model/inference/runbooks/performance/sglang_tp1_oom_disable_nz_weight.md)，它不能替代本文packed-FP4边界。回退时恢复env与匹配权重重载，重新验证精度；格式变化不是可随意在存活Tensor上切换的性能旋钮。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。

## GVA与后端构造的先后

非draft NPU且正ZBAL预算时，build_attention_backends在构造resolved后端后、图捕获前调用lazy_init_zbal_gva_mem。SSM attention_arch的Mamba2早返回发生在这段之前，不能把这一处调用泛化为所有SSM runner自动完成GVA初始化。
