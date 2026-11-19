---
type: Guide
title: 实验Triton静态启动：准入、参数ABI与工件生命周期
description: 解释静态/普通回退、API能力探测、constexpr过滤、metadata门槛、二进制持有与fast全局runner协议。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/compile_result.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/adapter.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/metadata.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/fast_launcher.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/compat.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: implementation
created_at: '2026-11-11T08:02:02Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton静态启动：准入、参数ABI与工件生命周期

## 固定包与准入结果

针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的实验Triton静态启动包；审阅本地Python模块，C++启动器、CANN与外部Triton实现仍独立。发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b的这些静态包同路径未出现，仅记录路径差异。未导入模块、执行生成代码、读写npubin、反序列化或运行设备；保持draft和空平台。

can_statically_launch读取torch._inductor.config，不是实验模块同名config的局部开关。use_static_triton_launcher关闭就返回None。开启后要求_C._StaticNpuLauncher._is_supported存在并为真；cpp_wrapper、被禁的用户自调优kernel、store_cubin、TRITON_REGISTER_TENSOR_MSPROF为true/1、非空启动hook，以及最终需要workspace、lock或device print的情况均拒绝静态启动。这里只保存源码门槛，不推断外部开关默认值或具体安装已支持所需aclrtLaunchKernelWithHostArgs。

_hook_is_empty接受None或可取calls且len(calls)==0的对象；缺calls不视作空hook，len抛TypeError也返回False。hook来源先尝试上游triton_compat.knobs，只有ImportError才换binary类属性。适配器指定的NPUStaticArtifactError/RuntimeError/TypeError/ValueError被转成CannotStaticallyLaunchNPUKernel；外层只捕获这个本地异常，记录原因后在strict_static_triton_launcher为真时重抛，否则返回None。不能改写成任意异常都会安全回退。

所列_precompile_config消费者在TritonBundler.put后调用准入函数：有静态kernel才返回NPUStaticTritonCompileResult，否则构造普通NPUTritonCompileResult。这个选择不是已有编译或设备执行的成功凭据。

## 三组参数名称分别服务网格与设备ABI

适配器先要求binary.asm['npubin']为非空bytes、src.fn.arg_names存在、signature为dict。signature及constants的键可直接用参数名或整数索引；tuple键必须非空，取首项后只接受整数，不接受tuple内的字符串参数名。未知名、负索引或越界抛本地工件异常。runtime参数依signature索引排序，去掉类型为constexpr或已列入constants的项，再逐项转换arg_kind。它不是把所有Python外层参数原样交给设备。

指针类型按以*开头识别为tensor，tensordesc显式拒绝；支持所列有符号/无符号整数和浮点标量，i1为bool、u1映射u32，fp16/bf16/fp32/f32映射主机f32、fp64映射f64，其他类型拒绝。标量装包类型不等同于Tensor内部dtype转换。

compat.py通过能力探测选择IS_TRITON_36_PLUS：可导入triton.knobs，且两个compiler路径均不暴露AttrsDescriptor才为真；混合接口形态会落入旧路径。这里不按版本字符串排序，也不保证任何自定义Triton构建的完整兼容。

| 适配分支 | 外层launcher_arg_names及规范化metadata |
| --- | --- |
| 新API形态 | 先取声明constexpr的参数名与num_warps/num_stages的并集，再与compile_meta.constants的键求交，只从arg_names去掉这个交集；声明constexpr若不在该字典不会在此被删除。使用TRITON_ASCEND_3_6布局，pure字段为is_pure_simt，lock字段为sync_block_lock_layout。 |
| 旧API形态 | 去掉声明的constexpr索引，以及compile_meta.constants里值为None、并非已知constexpr且不在compile_meta.signature的名字；使用TRITON_ASCEND_3_2布局，pure字段为force_simt_only，lock字段为lock_num。 |

kernel构造时再把runtime_arg_names映射到launcher_arg_names的位置；缺名报错。arg_names、launcher_arg_names和runtime_arg_names三组列表的用途不同。make_launcher还在外层def_args追加extra_launcher_args，runner_args则只含grid_0/1/2、stream与runtime_arg_names，不把额外网格参数自动加到设备参数。网格与外层签名生成见[共享网格和启动源码](torch_npu_experimental_triton_grid_and_launcher_codegen.md)，不应以同长度或同顺序假设取代这些过滤与映射。

## metadata校验不替代设备能力矩阵

metadata保存schema、layout、target_arch、mix/parallel、SIMT、动态共享内存、FFTS、CTA/cluster、workspace/lock及device-print信息。适配器要求target.arch非空，mix/parallel和对应pure字段、shared_mem_dynamic_size存在；mix/parallel转小写，enable_simt由parallel含simt或pure标记决定。global/profile scratch大小大于0时直接拒绝，因为此启动器不为活跃需求分配这些存储。

FFTS探测调用外部is_ffts_supported及force_disable_ffts；后者带arch调用抛TypeError时才尝试无参形式。该探测的ImportError/TypeError/ValueError变成本地工件异常，不用猜测值替代ABI结论。

NPULaunchMetadata是frozen dataclass，validate要求schema=1、layout为本地Enum实例、mix为aic/aiv、parallel非空、shared/workspace/lock非负、pure要求enable_simt、num_ctas=1且cluster_dims=(1,1,1)。target仅用前缀白名单Ascend910B/Ascend910D/Ascend910_93/Ascend910_95/Ascend950筛选；这是字符串门槛，不把“910B-or-newer”报错文案推广成所有后续产品都支持，也不替代平台运行认证。

trailing_pointer_count在3.2布局为0，在3.6非pure为1、pure为3，源码说明这些尾槽对应DTData及pure情况下的scratch指针。本地返回计数，真正字节布局/零初始化由未在此展开的原生实现承担，不能由Python数值直接认定C++装包已验收。

## 二进制恢复、装载与持有者

reload_npubin_path按compile_meta.device与kernel.hash定位Triton缓存中的name.npubin；路径不存在且有raw bytes才写回，否则抛错。reload_cubin_path只是TritonBundler使用的兼容入口，实际委托npubin恢复，不说明装载的是CUDA cubin。

kernel保存元数据、名称/hash、参数列表和寄存器等字段；_C_impl惰性获取_StaticNpuLauncher，缺失即报错。load_kernel已经持有loaded_kernel时直接返回；否则先validate，必要时从路径读raw bytes，再调用原生_load_kernel传入device、arg_kind及规范化启动字段。loaded_kernel和function指向同一不透明拥有者，随后清掉这个运行实例的npubin_raw与npubin_path。_init_handles使用构造时device装载，不是每次run自动切换设备。

close先清Python的loaded_kernel/function再委托原生_unload_kernel；没有本地同步承诺。__del__只释放这两个引用，注释将最终清理交给C++拥有者。run要求已经装载、实际参数数量等于runtime_arg_names，再把grid、stream整型化并交_launch_kernel；它没有在Python层自动加载或重新核验Tensor数值、全部shape和流完成状态。

__getstate__浅复制状态并去掉装载对象、function、npubin_path及_C_impl；__setstate__恢复字典、清_C_impl，旧状态缺runtime_arg_indices时补映射。它没有在保存时重新补回已被load_kernel清除的raw bytes；注释要求bundle副本先于启动器物化建立，不能假定任意已装载实例再保存后都可独立恢复。

## fast静态启动器保持全局runner协议

build_fast_launcher只接受Python函数、_is_static为真，且runner既不是局部变量也不是闭包自由变量的情况；runner绑定成默认形参的旧协议会被拒绝。随后要求可导入_FastNpuLauncher，并从全局runner绑定方法取kernel，且该kernel已有loaded_kernel。

成功时以_FastNpuLauncher(loaded)替换复制globals中的runner，用相同code/defaults/closure重建函数，复制kwdefaults和函数属性，保留_static_kernel_owner并设置_is_fast_static。它没有重写设备算子或网格。已知属性/键/类型/值异常返回None，其余构建异常记录warning也返回None；导入阶段只捕获ImportError。

有界_build_fast_launcher消费者还受use_fast_triton_launcher控制：先取得原始launcher，不接受未知包装，仅允许声明的downcast wrapper在优化后重新套回。相关downcast实现和原生fast执行体仍独立。排查未命中静态或fast路径时，应记录准入原因、API能力形态、runtime参数过滤、metadata、二进制副本建立时点及实际runner；这些路径的存在和减少主机开销的意图都不能替代性能测量。

## 固定来源

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/compile_result.py)：1–195；完整本地模块，外部实现另计。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/adapter.py)：1–270；完整本地模块，外部实现另计。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/metadata.py)：1–105；完整本地模块，外部实现另计。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/kernel.py)：1–198；完整本地模块，外部实现另计。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/fast_launcher.py)：1–48；完整本地模块，外部实现另计。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/__init__.py)：1–17；完整本地模块，外部实现另计。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/compat.py)：1–41；完整本地模块，外部实现另计。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)：634–649、1060–1082；仅所列消费者，不提升整个模块资格。
