---
type: Guide
title: GE图对象：上下文、输入登记与执行委托
description: 核对两版GeGraph所有权、默认图和名称、进程组记录恢复结构、输入getter及RNG与代码生成阶段的差异。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
created_at: '2026-11-10T12:57:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE图对象：上下文、输入登记与执行委托

## 固定版本与范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的ge/_ge_graph.py。此前只覆盖局部函数的两份文件在本次补齐全文；本卡限定Python图描述与调用合同，不替代原生执行器、kernel和完整设备能力。产品矩阵未知，保持draft与空平台；未导入上游、构造/反序列化图、生成或执行代码、读设备数据或做性能实验。

## 图构造与执行委托

GeGraph可新建ModelDef/graph，或接收model_def，或从serialized_model_def解析首张图；后两参数同时给出拒绝。直接传model_def时保留对象引用，并可改其图名，不是自动深拷贝。这里只读源码，本次没有解析任何模型或缓存。

构造会创建TorchNpuGraph执行器；SerializeToString序列化整个model，__str__和__getattr__主要面向首图proto。load、compile、run和auto_tune委托执行器，不在这些薄包装里完成完整设备/内存/性能验证；也不能把取得默认图说成一定是无需底层扩展的纯离线操作。

## 默认图和名称登记

_GeGraphStack继承threading.local，每线程有栈和默认图；空栈首次懒建GeGraph。上下文进入append、退出remove对应对象，default_ge_graph包装在finally移除；它不是任意共享图对象的多线程锁，也不应由global字样误读成所有线程共用一个默认图。

next_unique_name在登记表为空时从现有proto取名字，显式空名/重复名拒绝，无名按op类型递增后缀。它维护额外list和计数，直接手工改proto后不保证该登记自动同步。

record_input拒绝重复索引；record_input_info重复名字只警告后覆盖；num_inputs是已登记索引数量，不是直接扫描所有Data的结果。图输入变换后还需按[输入重写](torchair_ge_input_rewrites.md)核对实际getter、数量和顺序。

## 进程组记录与恢复的结构边界

record_process_group保存group_name到(rank_list,tag)对，set_used_process_group可直接替换整份字典。load(create_pg=True)且记录非空时，扫描已有HCCL组，再按图节点group属性查记录，必要时_find_or_create_pg_by_ranks_and_tag并重写group名称，之后执行器load。

需保留静态格式疑点：这段load把字典值直接当rank_list并取len，记录方法却存二元对；外部set_used_process_group是否预先提供另一结构必须追调用方，不能只连看两个方法就认证自动恢复任意子组成功。默认create_pg=False，也不能由保存了元数据推导已创建组或做过通信同步。

## 图RNG与输入getter的不同阶段

图RNG按Generator键懒建状态，种子成为Const，offset列表成为CPU Data/Unpack，调用时consume推进offset；显式Generator键未传factory的静态边界已在[RNG与Dropout](torchair_ge_rng_dropout_lowering.md)记录，本卡不重新解释为已验证的独立Generator支持。未导入TorchNPU的分支还调用torch.manual_seed(10)，不是没有状态副作用的通用CPU回退。

_TensorInput原样取输入，_DiscontiguousTensorInput显式contiguous；_ValueInput取值后torch.tensor，而codegen用numpy.array([value])再from_numpy，源码形状构造并不相同。_SymPackInput按既定索引取标量列表，codegen另生成插入表达式；_RngStatusInput实际consume，而其codegen插None占位。不能从同名getter/代码片段推定两条执行路线无需外围补齐即可等价。

_GeInputInfo保存value_type、func、shape、device_type、real_shape和dim_gears；这些登记不是实际输入Tensor已按规格变换或运行guard已经全部通过。

## 图输出保留与诊断代码

dont_prune_me仅追加列表，must_keep_ops暴露该列表；具体后续消费者如何接入NetOutput仍须另证，不等于当前已避免裁剪。python_code累计来自add_python_code的文本，基础imports、输入格式化及节点名可读表达不构成完整、无损、可独立执行的序列化保证。

核对图所有权、上下文/名称登记、输入信息、通信记录结构、RNG状态及实际调用执行器的阶段，再在匹配栈验证运行与性能。本次没有构造图、编译、创建进程组或运行设备。

- [通信图与进程组元数据](torchair_ge_collective_lowering.md)
- [FX编译管线](torchair_fx_compiler_pipeline.md)
- [常量和诊断代码生成](torchair_ge_primitive_const_promotion.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）
