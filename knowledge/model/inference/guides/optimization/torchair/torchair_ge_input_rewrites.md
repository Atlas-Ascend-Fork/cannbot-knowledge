---
type: Guide
title: GE输入重写：SymPack、RefData与权重占位
description: 说明两版GE符号输入合并、导出命名、RefData对象身份、固定权重占位和死输入重排的绑定条件。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/graph_pass.py
  role: implementation
created_at: '2026-11-10T10:53:20Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE输入重写：SymPack、RefData与权重占位

## 固定版本与证据范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的graph_pass.py。本卡解释符号输入合并、RefData、固定权重占位及死输入重排，产品范围未知，保持draft与空平台；未运行上游、改模型图或执行设备实验。

## SymPack变为新的host输入

optimize_sym_pack只识别input_desc[0].device_type为CPU的Data，以及_inputs_all_sym=True且axis=0的Pack；Pack每条输入必须来自所收集host Data。相同有序输入边的Pack复用一个新Data，比较键没有额外包含所有属性或输出dtype。

新Data的shape与real_shape为[Pack输入数]，dtype取首个Pack输入描述并转换，placement=CPU，index=graph.num_inputs；记录_GeInputInfo与_SymPackInput(原输入索引列表)。然后移除Pack并统一重写消费者边；这是把符号打包转成输入绑定，不是在设备上执行了Pack或求得任意符号表达式。

主线导出上下文额外收集Data名称，删除只被这些Pack使用的原Data及相应输入登记，尝试由公共基名去数字后缀生成合并名，冲突时追加递增后缀；仍有其他消费者的Data保留。发布没有这套导出名称回收，node_name为None。名称稳定性和最终输入签名须按版本验收。

## RefData身份来自输入对象及布局

replace_data_to_refdata只处理ref_input_idx指定的Data，按真实输入shape、stride、storage_offset及id(input_tensor)合成RefData名字；按graph.name与进程级_GLOBAL_NAME_MAP查重，首次记录_origin_data_name并重命名/改类型，再重写输入边，重复时仅警告。

id是当前Python对象身份，不是数据地址、内容哈希或跨进程稳定身份；本模块没有清空该全局名字表的步骤。把Data改为RefData不等于已验证生命周期、跨进程缓存或所有别名关系。

## 固定权重先放假ConstPlaceHolder

get_frozen_flag仅对value_type为PARAMETER或STATIC_TENSOR、func为_TensorInput且device_type=NPU的输入标1。不是所有Tensor、参数或固定shape输入都自动冻结。

frozen_data_by_constplaceholder为相应Data新建ConstPlaceHolder，初始shape为空、format=2、dtype=0、addr=0、size=4，并设置update_node_from_fx_input_idx；有Meta再set_meta。初值是占位而非真实权重地址或常量内容，函数只改消费者边，旧Data的移除还依赖后续处理，不能据此宣称权重已经写入图常量。

## 死输入删除与索引重排

remove_dead_data_and_reorder_data_index只统计Data的普通tensor边引用；引用为0就移除Data、删其控制边及named_inputs_info。保留Data按图中遍历次序重排index并收集已登记输入信息，缺登记则AssertionError。RefData不是这个Data统计分支的同义项。

这个计数会看Cmo输入，而引用复制优化中的Data消费者计数特别排除Cmo，两者不能互用。函数也没有回滚此前删除/改索引操作的事务；调用后须核对实际runtime输入列表与新索引对应关系。

## 验证与关联

比较优化前后Data/RefData/Pack、每个输入getter、符号打包顺序、命名冲突、frozen标记与占位更新，以及删除后输入数量/索引。只有完整执行器结合这些信息才能建立正确输入绑定；本次没有运行模型或缓存复用实验。

- [元数据与Data位置描述](torchair_ge_metadata_support_helpers.md)
- [FX编译与输入静态标记](torchair_fx_compiler_pipeline.md)
- [引用复制与副作用排序](torchair_ge_reference_copy_and_ordering.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/graph_pass.py)（implementation）
