---
type: Guide
title: 实验Triton掩码索引：非负clamp的局部证明与省略条件
description: 说明适用门槛、四种模式、结构轴和AST下界提取、仿射检查及counter，区分局部省略和完整访存验收。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/provable_clamp.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
created_at: '2026-11-11T08:13:12Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton掩码索引：非负clamp的局部证明与省略条件

## 固定调用与收益范围

针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf实验Triton的provable_clamp.py完整本地模块及所列codegen/config调用段。没有导入SymPy/编译器、运行证明器、发射或执行设备kernel；未知平台保持draft和空平台。外部IndexingOptions、range-tree约定、掩码解引用语义与实际Triton降低仍独立。

消费者只有在_masked_index_needs_nonnegative_clamp(result,self)返回True时，将新索引字符串包成tl.maximum(index,0)。若索引/掩码/expand字段完全没变就复用原result，否则创建新的IndexingOptions并保留原result.index等信息。这个局部优化不删除mask，也不是把完整地址边界检查移走；源码注释描述省掉非仿射maximum可能避免部分标量化，不把注释中的示例倍数当本仓实测收益。

## 先有适用门槛，再谈证明是否成功

函数首先读取nonnegative_clamp_mode。off直接返回False；非IndexingOptions或没有tmpmask也直接False。然后展开index表达式，把全部free symbols替为0得到origin；只有origin是明确数值且为负才进入后续判断。origin分析抛所列AttributeError/TypeError/ValueError/ZeroDivisionError时同样返回False，而不是保留clamp。

因此“所有无法证明的情况都保留clamp”只适用于已经通过负origin门槛后的证明阶段，不能套到整个函数。局部早返回也不证明索引在所有实际lane上非负，完整地址安全仍需结合上游index和mask。

| mode | 负origin门槛成立后的实际行为 |
| --- | --- |
| provable | 有kernel时尝试解析已发射定义、提取mask下界并证明；成功计provable_skip并返回False。无有效证明则最终True。 |
| on | 不尝试证明，直接走最终True，保留clamp。 |
| log | 保留clamp，并把index/mask写counter；配置log_path非空时追加文件记录。 |
| off | 在所有前置分析之前返回False，完全跳过本地clamp。 |

config初值为provable、log_path=None；本地helper直接读实验config，运行态控制按该模块的patch协议核对。未知mode字符串没有在本helper抛枚举校验错误：通过负origin门槛后也会走最终True。log写文件不在证明器的except内，不能笼统说诊断I/O失败也不会影响codegen。

## 已发射定义与结构轴来源

_npu_body_defs从kernel.compute.get_lines_ref取得已生成的行；无该接口就空字典。逐行strip，忽略空行、注释和装饰器，单行AST解析失败跳过；只接受单条、单Name目标的Assign，用setdefault保留同名首次定义。它不把循环、跨行语句或多目标赋值自动补成完整控制流。

缓存tag仅为行数和最后一行字符串，相同即复用旧定义表；不是对全部行做内容哈希。核对缓存时需保留这个本地身份范围，不能宣称它追踪了任意早期行原地修改。

axis_names只来自kernel.range_tree_nodes的键转字符串，不从通用变量名字推导“这是轴”。缺失/为空时证明无法认出轴。mask候选则从indexing.mask_vars里仅取名字以tmp开头的项；这些名字用于找定义，不能取代结构轴身份。

## AST只识别有限下界语法

_npu_ast_eval识别整数常量、一元负常量、已知轴Name和已登记定义。若某Name定义里出现属性名为arange的调用，且该Name以结构轴名开头，就取最长匹配轴名；不能把任意未登记变量按前缀当轴。可识别full调用的整数第二实参，拆开broadcast_to首实参及.to的接收对象，其他表达式返回None，Name递归深度超过8也放弃。

这些调用按属性名识别，并没有在该helper校验对象一定是tl或.to是否保持取值。它依赖生成DSL的外部约定，不能直接作为任意Python/Triton AST的通用数学证明器。

_npu_mask_conj_atoms只沿位与&和已知Name定义递归，只接受单个>=比较，且左侧解析成轴、右侧为整数常量才贡献下界。同一轴取最大下界；上界<、或表达式及未知运算不会自动转成可用的下界。所有tmp mask的下界按轴再取最大值，未出现的轴下界在后续公式按0处理。

## 仿射检查与诊断的准确含义

_npu_index_provably_nonnegative展开expr并取系数字典，只允许常量项和结构轴Symbol；非原子项、TMP符号、轴集合之外的Symbol或负系数均失败。按常量加各系数乘已知下界的和判断>=0。实现用int(c)转换系数，没有单独检查任意输入的c.is_integer；这里保存生成整数索引语境中的局部算法，不把它推广成所有有理/浮点/非线性表达式证明。

主函数还要求lb非空才接受该证明。成功跳过记provable_skip；未能证明记provable_unproven；证明区内的任意Exception记prover_error后保留clamp。这些counter衡量局部决策路径，不衡量正确性、访存矢量化或性能是否已在设备验收。

排查clamp未省略时，可按顺序检查tmpmask与负origin门槛、kernel结构轴、已发射定义、可识别的>=下界、是否有TMP/负系数/非线性项，以及实际mode和counter。不能仅看到provable_skip就扩大为任意索引安全认证，也不能为追求注释所称收益直接用off替代缺失证明。

## 固定来源

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/provable_clamp.py)：1–247；完整本地证明器，外部约定另计。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)：4071–4088；仅所列有界内容。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)：99–111、471–471；仅所列有界内容。
