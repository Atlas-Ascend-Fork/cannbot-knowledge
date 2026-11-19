---
type: Guide
title: Catlass 编译产物缓存：源码、命令、进程命中与动态库寿命
description: 跟踪模型代码生成到Catlass二进制编译与.so加载，区分源去重、磁盘命中、进程映射和CppWrapper/AOT路径。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codecache.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/async_compile.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_scheduling.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/cpp_wrapper_npu.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/cpp_builder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codecache.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/autotune_process.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_template.py
  role: implementation
created_at: '2026-11-10T12:07:13Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Catlass 编译产物缓存：源码、命令、进程命中与动态库寿命

## 固定版本与明确消费者

定向审阅 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 Catlass scheduling、AsyncCompile patch、CodeCache与C++ wrapper相关路径。未编译或加载任何生成产物、导入上游、调用设备或测量时延；未知整卡平台，保留 `draft`、空列表。

发布版 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 虽也有 `_inductor/codecache.py`，所读内容是CacheBase设备/CANN系统身份与AOT打包修复；不含本卡这组Catlass缓存类，同路径 `async_compile.py` 也缺失。文件同名不代表可套用主线缓存层或动态库加载行为。

候选是否生成及融合资格另见[Catlass实际候选与Epilogue](torch_npu_catlass_candidate_and_epilogue_constraints.md)，配置支持范围见[矩阵乘调优指南](torch_npu_inductor_catlass_autotune.md)。本卡从已进入Catlass的编译消费者继续追踪，不承诺默认所有mm都走此链。

## 一次模型生成内的去重与二进制缓存不同

`CATLASSScheduling.define_kernel()` 先按原始源码查wrapper的 `src_to_kernel`，重复源码复用kernel名；新源码替换 `KERNEL_NAME` 后写出 `async_compile.catlass(...,'so',aot_compile=...,is_mix=...)`。它还记录每个kernel的is_mix，让C++ wrapper重建一致的编译路径。

后端初始化明确调用 `patch_async_compile()`，将该方法装到Inductor的AsyncCompile。方法提交一个task，由 `CATLASSCodeCache.load()` 返回DLL wrapper；AOT模式还先compile为 `.o` 并将路径加入 `aot_kernels_o`。这些是实际调用关系，源码内去重、异步提交、二进制已存在和模型最终选中执行仍需分别确认。

## key输入含源码与编译命令，但不是完整环境证明

`CATLASSCodeCache.write()` 用dummy输入/输出路径生成目标扩展名和is_mix对应的编译命令，将其repr作为extra，与原始C++源码一起传给上游write生成key/源码路径。目标so/o与Cube或Mix选择会改变这里的命令输入；不能仅按相同矩阵shape理解为同一制品。

命令包含编译器路径、架构/编译选项、Catlass/CANN include路径与链接选项；include使用realpath规范化。该层不是对目录下全部头文件、编译器和动态依赖内容做完整指纹，因此原路径上替换工具链或模板库不能仅凭旧文件存在判为兼容。跨机与软件升级仍按实际产物和环境身份验证。

`compile(extra_args=...)` 可以把额外参数加入真实命令，但 `write()` 生成key输入的dummy命令未传这组extra_args。当前所读scheduling→AsyncCompile链未传非空extra_args，所以不能据此声称默认模型已发生冲突；若扩展内部调用使用该参数，需要先核对key是否仍能区分实际编译选项。

CANN路径也有初始化时机：`cpp_builder`在导入时根据ASCEND_HOME_PATH是否存在选择正常getter或lazy_error。不能假定导入后补一个环境值，这个已经选择的getter便自动更换。配置、源码和工具链准备应在真实进程导入/编译前完成，本卡未探测本机安装。

## 进程字典、文件锁和磁盘文件是不同命中层

`compile()` 首先查类级 `cache` 字典。进程未命中时按key取得文件锁，在锁内算出输出路径；输出文件不存在才调用编译器，否则跳过编译，再保存input/output路径条目。其他进程可借磁盘文件省编译，但每个进程仍需建立自己的条目和加载状态。

这里对已存在产物只做路径存在检查，没有在本函数验证导出符号、ABI、依赖或数学正确性；“Compilation skipped”不能替代模型可运行的验收。编译命令失败被包装成NPUCompileError，load自身只接受so，不是将o/exe直接当作DLL加载。

类的cache_clear清的是进程字典；它不在该表达式中删除磁盘产物或卸载已映射so。磁盘清理、内存元数据与动态库寿命不能混为一个“清缓存”动作。

## 动态库保留与C++ wrapper路径

Python load使用 `PersistentDLLWrapper`。该类的close只把is_open置假，不调用dlclose；注释解释其目的是避免CANN profiler仍持有已卸载库的callback指针。本卡没有复现该崩溃，也不把进程级驻留描述成没有任何资源代价；删除Python变量不能据此保证所有库映射立刻释放。

JIT C++ wrapper使用原始源码、kernel名替换、严格一致的dedent/换行和is_mix重新调用write计算相同so路径，首次调用通过dlopen/dlsym加载；查找失败会抛错。这里write只生成源码/key路径，不再次触发编译。AOT与JIT使用的是不同加载/链接组织，不能把某层源码缓存命中等同于任意部署包都已包含所需产物。

[MegaCache打包](../../../apis/torch_npu/megacache_artifacts.md)目前对CppWrapper独立二进制有自己的限制，本卡的CppWrapper运行链不消除它。性能核对时分开记录源码去重、进程/磁盘命中、实际编译、动态加载、首轮与稳态调用，再验输出与真实选中kernel；未增加verified或收益数字。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codecache.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/async_compile.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_scheduling.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/cpp_wrapper_npu.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/cpp_builder.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codecache.py)（implementation）

## 自动调优还会申请输入、探测workspace并同步

主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的`autotune_process.py`补充了前文编译缓存之外的测量准备。模板实际构建CATLASSBenchmarkRequest；融合请求另收集epilogue读取的输入。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`同一autotune_process.py路径不存在，不套用主线实现。

| 阶段 | 实际行为与成本 |
| --- | --- |
| 安装 | `_apply_common_npu_triton_patches`调用patch_tuning_process；后者把上游可见设备变量名改为ASCEND_RT_VISIBLE_DEVICES、替换子进程初始化函数，并改ExternKernelGPUBenchmarkRequest的基类组合为NPU mixin与原通用请求类。它也影响extern候选测量，不只Catlass。 |
| 子进程初始化 | NPU可用时创建一个NPU zeros；形参fp32_precision在这个函数体没有被消费，不能据签名认定已设置对应精度策略。 |
| 请求构造/预编译 | 构造时write源码/key；precompile另调用compile。二者不是本地已经完成benchmark或选中Kernel的信号。 |
| 输入准备 | benchmark的output_tensor为None时，按全部input/output TensorMeta重新物化输入和输出，即使调用方原本传了位置输入；有output时直接使用所传对象。 |
| workspace探测 | 首次调用以按输入meta.name去重数量加一个输出的空指针列表查询workspace_size，随后NPU synchronize。成功后保存标志，以后不再查询；这不是每次按实际Tensor地址、别名或新shape重算。 |
| 启动准备 | 获取DLL函数、当前流和输入/输出data_ptr；workspace_size>0时申请ceil(bytes/8)个float64零元素，传空size指针、workspace指针和流，绑定成partial。 |
| 异常 | make_run_fn抛NonzeroWorkspaceNotSupportedError才转为inf；其他异常没有在benchmark统一吞掉。该方法没有finally自动调用cleanup_run_fn。 |

workspace探测的unique meta.name数量与真正启动时的全部输入指针列表是两种组织，当前本地方法没有再次证明两者任意情况下都满足外部ABI。DLL、函数符号、额外参数和代码缓存的完整合同沿用前文；这里没有加载.so或执行查询。

### NPU事件返回毫秒均值，不是所有测量路径共用的口径

do_bench收集直接输入/输出中NPU Tensor的device.index，多个不同索引报错；只有一个时进入该device上下文，没有则取当前NPU设备。它没有递归检查嵌套参数或把非NPU Tensor自动迁移。

`_bench`先调用一次并全NPU同步，再用一对事件包5次调用取得estimate_ms。warmup默认25、repeats默认100被用作毫秒预算，除estimate后将次数分别夹到1..250和1..1000；计时事件包住全部n_repeat，最终以elapsed_time/n_repeat返回毫秒均值。源码没有给estimate_ms==0增加除零保护，也没有在此剔除异常值或取多组中位数。结束后do_bench外层再同步以暴露设备错误。

这条路径没有实验Triton的mspti/event分组选择，也没有在每次fn前自动克隆、重置被修改的输入或核对数值。对有副作用的候选，重复调用可能消费不同内容；计时准备、同步和结果正确性要与[实验Triton输入隔离](torch_npu_experimental_triton_autotune_timing_and_input_isolation.md)分别判断。

融合请求对template inputs作浅列表copy，遍历epilogue的read_names，跳过模板自身输出名，依次从name_to_buffer或graph_inputs寻找并去重；找不到则assert。输出仍取模板节点。benchmark随后建立新的CATLASS请求并返回`(res,None)`，不能把这段集合收集当作已经证明全部融合别名或输出合同。

cleanup_run_fn请求DLL.close、清DLL引用和workspace；它没有复位_workspace_size_updated或workspace_size，因此对象再次使用不能概括为重新查询全部workspace元数据。前述PersistentDLLWrapper的close也不等于操作系统卸载.so。此处仅静态审阅，无设备测量、编译、动态加载或新增verified。

## 固定实现来源

- [autotune_process.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/autotune_process.py)（implementation）：1–306。
- [__init__.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）：99–114。
- [catlass_template.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_template.py)（implementation）：111–119。
