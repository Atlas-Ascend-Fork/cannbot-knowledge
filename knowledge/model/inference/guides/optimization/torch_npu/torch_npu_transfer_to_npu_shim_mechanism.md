---
type: Guide
title: transfer_to_npu 迁移 shim：patch 面、参数改写语义与边界
description: 记录白名单式 CUDA→NPU 补丁的启用门槛、设备参数改写规则、第三方库包装与两版差异，不把白名单外接口当已迁移。
tags:
- task.migration
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/transfer_to_npu.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/apis_config.json
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/optional_features.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/monkey_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/transfer_to_npu.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/apis_config.json
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
created_at: '2026-11-12T04:15:22Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# transfer_to_npu 迁移 shim：patch 面、参数改写语义与边界

## 固定版本与证据范围

主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b的patch面差异显著（主线669行、发布508行），差异处逐条标注，两版不能互相推定。本卡为静态审阅，未导入、未构造device、未运行迁移脚本，draft、platforms为空。

## 启用方式与时机

两种启用：显式`from torch_npu.contrib import transfer_to_npu`（须在第一次构造`cuda` device之前——patch在import时刻全量生效，此前已创建的CUDA对象不回溯）；或设`TORCH_TRANSFER_TO_NPU=1`（仅接受`0`/`1`，其他值在`import torch_npu`时抛`ValueError`；主线经`_init/core/optional_features.py`，发布在`torch_npu/__init__.py`末尾）。import时按rank0打印一次性`ImportWarning`，列出被改写device参数的函数清单，并设`warnings.filterwarnings('once')`。教程级用法与"首次构造前导入"的验收事实见[初始化与设备探测](torch_npu_initialization_and_device_detection.md)和[MNIST迁移验收](../../../../training/guides/torch_npu_mnist_migration_acceptance.md)，本卡补机制。

## 四类替换

1. **模块级别名**：`torch.cuda←torch_npu.npu`、`cuda.amp←npu.amp`、`cuda.random←npu.random`、amp子模块，及`torch.profiler`系列（`ProfilerActivity.CUDA←NPU`）；主线新增`cuda._pin_memory_utils←npu._pin_memory_utils`。patch经`_apply_patches`挂接，缺失的中间模块会被创建为空模块再挂接（monkey_patches的`_getattr`）；发布调用`torch_npu._apply_patches`。
2. **白名单函数包装**（`_wrapper_cuda`，本身仅`@wraps`、不带disable）：`torch.*`创建/factory 47个、`Tensor.new_*/to/pin_memory`、`nn.Module.to/to_empty`、`torch.cuda`工具22个（主线另加`get_rng_state/set_rng_state`）、`fft.fftfreq/rfftfreq`、`DistributedDataParallel.__init__`、`cuda.device`与`DeviceContext.__init__`、`amp.autocast.__init__`、`UntypedStorage.__new__`；主线新增autocast开关系列（`is/set_autocast_enabled`、`get/set_autocast_dtype`、`get/set_autocast_gpu_dtype`、`custom_fwd/bwd`）；`init_process_group`叠加nccl→hccl替换（主线并把backend串内`cuda`也改写为`npu`）、FSDP/DeviceMesh/`_new_group_with_tag`/pipelining stage与`build_stage`；`torch.profiler.profile`若收到CUDA专属`experimental_config`则告警并剔除。通用`_wrapper_cuda`在**两版**都遍历全部普通位置参数做device替换（含`cuda`的字符串、type含`cuda`的`torch.device`；int是否改写由`replace_int`门控、即仅`to`/`to_empty`）；`_fields`命名字段限制只属于主线`_patch_nametuple`（针对`Kernel` namedtuple的`device/device_type/map_location/device_id`字段），发布版`_patch_nametuple`同样整包替换位置参数但`replace_int=False`不做整数转换。
3. **直接别名**：`Tensor.cuda←Tensor.npu`、`is_cuda←is_npu`、`Module.cuda←npu`、`TypedStorage.is_cuda`（主线）、`cuda.DoubleTensor←npu.FloatTensor`（double不支持——数值语义变float，是精度差异不是等价替换）、`is_nccl_available←is_hccl_available`、`ProcessGroupNCCL←ProcessGroupHCCL`（两处，详见[集合通信约束](../../../../training/guides/torch_npu_native_collective_constraints.md)）、`CUDAGraph←NPUGraph`、`cuda.memory._record_memory_history/_snapshot/_dump_snapshot`、`_C._host_emptyCache`、`default_generators`经`npu._lazy_call`惰性更新（主线）、`torch.Generator/_Event`换代理类：主线用`_TorchTypeProxyMeta`保持`isinstance`可用，且torch≥2.13起`Stream.record_event`拒绝子类实例，`_EventProxy`改为返回基类实例；发布版代理会破坏这两点。
4. **环境探测**：`UninitializedTensorMixin._allowed_methods`的`to`替换（meta参数惰性物化到NPU）、删除`Backend.default_device_backend_map['cuda']`（防`init_device_mesh`按cuda解析nccl）、`torch._utils._get_available_device_type→'npu'`（不可用时None）、DCP `filesystem._OverlappingCpuLoader.__init__`改写（device_type从stream或`'npu'`解析并补`wait_stream`，与[save_async](../../../../training/apis/torch_npu/save_async.md)的异步保存面相邻）、`torch.utils.cpp_extension`指向torch_npu版本并仅包装`include_paths`（构建面见[扩展后端范围](torch_npu_native_extension_backend_scope.md)）。

## 参数改写语义（易踩坑）

- 字符串：只要**含`cuda`子串**就整体`replace('cuda','npu')`（如`"my_cuda_flag"`也会被改写）；不含则不动。
- `torch.device`：type含`cuda`时映射为`npu:index`（无index则`npu`）。
- int：**位置参数**仅`to`/`to_empty`（`replace_int`门控，bool除外）改写为`'npu:N'`；**关键字**则不同——device kwargs（`device/device_type/map_location/device_id`）取值为精确int类型时，任意白名单函数都会被`_replace_cuda_to_npu_in_kwargs`无条件改写为`'npu:N'`。位置与关键字行为须分开看。
- dict只改写顶层str键/值（含`cuda`才替换），嵌套dict与任意对象不递归；`device_ids`：list在两版都会被**原地改写**（kwargs持有同一list对象——发布版未重新赋值`kwargs`键但同样生效），主线额外支持tuple并把重建的tuple写回`kwargs`。
- 主线`_replace_cuda_to_npu_in_kwargs/_list/_dict`三个helper带`@torch._dynamo.disable`避免被trace；`_wrapper_cuda`本身只有`@wraps`，发布版所示helper无装饰。
- `torch.jit.script`仅在`_dynamo.use_jit_script`为False（默认）时旁路返回原对象；为True时仍调用真正的`torch.jit.script`（发布版告警文案曾写“using torch.jit.script successfully”，有误导，主线改为“torch.jit.script is in use.”）。`script_method`两版恒为透传。需要TorchScript的脚本不能依赖该shim的默认旁路。

## 第三方库包装

`apis_config.json`按已安装包版本门控包装：transformers≥4.32.0（11项，含`TrainingArguments.__post_init__`、Trainer RNG保存/恢复、`is_torch_cuda_available`等探测）、trl≥0.7.1（2项）、peft≥0.5.0（`infer_device`）、accelerate≥0.22.0（13项，含`notebook_launcher`、`get_max_memory`、bnb量化加载、`PartialState._prepare_backend`等）。机制：import时先快照真实`torch.cuda.is_available`（此时patch尚未生效），包装后的API执行期间临时恢复该真实值、正常返回后还原——因为patch后`torch.cuda.is_available()`实际返回NPU可用性，这些探测/命令类API需要看到真实CUDA状态，避免第三方库误入CUDA专属路径。该包装**没有**try/finally：被包装API抛异常时`torch.cuda.is_available`停留在真实值，不会自动还原。配置加载有硬校验：拒绝符号链接、不存在/不可读、basename超200字符、超10MB、非dict JSON（均按空配置处理）；版本比较用`packaging.Version`，缺依赖回退`distutils.LooseVersion`。名单外的第三方API不改写；包装发生在shim import时点，之后安装/升级的库不会被补。

## Triton/Inductor 面

主线拆成双通道：`torch.utils._triton.has_triton`固定为False（短路CUDA专属测试门控），dynamo/inductor各入口的`has_triton`改为设备感知的`_dynamo.has_triton`（经`_compat.inductor`，NpuInterface注册后失效缓存）；`get_gpu_type`各处指向恒`'npu'`（配合torch_npu inductor的`patch_is_gpu`清lru缓存）；`benchmarking._get_default_gpu_device_type`强制`'npu'`（否则cuda+npu同时报告可用会触发上游`assert len(avail_gpus) <= 1`）；`torch.npu.is_available()`时把Triton NVIDIA `CudaDriver.is_active`置False（防CUDA Triton driver与昇腾driver冲突）；`trace_rules._disallowed_callable_ids.function_ids`置None。**发布版只有单点patch：`torch.utils._triton.has_triton`恒False**，缺少主线逐别名/设备感知patch；dynamo/inductor各消费点按实际版本/导入时机核对——两版Triton patch面不同。Shim不能替代显式的后端/设备检查（见[Profiler 兼容性](torch_npu_native_profiler_compatibility.md)）。

## 失效边界

白名单外的torch接口、自定义函数、第三方CUDA扩展不做参数改写；`'cuda'`子串替换有字符串副作用；`DoubleTensor→Float`引入精度差异；jit.script默认旁路（`use_jit_script=True`时仍调真script）；patch为进程级全局，不回溯已创建对象，也不提供CUDA kernel级兼容；与dynamo交互时`function_ids`重置等行为随torch版本耦合。迁移既有TorchNPU旧接口另见[旧接口迁移](torch_npu_legacy_api_migration.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/transfer_to_npu.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/apis_config.json)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/optional_features.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/monkey_patches.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/__init__.py)（implementation，定向阅读`_enable_optional_features`调用段）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py)（implementation，定向阅读jit/triton相关段）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/transfer_to_npu.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/apis_config.json)（implementation，与主线逐字节一致）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation，定向阅读环境变量门段）
