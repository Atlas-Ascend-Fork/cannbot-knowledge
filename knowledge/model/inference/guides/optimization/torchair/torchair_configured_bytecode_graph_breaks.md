---
type: Guide
title: 配置驱动的graph break：字节码补丁与生命周期
description: 按字节码hook说明配置解析、栈识别、共享处理器替换和环境配置生效时点。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/__init__.py
  role: implementation
created_at: '2026-11-12T02:09:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 配置驱动的graph break：字节码补丁与生命周期

BREAK_GRAPH_OP_LIST在add_npu_patch安装阶段读取，决定是否替换Dynamo InstructionTranslatorBase的三个字节码处理器。它控制编译图边界，既不移除底层算子实现，也不保证带同名操作的所有图都会按语义识别命中。两固定版所列本地逻辑相同，未执行字节码或模型。

| 名称 | 检查范围 |
| --- | --- |
| SLICE | self.stack[1]为TupleVariable，且as_proxy()中的元素出现slice时抛Unsupported；没有概括所有getitem写法 |
| SETITEM | 对应hook无条件抛Unsupported |
| NN.CONV3D | 仅stack[0]是NNModuleVariable且module_type精确等于torch.nn.Conv3d |
| NN.LINEAR | 扫描整个stack中NNModuleVariable，module_type精确等于torch.nn.Linear |

环境值为空/不存在时返回；否则按逗号拆分并upper，不strip空白。未知名称或尾逗号产生的空项会报错；名称验证全部完成后才调用add_break_graph，不能把带空格的自由文本当有效配置。

add_break_graph给BINARY_SUBSCR、STORE_SUBSCR、CALL_FUNCTION各建带break_graph_if_unsupported的wrapper，按已配置的hook检查后继续原有对应栈操作。store_subscr还把结果guards加入self.output.guards。它直接给共享InstructionTranslatorBase类赋值，没有保存原处理器或提供撤销函数；修改环境为无值不会把已装的处理器自动恢复。

外层add_npu_patch的run_once只标记首次完整成功调用，见[Meta补丁生命周期](torchair_meta_fake_tensor_and_global_patch_lifecycle.md)。因此环境通常在这次安装时形成闭包配置，之后仅修改BREAK_GRAPH_OP_LIST不表示每张图都会重新读取；失败重试也不等于事务回滚。源码依赖私有字节码栈形态，不用这些字符串推导所有PyTorch版本适配。

## 实现来源

- [固定实现1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/__init__.py)：1–22、74–82、157–283、454–462。
- [固定实现2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/__init__.py)：1–22、72–80、155–279、444–452。
