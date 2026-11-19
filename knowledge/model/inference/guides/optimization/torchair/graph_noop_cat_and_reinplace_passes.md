---
type: Guide
title: 图变换的存储语义：Noop、Cat与view原地恢复
description: 保留文档平台范围，补完整独立包Cat预分配和三目标view原地恢复的源码条件与版本门控。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/remove_noop_ops.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/remove_noop_ops.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/remove_cat_ops.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/inplace_pass.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/inplace_pass.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/remove_cat_ops.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/remove_noop_ops.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/npugraph_ex/compile_fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/remove_noop_ops.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/_recover_view_inplace_pattern.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/cat_optimization.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/_recover_view_inplace_pattern.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/cat_optimization.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/npugraphex_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/core/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/core/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/graph_transform_observer.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/graph_transform_observer.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/remove_noop_ops.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/remove_noop_ops.md
  role: constraint
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 图变换的存储语义：Noop 消除、Cat 与重新原地化

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。本卡选取来源支持的 A2/A3 推理范围，其他产品和特殊参数另行核对。

## 冗余与别名

GE 的 experimental_config.remove_noop_ops 和 npugraph_ex 的 options.remove_noop_ops 默认 True，依赖 PyTorch≥2.2，支持集随版本变化。完整 slice、repeat 全 1、零 padding、无变化 cast 等可能消除；列出 clone/alias/view 的名字不表示每次都可删除，输入输出 shape 和新引入的别名关系必须保持。

## Cat 消除

npugraph_ex 的 remove_cat_ops 默认 True，只针对 aten.cat.default、dim=0；各输入非拼接维度相同，生产算子须有 .out 变体，且这些输入不能同时供其他 cat 使用。其机制是预分配输出、slice 后让生产者原地写入，不能推广成任何 cat 都零拷贝。

## 重新原地化

inplace_pass 面向图中间节点的 out-of-place→in-place；input_inplace_pass 面向输入 mutation，将 Functionalize 产生的 out-of-place+copy_ 恢复为原地操作，默认均 True。

该发布文档对多输入原地算子只列出 npu_kv_rmsnorm_rope_cache_v2、npu_mla_prolog_v3、npu_add_rms_norm_v2，并标记第一个为实验接口、暂不支持商用。不要从普通单原地转换推导任意自定义多原地算子自动支持。compile_fx 自定义后端还不支持 input_inplace_pass。

## 定位顺序

保存原始和优化 FX，逐项关闭相关 Pass，核对消费者、输入是否被改写、输出是否共享存储和多次调用结果；节点变少不等于语义保持，也不自动证明性能改善。

- [低层 compile_fx 的能力边界](../../../apis/torchair/npugraph_ex_compile_fx.md)
- [自定义 mutation 的交付](../../integration/torchair/custom_operator_graph_contract.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线原地化与低层后端的变化

TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的Noop、Cat和inplace页保留上述各自开关与匹配条件，产品范围按主线总览包括A2/A3/950；并不是任意clone、view或cat均可删除。多输入mutation白名单仍只有列出的三个接口，其中kv_rmsnorm_rope_cache_v2仍是暂不用于生产的实验接口。

与发布段不同，主线compile_fx文档将input_inplace_pass改为有条件使用：自定义AOT后端需配合aot_module_simplified(keep_inference_input_mutations=True)。这只补齐AOT输入mutation保存条件，不扩展低层入口对多流表达和限核的支持；示例里如果没有该参数，也不能当作已满足条件的输入原地化配方。

Cat消除需生产者具备.out变体，不把文档将其称为“原地变体”理解成所有下划线算子均可替代.out；输出预分配、slice写入与alias仍要逐项核对。来源中的示意FX文本也不是可直接运行的验证结果。

## 主线GE Noop文档与实际跳过条件

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的GE Noop页与发布页正文相同，与npugraph_ex选项分开消费。

GE remove_noop_ops默认True，文档依赖PyTorch≥2.2，2.5.1只是示例规则集；实现从torch._inductor.fx_passes.post_grad导入，缺失时Warning并跳过，开关True不证明实际执行。完整切片、repeat全1、padding全0、同dtype/device转换、整型ceil/floor/round/trunc、pow1、单Tensor cat等仅在对应条件下可能冗余；view/copy/alias/clone列在名单不表示可无条件删除。

文档明确输入/输出shape不一致，或改写引入新的别名关系时不消除。自定义Pass也必须保留别名、修改写回和消费者语义；不能为了减少节点数破坏这些关系。用Noop阶段前后FX图核对实际变化，再量化稳态开销，未执行上游优化或性能实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/remove_noop_ops.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/remove_noop_ops.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/remove_cat_ops.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/inplace_pass.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/inplace_pass.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/remove_cat_ops.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/remove_noop_ops.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/npugraph_ex/compile_fx.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/remove_noop_ops.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）

## Cat预分配的完整独立包实现

完整读取独立npugraph_ex两版cat_optimization.py及_recover_view_inplace_pattern.py，追加的是准确源码静态合同。原文文档平台/生命周期保留，不将局部Python检查升级为新的硬件认证；未运行Pass、编译或设备。

Cat只收集aten.cat.default。验证至少2个call_function生产者、cat与输入有val、dim为原生int且等于0、输入秩和非拼接维度一致，以及每个生产者具有可选.out。另拒绝生产者供原快照中其他cat使用，但不拒绝全部非cat用户，也不独立验证所有dtype、device、stride、重叠或执行scope。bool False也满足该局部int==0条件，不能把这里写成严格type(dim)为int。

_get_out_variant按packet遍历带名为out参数的overload，比较除out之外的有序参数名和类型；不在此比较所有默认值、kw-only、mutability或返回类型。找不到原schema时只取packet.out。该匹配条件不同于名字带下划线，更不证明任意out实现完整语义等价。

输出在最早生产者之前按cat输出Meta的dtype/device/shape申请empty，pin_memory=False、memory_format=None；符号shape仅从符号placeholder表经外部construct_fx_node_shape处理。各输入第0维不能解析时跳过，前面已插入的形状节点没有通用事务回滚。Cat有stream标签才为申请插入scope enter/exit，主线target为npugraph_ex，发布为air；未逐个证明所有生产者与cat同流。

逐项建立dim0 slice、以原args和kwargs加out构造新生产者并复制Meta，之后将原生产者的所有uses替换、cat uses改为预申请输出；重复生产者在replacement dict按最后一次同key记录。只删除已无users的旧节点、清其Meta；有成功优化才lint/recompile。它可能改变其他用户看到的存储别名，不能从节点数减少推出任意后续mutation都正确。

真实调用点另绑定fx2acl_converter指定范围：主线读取平铺remove_cat_ops并委托本地Pass驱动，发布从debug.aclgraph.remove_cat_ops读取并直接调用后dump；本卡只对账该调用区间，不据此关闭整个转换器或条件图驱动。

## view到原地恢复的三目标与版本门控

本文件导入时按目标可见性登记scatter_update、npu_scatter_nd_update、npu_quant_scatter到相应下划线版本，输出0映到引用输入0；没有为随后新增模块自动重建表。候选copy_须恰2个位置实参、目标为placeholder、来源非placeholder，且两端val.size相等；没有独立dtype/device/stride/完整alias检查。

完整结构须为同一placeholder→pre_view→受登记非原地算子→post_view→copy_回placeholder，pre_view只有1个user、placeholder只有2个user；post_view和非原地结果可另有消费者。CANN helper要求≥8.3.RC1，任何异常返回False而跳过Pass；日志说skip version check不等于无条件继续。注释说明该门槛与既往格式传播问题有关，本次没有复现或认证所有产品。

通过后在原算子之后插入下划线节点、保留args/kwargs，replace_all_uses_with并传播Meta；copy_无user才删除，否则保留，旧非原地节点删除。日志实参读取config.mode.value，所以出现匹配时不能把默认config=None当作通用安全调用。正常到末尾会lint/recompile，没有覆盖中途异常的整图回滚。它与文档中的整个input_inplace_pass、多输入mutation白名单是不同层次，不能仅从这3目标扩大支持集合。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/_recover_view_inplace_pattern.py)（implementation）：1–273。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/cat_optimization.py)（implementation）：1–242。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/_recover_view_inplace_pattern.py)（implementation）：1–223。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/cat_optimization.py)（implementation）：1–253。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：320–382。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：315–355。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：300–330。
- [固定实现 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：230–248。


## 独立包Noop包装器的两版配置面与debug目录命名

独立 npugraph_ex 两固定版的 Noop 消除不是页内自实现：`_optimize_noop_ops` 从 `torch._inductor.fx_passes.post_grad` 导入 `remove_noop_ops`（主线 52–54、发布 30–32，try/except 守卫），导入失败置 None，Pass 应用时打「check if your PyTorch version is above 2.2.0 …」告警并跳过——与集成侧同一守卫形态，但行锚在独立包 npu_fx_compiler.py：主线 392–398、发布 332–338，装饰器 pass_name 为 optimize_noop_ops，调用点在 pre→noop→recover→pattern→view→post 顺序中段（主线 357–358、发布 312–313）。开关读取路径两版分家：主线读平铺 `config.remove_noop_ops`（compiler_config.py 43，默认 True），发布读嵌套 `config.experimental_config.remove_noop_ops`（npugraphex_config.py 44 的 OPTIONS_TO_CONFIG_MAP 把平铺名译进 experimental_config，experimental_config.py 17 默认 True）；默认值相同、键路径不同，不能把一版 options 字典直接塞进另一版。

两版 remove_noop_ops 页的行级差异只有一处实质：发布版在 aten.slice 行尾追加了「当算子的输入/输出Shape不一致，或优化后在输入/输出间引入了新的别名关系时，不会进行冗余消除操作」一句，主线 npugraph_ex 页该行没有此句（同一约束的主线表述在 GE Noop 页正文，见前文）；该句本身与本卡既有别名/shape 守卫一致，不构成新的行为承诺。另两页承诺的 Debug 落点各自与实现一致：主线写「Debug信息的npugraph_ex目录」、发布写「torchair目录」，对应各自独立包 core/utils.py `_create_debug_log_paths` 的目录名（主线 18 "npugraph_ex"、发布 16 "torchair"）与 graph_transform_observer 的图转储目录（主线 97/99、发布 91）——是各 pin 内文档与实现配对成立，不是任一版文档写错；跨版本目录名通用化已由[独立包设计合同](npugraph_ex_standalone_design_contracts.md)排除。

## 补充来源

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：27–54（导入守卫）、345–375（Pass 顺序窗口）、392–398（包装器）。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：27–34、305–330、332–338。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py)（implementation）：43、183–210（_process_kwargs_options 白名单）。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/npugraphex_config.py)（implementation）：18、44、104–123。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/experimental_config.py)（implementation）：17、25。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/core/utils.py)（implementation）：14–18。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/core/utils.py)（implementation）：12–22（发布急切初始化副本）。
- [固定实现 8](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/graph_transform_observer.py)（implementation）：91–101。
- [固定实现 9](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/graph_transform_observer.py)（implementation）：85–93。
- [固定约束 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/remove_noop_ops.md)（constraint）：1–74 全文复核；行 16 与行 64。
- [固定约束 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/remove_noop_ops.md)（constraint）：1–74 全文复核；行 16 行尾追加句、行 64 目录名。
