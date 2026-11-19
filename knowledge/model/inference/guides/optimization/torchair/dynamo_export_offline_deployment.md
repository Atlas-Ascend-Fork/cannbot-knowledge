---
type: Guide
title: dynamo_export：GE 离线导图、外置权重与部署路径
description: 串联 AIR 导出、权重路径、ATC 转换和多卡配置，明确整图及功能互斥。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/dynamo_export.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/dynamo_export.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/dynamo_export.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/dynamo_export.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_export.py
  role: implementation
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# dynamo_export：GE 离线导图、外置权重与部署路径

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。发布部分选取A2/A3；主线A2/A3与950的限定范围见后文，不回推发布版。

## 导出入口

`torchair.dynamo_export(*args,model,export_path="export_file",export_name="export",dynamic=False,config=CompilerConfig(),**kwargs)` 用典型样例输入 trace，导出供 CANN 使用的 AIR 图，不再依赖 PyTorch 执行。dynamic 表示静态/动态图选择，不意味着支持任意动态 Python 分支。

## 前提与产物

被导出部分必须能构成一张图，不支持动态 if/else；不能同时开启 frozen_parameter，动态分档也不支持与 Dynamo 导图组合。AIR 文件大小不能超过 2G；权重可能以内嵌 Const 或外置 FileConstant 记录，dynamo.pbtxt 可读，AIR 为二进制。

export_path 使用相对路径时，后续 ATC 编译/运行需从相对路径父目录执行；绝对路径移到其他服务器时须保持原绝对路径，否则可能找不到外置权重。迁移时同时核对图和所有引用权重，不能只复制 AIR。

## 编译与多卡

来源提供 ATC 使用 --framework=1 将 AIR 转 OM 的路线，soc_version 应按实际设备选择，不把导出成功等同于 OM 可运行。

前端已含通信逻辑时，config.export.experimental.auto_atc_config_generated=True 可生成 model_relation_config.json、numa_config.json 模板；它们需要按实际拓扑修订，不是最终集群配置。后端切分可用 enable_record_nn_module_stack=True，但层定义需采用数组形式、模型深度至少两层，才能保留可供识别的层栈。

单/多卡及 AllReduce 等导出支持均按目标 rank 和通信域核对。比较原模型、导出图及目标环境结果，分别记录外置文件、shape 和通信映射。

- [分档互斥](../../../apis/torchair/set_dim_gears.md)
- [固定地址输入](../../../optimizations/rules/frozen_parameter_address_contract.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线导出副作用与成功信号

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节文档/实现已核对，主线总览覆盖A2/A3与950PR/950DT；发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的A2/A3条件仍独立保留，不回推发布版950或两仓主线配套。

主线实现的config默认None，省略时新建配置；传入对象会被直接设置export_mode、export_path_dir/export_name、weight_name和enable_ref_data=True，不能把同一对象导出后原样复用当作独立在线配置。export_name只取路径basename，实际产物还会受rank后缀影响。

实现调用torch._dynamo.reset()，再以fullgraph=True、指定dynamic和no_grad运行样例模型，捕获内部ExportSuccess；正常执行却没有该信号时只记录“export error!”。符号链接路径被拒绝时也可直接返回None。因此API无返回值不证明导出成功，需核对日志、AIR、可读图和全部引用权重/配置，再进入ATC与目标环境验证。

导出前的旧通信补丁分支直接比较torch.__version__与"2.3.0"；实际比较语义依赖版本对象，不能只据表达式推定排序或误判。[旧补丁的全局影响](collective_communication_graph_contract.md)仍需计入，不因处于导出过程就视为局部配置。

## 主线options文件与多卡部署模板

主线特性页新增options.json说明：按compile options与execute options组织，各有global/session/graph作用域；前两者来自全局初始化，graph来自单图编译。多卡示例在rank_0/rank_1内分别生成该文件，不能只保存根目录一份配置来假定所有切片完全相同。发布页未描述这项产物，不由文字差异推断发布实现绝对不会生成。

权重参数量不超过(2G-200MB)时，来源说明以内嵌Const保存；超过时写到export_path下并由FileConstant引用。该权重分界不是允许AIR突破2G。样例树可能演示外置权重，不能据样例固定要求每次必有同名p1/p2文件。

auto_atc_config_generated与enable_record_nn_module_stack默认均False；前者模板的item初始放node_id=0，需要按真实部署划分node，后者仍要求数组形式层命名与至少两层模型。导出脚本示例用gloo/CPU样例trace不等于目标HCCL/NPU执行已验证；迁移时一并核对路径、权重、作用域options、rank和拓扑。

## 导出前版本门槛的比较语义

复查npu_export.py的旧补丁条件，表达式为torch.__version__ < '2.3.0'，没有在此强制str转换。实际比较取决于版本对象，不能仅据右侧字符串就声称存在两位minor的字典序缺陷。这里仅确认条件及调用patch_for_hcom的控制流，不执行导出或补丁；全局替换的影响仍按对应通信卡核对。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/dynamo_export.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/dynamo_export.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/dynamo_export.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/dynamo_export.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_export.py)（implementation）
