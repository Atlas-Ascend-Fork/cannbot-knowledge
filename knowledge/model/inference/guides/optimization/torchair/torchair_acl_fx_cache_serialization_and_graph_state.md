---
type: Guide
title: ACL缓存的FX图序列化：子模块状态与节点元数据边界
description: 对照独立与集成双版FX缓存，说明模块浅复制差异、节点元数据未显式保存、名称解析和追踪环境恢复。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph_cache_utils.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph_cache_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph_cache_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph_cache_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
created_at: '2026-11-11T07:39:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# ACL缓存的FX图序列化：子模块状态与节点元数据边界

## 固定包、版本与恢复阶段

审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013，区分独立npugraph_ex与集成python/torchair下各自的acl_graph_cache_utils.py。四个完整本地模块分别为192、190、190、190逻辑行；发布两个文件末尾无换行，不能用换行符数量189省略最后一行。

四个转换器所列消费者均在normalize_config、fx_graph.recompile后，把SerializableGraphModule(self.fx_graph).convert_to_bytes()存入_serialized_gm。生成的常量初始化代码内嵌这段bytes，调用rebuild_from_bytes，再取得包装的_artifact。这里恢复的是Python FX图及其模块状态，独立包后续仍按[恢复后的捕获键与首次调用](npugraph_ex_restored_capture_keys_and_first_call.md)建立捕获对象；不能把生成字符串或FX恢复成功当成已有可重放设备图。

没有导入这些模块、调用pickle、反序列化缓存、执行生成代码、建图或运行设备。产品范围未知，保持draft和空平台。四个转换器只引用所列有界调用段，其余函数和外部PyTorch实现没有据此闭合。

## 包装协议与临时关闭追踪

SerializableArtifact要求artifact可调用，保存原对象并直接转发__call__；若原对象_boxed_call为真，就把这个标记设到包装上，artifact属性返回同一底层对象。__reduce__给出rebuild_from_bytes与convert_to_bytes结果的重建协议，两个方法在基类仍为抽象方法。

基类__new__遇已有SerializableArtifact时返回该对象，基类__init__也有相应早返回；但SerializableGraphModule自己的__init__先检查输入是GraphModule。不能仅由基类的复用分支推定“把任意已包装对象再传给GraphModule包装器都被接受”。这只说明局部检查顺序，没有执行构造异常测试。

序列化和恢复都进入temp_disable_tracing_envs：持有compile_lock并进入_disable_current_modes。按所加载torch.__version__与2.5.1比较，低版本使用本模块创建的RLock及TracingContext.get；若存在上下文，把fake_mode暂设None，在finally恢复。较高版本导入Dynamo的compile_lock，经TracingContext.try_get与patch(fake_mode=None)或nullcontext运行。这里是Python追踪环境的临时处理，不是设备流同步或跨进程工件锁；相关外部上下文实现没有展开。

## 模块状态是浅复制，独立包有专门修订

serialize_fn先浅复制gm.__dict__，删除副本中的_graph；遇_modules里的GraphModule子项，再递归把它编码成三元组。

| 固定实现 | 替换子模块表项前的处理 |
| --- | --- |
| 主线独立npugraph_ex | 额外复制gm_dict['_modules']字典，再替换副本里的GraphModule项。递归子图同样经过这个函数。 |
| 主线集成python/torchair | 没有该字典复制；浅__dict__副本与原模块仍共享_modules字典。 |
| 两个发布包 | 完整文件逐字节相同，也没有该字典复制。 |

因此，后三种本地实现遇GraphModule子项时，对gm_dict['_modules'][k]的赋值也会改变原图共享的模块表项，把该项替换为序列化三元组。不能笼统把这三个serialize_fn当成不修改原图的只读快照；这条静态路径没有在真实torch.cond模型上执行或复现故障。

主线独立包的修订只明确隔离这张模块字典的替换，不把整个__dict__变成通用深拷贝，也不保证所有Tensor、任意属性或外部对象都可序列化。主线集成包与独立包有这个实质差异，不能只按“同一提交”混用结论。

## 节点记录不包含任意node.meta

序列化记录graph._tracer_cls和_tracer_extras，再按原graph.nodes顺序记录每个节点的六项：name、type、op、格式化target、args、kwargs。map_aggregate把参数里的Node替换为仅含名称的_ArgWrapper；其他叶子原样交后续pickle。

这份六元组没有显式保存node.meta。不能从恢复图能生成代码，进一步推导原节点中的FakeTensor、tensor_meta、源堆栈或优化Pass私有标记都会按原值恢复；若后续Pass依赖这些字段，需要核对其重新传播/生成阶段。这里不对外部Graph.create_node是否设置其他默认元数据作推断。

恢复先把_modules中tuple值递归解码，创建GraphModule实例并直接赋gm.__dict__，再用保存的tracer信息创建Graph。节点按保存顺序重建；Node参数按名称直接从此前创建的映射取回，没有本地“缺失名称自动补建”的流程。call_function的target额外按点分名称解析：import第一个模块，逐层getattr，确认callable；任一解析异常包装为NotImplementedError。其他op类型保留记录的target。最后赋gm.graph并recompile，仍未执行模型前向。

## bytes恢复成功的验收范围

SerializableGraphModule将上述三部分交pickle.dumps，恢复时用pickle.loads再调用deserialize_fn；本地没有在这个bytes协议内另加完整性摘要、配套版本或设备图校验。主线注释把pickle加载限定为内部可信缓存，不能把这段实现推荐为任意外部数据的通用解码入口；外层缓存的身份和校验应另核。

定位缓存命中后异常时，分别记录独立/集成包、固定提交、是否存在GraphModule子项、序列化前后模块表、节点元数据重建阶段、可解析的target名称，以及后续实际捕获/replay是否完成。没有子图的用例不足以覆盖共享_modules分支；Python图恢复成功也不等于数值、别名、梯度或启动时延已验收。通用GE缓存落盘资格另见[cache_compile保存与重编译](torchair_cache_save_and_recompile_contract.md)，不把两套工件格式视作同一协议。

## 固定实现证据

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph_cache_utils.py)（primary）：1–192；完整本地serializer，外部被调实现另计。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph_cache_utils.py)（implementation）：1–190；完整本地serializer，外部被调实现另计。
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph_cache_utils.py)（implementation）：1–190；完整本地serializer，外部被调实现另计。
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph_cache_utils.py)（implementation）：1–190；完整本地serializer，外部被调实现另计。
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：538–543、715–727；仅有界消费者，不提升整转换器资格。
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：346–351、542–554；仅有界消费者，不提升整转换器资格。
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：319–324、502–509；仅有界消费者，不提升整转换器资格。
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：319–324、502–509；仅有界消费者，不提升整转换器资格。
