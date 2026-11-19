---
type: Guide
title: 条件图编译门控：分支Pass、函数化解包与别名检查
description: 核对独立npugraph_ex中cond包装识别、输入原地开关下的解包、变换后别名门控与生成代码结构检查。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/cond_utils.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
created_at: '2026-11-10T13:59:10Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 条件图编译门控：分支Pass、函数化解包与别名检查

## 范围与前置依赖

本卡只绑定TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`的`npugraph_ex/npugraph_ex/`独立编译路径。公开版本、平台、分支输出与嵌套mutation限制沿用[条件捕获文档](npugraph_ex_conditional_capture.md)，这里补齐真实编译消费者，不外推发布版或同仓集成TorchAir。整卡平台未知，保持draft、空平台；未执行上游或编译模型。

检测不只识别裸higher_order.cond，还识别auto_functionalized/auto_functionalized_v2中第一个参数为cond的包装，并递归检查GraphModule子图。发现cond后先load_cond_dependencies：要求torch_npu条件节点warmup/capture分派接口，以及torch的input alias/mutation分析函数；缺接口立即报错，不通过跳过别名分析来降级。成功结果保存在模块级_COND_DEPS，不是每次重新探测运行库兼容性。

## 分支也要经过图变换

iter_cond_gm_tree只沿cond引用的true/false分支后序遍历，最深子图先于父图；没有cond只返回root。它不等于对while_loop/scan等所有高阶子图都启用同一套Pass。裸cond通过args[1:3]找get_attr，包装形式通过kwargs中的true_fn/false_fn找分支，不能仅移动一个args偏移来识别包装。

优化器对子分支取placeholder的meta值，优先val，其次example_value；任一缺失就返回None并报具体子图路径，不能盲用root输入样例。前后自定义Pass、pattern等仍受实际配置控制；Converter自己的local Pass驱动也遍历cond分支，对变更后的子图lint/recompile。没有在本卡证明所有Pass或上游元数据生产都正确。

## 关闭输入原地Pass也须解开cond包装

input_inplace_pass=True路线先做输入mutation的reinplace，再在辅助函数可用时执行通用decompose_auto_functionalized。False路线仍专门运行decompose_cond_auto_functionalized，它只注册并解开包住cond的两个wrapper，保留其他wrapper。

专用解包将get_attr常量解析后用replace_by_example替换，给dense helper的第二个参数明确传None；不是传空元组。源码以此保留函数化语义，并说明两者clone含义不同，但本卡没有执行外部helper或测量拷贝，不能把关闭输入原地Pass理解成没有复制成本。解包后清理无用户get_attr和不再引用的GraphModule属性；仍有用户的target受保护，最后lint。

后续还递归检查残留wrapper，发现未解包cond就明确报内部错误，不把之后序列化失败误当作不相关缓存问题。该门控不能代替模型mutation正确性验证。

## 别名检查放在local Pass之后

validate_cond_graph在所有所列local Pass完成后调用，解析每个裸cond的两支GraphModule，并分别调用torch的alias/mutation helper。它要求返回长度5、第1号项为dict、第3号项为list，才按第1号项读取输入到输出的存储别名映射；遇到非空映射就拒绝该分支返回输入或其view，并给出输入/输出索引。

本地检查不禁止所有operand mutation，也不自己重新验证全部dtype/device/layout/shape合同。外部helper缺失或协议变化不被静默忽略；只有source检查通过，也不能据此保证全部运行时别名或嵌套副作用安全。返回clone与公共文档的嵌套mutation限制仍需分别核对。

## 生成代码还有一道结构检查

代码生成结束且_contains_cond为真时，validate_cond_codegen先AST解析生成文本，再递归构造每支应有的函数名，要求每个名字恰有一个定义。嵌套名字带父路径，避免不同GraphModule复用节点名造成冲突。它还检查形如true_graph_N/false_graph_N的变量是否被读取却从未写入。

这是所列模式的语法/结构检查，不是执行生成代码、完整变量支配分析、输出数值或存储语义验收。本次只读实现，没有调用这些Pass或执行生成文本。运行时双分支与统一输出缓冲见[条件节点运行链](npugraph_ex_cond_dispatch_and_output_buffers.md)，参数更新与key仍复用[任务更新规则](npugraph_ex_task_update_rules_and_graph_keys.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/cond_utils.py)（primary）：定向范围33–94, 112–261, 264–307, 319–479, 525–548, 628–695。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：定向范围314–388。
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：定向范围241–254, 264–321, 425–492, 527–541。

## scope结构门控按分支局部检查，不是所有Pass之后的验收

本节补独立npu_fx_compiler的_valid_graph及实际调用段，固定主线92e1e967与发布7c6c754。调用发生在通用_optimize_fx之后，随后save_fx_graph并由解释器构图；Converter自己的optimize_graph_without_runtime还在后面。所列调用段没有在这个后续优化结束后再次调用_valid_graph，因此不能把它概括成“所有本地Pass改写后的最终scope验收”，也不能替代前文后置的cond别名检查。

主线通过iter_cond_gm_tree检查root及所遍历的每个cond分支GraphModule，每个模块新建自己的scope栈/列表。子图RuntimeError会追加具体GraphModule路径；root的同类错误直接重抛。入口与出口分处root/child或不同分支，不能靠另一张子图的标记抵消本地残留。发布所列_valid_graph只对传入root调用一次局部检查，没有这条递归分支检查；这只是固定本地门控差异，不推断发布的其他模块或Runtime完全不检查scope。

两版识别普通scope所用的精确target字符串也不同：主线是npugraph_ex.scope_enter/exit.default，发布是air.scope_enter/exit.default。它们与[资源scope注册](npugraph_ex_core_limit_stream_targets_and_static_kernel_gate.md)的命名空间对应；这个验证器没有按任意相似Python名称通用匹配所有标记。

普通scope_enter入栈、scope_exit弹栈，空栈遇exit或最终仍有enter就抛错，但不在这里匹配attrs、scope名称或完整调用Schema。superkernel begin则进入另一列表，end取首个参数作名字（缺失时用None），从列表前方找第一个同名begin并移除。找不到或最终仍残留才报错；同名重复与跨次序关闭没有被改成严格后进先出，普通scope栈与superkernel列表也各自独立。

因此，校验成功只说明这些本地规则通过，不能据此宣称所有作用域都满足严格嵌套、缺失参数已合法化、跨流顺序已完成，或任意自定义Pass/条件模型都可安全捕获。排查graph break或分支捕获异常时，应保留固定命名空间、每个GraphModule的标记顺序、superkernel名字及修改发生阶段；没有运行验证器、Pass、条件模型或设备实验，也没有新增verified。

## 有界scope校验源码证据

- [固定检查 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：471–562、761–771；仅完整局部检查与实际调用段，不提升整个编译器或外部遍历/Runtime资格。
- [固定检查 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：395–459、634–646；仅完整局部检查与实际调用段，不提升整个编译器或外部遍历/Runtime资格。
