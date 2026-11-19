---
type: Guide
title: 原生Module与参数容器：方法级平台和dtype边界
description: 区分Module.compile/double等950DT例外、方法类型表、Parameter/Buffer与Lazy元数据，避免泛化到所有模型参数。
tags:
- task.implementation
- topic.compilation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-__future__.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-__future__.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/Serialization-semantics.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Serialization-semantics.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-aliases.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-aliases.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_module.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/api_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/patch_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/__init__.py
  role: implementation
created_at: '2026-11-09T12:17:09Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生Module与参数容器：方法级平台和dtype边界

## 固定版本与清单解释

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14支持页及完整子方法，产品按A2/A3训练系列与950DT逐项记录，不扩展950PR或发布组合。文档版本差异不直接证明发行历史或实际包回归。上游“已验证产品”属于清单口径，本卡仅静态审阅，未执行上游、NPU或性能实验。

页面说明未收录API尚未验证、未验证产品不纳入；缺少条目不等于绝对不支持。限制字段与正常方法说明分开阅读，这份支持表不替代完整社区参数手册。

## 方法级产品矩阵

Module类支持三类产品，不意味着全部方法同样支持。compile、double、set_submodule、xpu在清单的950DT行明确不支持，A2/A3行支持；不能据通用torch.compile或其他图后端的950能力覆盖Module.compile的单独条目。

xpu条目另称NPU形式名称为Module.npu；xpu的产品标记不能直接当作实际npu方法的独立支持矩阵。cuda条目也不自动说明当前Python安装是否完成CUDA→NPU迁移映射，实际入口和设备另行核对。

mtia在2.7.1、2.11、2.12、2.13页列三类产品均不支持；2.9、2.10、2.14页没有该方法，不从未收录推定行为改变。

## 中文dtype表的粒度

Module、Parameter、Buffer、Sequential、ModuleList、ModuleDict、ParameterList、ParameterDict及LazyModuleMixin的主条目多写input仅FP32。它们不是参数张量形状/语义手册；同一来源又明确列Module.bfloat16及具体BF16算子，因此不能从笼统的input/self字段推出“所有模型与参数必须转FP32”。对具体调用保留该条目范围，混合精度与实际参数另按算子/方法验证。

| Module方法 | self条目 |
| --- | --- |
| cpu、cuda、extra_repr、forward、get_parameter、get_submodule、named_children、named_modules、state_dict、to、to_empty、train、zero_grad | FP32 |
| eval | FP32、INT64 |
| float、half | FP16、FP32 |
| type | FP16、FP32、INT64 |
| load_state_dict、modules | 2.9/2.10/2.14页列FP32；2.7.1及2.11..2.13页未重复该限制 |

bfloat16、buffers/children、named_buffers/named_parameters/parameters、get_buffer/get_extra_state/set_extra_state、add_module/register_module、requires_grad_等另列产品但无新的dtype细表，不把省略解释为任意dtype全可用。

## 容器、Lazy与钩子

Sequential.append、ModuleList的append/extend/insert、ModuleDict的clear/items/keys/pop/update/values、ParameterList的append/extend，以及ParameterDict的clear/copy/fromkeys/get/items/keys/pop/popitem/setdefault/update/values，相关self条目均列FP32。容器支持不独自保证其中全部子模块、混合dtype、设备与图模式兼容。

UninitializedParameter及cls_to_become、UninitializedBuffer只列产品，LazyModuleMixin的has_uninitialized_params/initialize_parameters列self为FP32。parameter.is_lazy仅在同提交2.11..2.14四页收录，不据旧页缺项推定实际包绝对不可用。

Module自身的前后向、load/state_dict前后钩子与register_buffer/register_parameter均有产品条目；全局register_module_forward_pre_hook/forward_hook/backward_hook/full_backward_pre_hook/full_backward_hook以及buffer/module/parameter_registration_hook也列三类产品。钩子可注册不证明回调中任意Python、通信或副作用能被完整捕获。stateless.functional_call同样只列支持，参数替换、别名、mutation与动态控制流仍需独立核对。

Identity条目仅列input FP32，不由“恒等”名称把它的类型集合扩为所有输入；这类笼统表述同样按条目和实际路径保留边界。

## 验收

固定方法、真实参数/Buffer、dtype、设备及前后向，检查状态加载、Lazy物化、Hook与编译后图，再比较数值和性能。支持表与代码实例存在差异时保存两者，不用全局强制转换掩盖问题。

## 参数转换与状态辅助清单

同提交中英文七版本torch.__future__页对set/get_overwrite_module_params_on_conversion与set/get_swap_module_params_on_conversion列三类产品支持，但没有给出开关默认值、优先级或对优化器引用的完整规则。参数对象身份、别名和已有优化器状态应独立核对，不能由“支持”推定交换/覆盖不会影响已构造的优化器。

Serialization semantics页只列torch.serialization.clear_safe_globals的三类产品支持；不是完整的序列化、weights_only、可信加载或跨版本检查点合同。本文未加载任何检查点。torch.nn.modules.utils.consume_prefix_in_state_dict_if_present仅在同提交2.13/2.14中文Aliases页收录，列三类产品；不由名字推断所有键、metadata或原地修改参数都已在表中给出。

## 英文表的独立方法限制与NPU补丁

以上dtype表和未列限制的说明以中文页为起点；英文七版本又给register_backward_hook/register_buffer/register_forward_hook/register_forward_pre_hook/register_full_backward_hook/register_full_backward_pre_hook/register_load_state_dict_post_hook/register_module列self仅FP32，load_state_dict/modules在英文七版本也均列self FP32。不能用中文省略项取消英文局部限制，更不从self表强制转换所有模型参数。

register_state_dict_pre_hook在中文七版本列950DT支持，英文七版本明确950DT不支持；保留两侧表与具体方法，不用全局state_dict钩子支持覆盖。英文还对ipu/share_memory/npu三个方法明确三类产品均不支持，中文没有独立条目；xpu的“NPU形式为npu”说明不能自动解释这些独立产品表。

同提交utils/_module.py却实际定义npu，_apply_module_patch把它安装到torch.nn.Module；api_patches经PatchManager的api组调用该补丁，包初始化调用_apply_all_patches。函数用_apply逐Tensor调用t.npu，且注释提醒迁移可能改变参数/Buffer对象，应在构造优化器前考虑参数身份。这是静态接入证据，与英文npu全不支持标记并列保存，不由Python安装路径推导各产品、dtype或设备调用必然成功。

英文2.9/2.10/2.14对state_dict提示destination/prefix/keep_vars的位置参数形式已弃用，改用关键字；同三页对stateless.functional_call提示迁移到torch.func.functional_call。其余英文版本和中文未重复这些Version Notes，不把未写提示当作弃用撤销，也不宣称本文已经运行迁移。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md)（primary）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-__future__.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-__future__.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-__future__.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-__future__.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-__future__.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-__future__.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-__future__.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-__future__.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-__future__.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-__future__.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-__future__.md)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-__future__.md)（primary）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-__future__.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-__future__.md)（constraint）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/Serialization-semantics.md)（constraint）

- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/Serialization-semantics.md)（constraint）

- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/Serialization-semantics.md)（constraint）

- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/Serialization-semantics.md)（constraint）

- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/Serialization-semantics.md)（constraint）

- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/Serialization-semantics.md)（constraint）

- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/Serialization-semantics.md)（constraint）

- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Serialization-semantics.md)（constraint）

- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Serialization-semantics.md)（constraint）

- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Serialization-semantics.md)（constraint）

- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/Serialization-semantics.md)（constraint）

- [固定来源 33](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/Serialization-semantics.md)（primary）

- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Serialization-semantics.md)（constraint）

- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Serialization-semantics.md)（constraint）

- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-aliases.md)（constraint）

- [固定来源 37](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-aliases.md)（primary）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_module.py)（implementation）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/api_patches.py)（implementation）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/patch_manager.py)（implementation）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/__init__.py)（implementation）
