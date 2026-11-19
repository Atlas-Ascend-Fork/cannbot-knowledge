---
type: Guide
title: 独立npugraph_ex原地化：别名、回写与多流检查
description: 完整区分输入回写与中间Tensor两条原地化算法，说明Meta、Storage、用户收集、版本流检查与失败后状态。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/c10d_functional.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/c10d_functional.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-11T06:33:53Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 独立npugraph_ex原地化：别名、回写与多流检查

## 固定版本和两条算法

本卡完整审阅独立包两版graph_pass.py、utils.py及c10d_functional.py的本地定义：主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c、发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013。没有执行MetadataProp、FakeTensor、图改写、通信或设备。平台未知，保持draft与空平台。普通TorchAir和[Cat/view规则](graph_noop_cat_and_reinplace_passes.md)按各自来源消费。

输入mutation回写优化与中间Tensor原地化是两条不同算法，不能互相借用全部守卫。前者允许有copy_回写语义的placeholder/get_attr进入候选，后者用placeholder FakeTensor Storage集合阻止输入原地修改；中间算法也没有给get_attr建立同一输入集合。它们调用的Torch私有别名工具及设备实现不因本地文件读完而闭合。

## 注册表和Storage身份

InplaceableNpuOp是frozen dataclass，保存inplace_op、mutated_arg列表和extra_check（缺省lambda True）；frozen不深冻结列表。register先核两个名字是否存在，再取各自.default或原packet，二者非None才写全局表，没有额外验证所有Schema或索引。两版三项配置相同：kv_rmsnorm_rope_cache_v2的功能版修改5/6，mla_prolog_v3功能版修改9/10，add_rms_norm_v2功能版修改0/1。

get_storage按untyped_storage()._cdata判Storage对象身份；get_node_storage只对meta['val']为Tensor且_has_storage成功的节点给出身份，否则None。它没有用Tensor逻辑起始地址认证所有视图不重叠。META_ONLY_OPS精确包含sym_size、sym_stride、sym_numel、sym_storage_offset；工具可选导入失败会留下None，不能据一个总开关假定所有调用点都安全降级。

## 输入回写要保留可观察的别名使用

_mutated_input_reinplace反向扫描建立节点顺序、Storage到节点表，以及写向placeholder/get_attr的copy_回写表。已知多输出算子的getitem源在配对键中折回算子；相同目的或配对反向覆盖后保留较早的copy。只有存在相应回写，且候选与回写之间没有不允许的后续别名使用，才允许修改输入。原地候选之后、回写之前的普通用户会阻止；仅元数据使用可递归检查，同一目的的覆盖copy有专门豁免。

列表参数先要求Storage身份不同再逐项检查；缺Storage拒绝。可能重叠的视图才进入观察检查，_overlap工具缺失或遇到GuardOnDataDependentSymNode按可能重叠处理；不是吞掉所有异常。中间值还不能与placeholder/get_attr视图共享被检查的Storage。此处是图内Meta与别名分析，不是运行时完整别名证明。

已知多输入可变算子要求每个被改参数都有对应copy回写，随后合并can_inplace与extra_check；成功才换target并重连copy/getitem。普通候选使用第一个参数、_maybe_get_inplace_op与single流检查；主线还排除placeholder/get_attr节点进入该普通分支，发布没有这项局部op过滤。

auto_functionalized_v2按_all_bases的枚举索引记录only_clone_these_tensors，旧auto_functionalized按get_mutable_args参数名处理并去掉值为None的项。can_inplace与流检查通过后可以省克隆，但已被本次原地化的同Storage参数会保留另一路克隆；不把它推广成任意容器/别名去重保证。替换字典逐链解析，再重连用户并删旧节点；本helper注解为GraphModule却没有显式return，上层忽略它的返回值。

ReinplaceCounters只在numel与element_size均为Python int时估算字节，动态值不因此获得真实节省量。计数器和导入的私有工具没有每个使用点各自完整的None保护，也没有设备复制量或性能测量。

## 中间原地化的实际检查比注释窄

reinplace_with_multi_stream_check先委托外部MetadataProp.propagate，再用FakeTensor叶子建立StorageWeakRef别名表。已知多输入算子检查索引范围，假设修改后参数位于输出的末尾，并调用extra_check；普通OpOverload要求第一个Schema参数的type精确为TensorType，然后检查实参0。

普通分支只在两边展平叶子数相等时逐项比较numel、dtype及_debug_has_internal_overlap==1；源码没有像注释所说另逐项比较size/stride，叶子数量不等也没有在这一处直接标错。resize有豁免，完全相同self Node在顶层位置参数出现多次则拒绝。随后拒绝输入Storage，并要求后续别名使用仅属于可消去的inverse-view用途。

自定义多输入分支跳过上述普通metadata、重复self及后续使用检查，仍保留索引、输入Storage和流检查；不能由普通分支的守卫推成它也验证了任意多输入Schema或所有可变实参互不别名。

view_scatter可改成对应view加copy_，其它候选换原地target；输出Storage按末尾输出映射（否则用首输出）与输入Storage合并。后续node_idx更大的用户在args和kwargs中都重定向；视图别名集合再更新，inverse-view节点最后统一删除，随后recompile。没有在此重新执行完整数值、FakeTensor结果、通用别名分析或graph.lint。

## 两版流检查的保证不同

utils的用户收集只看直接非copy用户、最后遇到的copy及相关getitem/copy用户，不是所有视图的传递闭包，也不承诺去重。多输出按输出尾部位置与修改实参映射；输出映射计算异常时退为空字典；索引仅在idx≥len(args)时警告跳过，负索引没有在每条路径独立拒绝。checker以zip将索引和用户列表配对，不能据此认证两者总是等长。

主线ReinplaceStreamChecker把原地节点及所收集用户交给[图元数据的事件路径分析](npugraph_ex_standalone_design_contracts.md)：按图位置检查跨流event保护。发布仅调用verify_nodes_on_same_stream(users)，没有把当前原地节点放入该列表；少于两个用户时该helper直接True。因此发布局部True不能改写成“原地节点与全部用户一定同流”。单输入、三项多输入表及auto-functionalization分别取各自修改参数，但都依赖这些实际用户收集范围。

## 包装、版本条件与失败后状态

_reinplace_inplaceable_ops_pass先添加stream标签，内部工具不可用则告警返回original_gm；multi_stream_enabled形参没有在函数体用于关闭这些流检查。NotImplementedError直接抛出；其它异常直接判断torch.__version__ < '2.5.0'，条件成立时抛带升级/关闭配置建议的RuntimeError，否则告警返回original_gm。本地没有强制转str，实际比较语义由所加载版本对象实现决定。主线消息写config.inplace_pass=False，发布消息写旧experimental debug路径，不拿消息文字替代配置消费者证据。

original_gm=gm只是同一对象引用，返回它不是事务回滚，不能承诺异常前的部分改图已撤销。输入mutation包装也先标流，但没有同一try/except。主线eliminate_self_copy只删copy_(x,x)中args[0] is args[1]且无用户的节点，不按一般地址/别名等价删除；本helper不lint或recompile，调用者负责后续生成。

## all-to-all分解只是一座本地桥

两版c10d_functional完整AST相同；仅在直接比较torch.__version__ >= '2.3.1'成立时定义decomp_c10d_functional_all_to_all_single；右侧字符串字面量不意味着左侧对象采用普通字符串比较。它从group_name解析ProcessGroup，再取rank列表和group tag，将input、output/input split sizes、tag、ranks、len(ranks)传给_all_to_all_single。这里没有独立split/rank合法性检查，也没有在本文件完成注册或证明同步、异步、通信正确性；外部HCOM实现仍独立。

## 完整本地源码证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py)（primary）：1–1631；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/c10d_functional.py)（implementation）：1–20；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：1–545；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py)（implementation）：1–1441；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/c10d_functional.py)（implementation）：1–24；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：1–506；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
