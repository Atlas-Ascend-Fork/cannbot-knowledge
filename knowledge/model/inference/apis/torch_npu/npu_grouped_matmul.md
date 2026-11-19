---
type: API
title: 分组批量矩阵乘（torch_npu.npu_grouped_matmul）
description: torch_npu.npu_grouped_matmul：按分组边界对多组输入和权重执行矩阵乘，group_list 编码须与路由结果一致。 将相同或相似形状的多组矩阵乘批量处理，可减少独立调用和内存访问开销；具体形状支持、分组边界与收益仍由该版参数契约及实际负载决定。 按固定发布与主线区分A2/A3、310P和950的分组表示、尺度/打包、bias位置、图模式和调优边界。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_grouped_matmul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/dynamic_output_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/dynamic_output_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py
  role: implementation
created_at: '2026-11-10T03:38:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- 310p
- '950'
aliases:
- torch_npu.npu_grouped_matmul
- GroupedMatmul
---


# GMM 分组输入与返回约定

## 版本与范围

前面的基本范例描述发布基线 `ascend_26_0_pt28` 对应 OpPlugin 的 A2/A3 FP16/BF16 推理合同；后续各节另补发布量化、310P及固定主线950的独立范围。输入 x、weight 是 Tensor 列表；接口返回 List[Tensor]，即使输出只有一个 Tensor，返回值仍是列表。

常用调用形态（省略量化和激活参数）：

```python
outputs = torch_npu.npu_grouped_matmul(
    x, weight, bias=None, group_list=...,
    split_item=..., group_type=..., group_list_type=...,
    output_dtype=None)
```

## 分组与切分

split_item 为 0/1 时产生多个输出，其数量与 weight 列表相同；2/3 时列表里只有一个输出。group_type=-1 表示不分组，0 表示 M 轴分组，2 表示 K 轴分组；具体可用场景受输入表示及 dtype 限制。

Tensor 形式 group_list_type=0 表示累积边界，应非负且单调不减；type=1 表示每组大小；type=2 是 group index/size 成对表示，在发布来源中只支持特定 INT8、M 轴分组场景，不能用于通用 BF16 路线。List[int] 与 Tensor 参数组合也不同，不应把全部类型选项混搭。

典型 Tensor group_list、单输入、单权重组、单输出的 M 轴路径要求 group_type=0、split_item 为 2 或 3，x/y 为二维、weight 为三维，x 不支持转置。group_list 必须是 int64，第一维最多 1024 个 group；group_list_type=0 时末项必须等于 x 的 M，type=1 时组大小总和必须等于 x 的 M。保持专家/分组顺序与权重一致，不能把累计边界当 token count 直接传入。

例如 x=[X]、weight=[W]，X.shape=(M,K)、W.shape=(G,K,N)，group_list 为长度 G 的 int64 NPU 累计边界 Tensor 且末项等于 M，可采用 split_item=3、group_type=0、group_list_type=0，返回长度为 1 的列表，其 Tensor 为 (M,N)。该形态仍需满足具体 dtype、bias 与组边界约束，不能切换到 split_item=0/1 后沿用单输出解释。

## 验证与边界

对每组显式 matmul 建参考，比较组边界、空组、输出拆分/拼接与精度。FP16 和 BF16 的 bias dtype 合同不同；量化、伪量化及激活须按源码文档相应场景重新核对，不能推导任意 dtype 组合都可用。310P的窄范围及主线950扩展见后续产品专节，不由前面的A2/A3范例外推。未运行 GMM 或性能实验。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## 主线扩展与产品范围

以下补充固定OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda与发布dedc316708372c9a8bfde4527abd2a94b74840f5，以及TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c、发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的实现差异。发布来源组合是ascend_26_0_pt28，主线配套未知；本卡不登记运行或梯度验证。

主线公开产品为A2/A3、310P及Ascend950系列（包含旧称Atlas A5）的PR/DT；发布有A2/A3与310P，未列950。950新格式与模式不回推发布。主线中文明确非量化/全量化适用训练或推理，伪量化仅推理；英文开头也这样写，约束段却只写推理。这里保留范围差异，不把所有量化组合标为已支持训练；950的K轴分组训练另只列HIFLOAT8/E4M3/E5M2全量化输入，FP4全量化仍只推理。

310P范围较窄：x/weight/bias/output为FP16，group_list必须Tensor，group_type=0、split_item=2/3、单x/单三维weight/单输出，N为16倍、最多1024组，x不转置、weight可转置；type=0末边界或type=1总行数须等于M。不能用type=2、激活、量化/伪量化尺度、tuning_config和dtype覆盖扩展该产品。其类型表又列FP32 per_token_scale，而参数段没给完整310P语义，不能据这一格构造新量化路线。发布图样例使用多列表、group_type=-1，与310P窄表不符，不作310P可用配方。

## 默认值、两种重载与边界数组

两固定Schema的Tensor重载默认group_type=None，C++明确要求显式-1/0/2；主线文档原型的-1不代表省略时实际绑定自动得到-1。List[int]重载的group_type=None可以走旧List实现，不能以同名函数统一所有参数行为。Tensor版有tuning_config和四个dtype覆盖，List版没有这些新参数且output_dtype用ScalarType；不要混用数字枚举空间。

主线List[int]要求非负递增且长度非0，发布写长度不能1；主线Tensor count中文也改为非空，英文仍写长度不能1。Tensor type=2的中文新增非零size组按groupIdx有序前置、零size组按groupIdx有序后置；不能只验证size非负。中文generic enum提到group_type=1为N轴，但各产品条款和C++都仅-1/0/2，因此不据此启用N轴分组。

A2/A3的M轴单输出通常须覆盖全部M；type=2总size中文写<=M而英文写=M，保留差异。950单单单和中文单多单允许有效分组总量/末边界<=M，英文单多单仍写=M；因此主线有前缀有效的场景，不能无条件消费返回的全部M行。发布INT4示例末边界14而输入M=15，与发布完整覆盖表不同，不当作扩大旧协议的证明。

split_item=0/1返回多个Tensor，=2/3只返回一个Tensor但外层始终List。M轴组合还需分别核对单单单、单多单、多多单的列表长度、N相同和统一weight转置。950非量化列表最多1024，普通/量化多列表通常128；MX NZ多weight只Eager，不能由列表上限推导图支持。K轴group_type=2要求x转置、weight不转置、ND进出；单输出为[E,M,N]，单多多为各[M,N]且仅非量化、不支持bias，不能按M轴拼接解释。

## 量化公式中bias的位置

非量化为X@W+bias。INT8静态量化中，INT32 bias在整数GMM后、乘scale前加入；FP16/BF16/FP32 bias则在缩放后加入且无offset。动态量化同理：INT32 bias先加再乘weight scale与per_token_scale，浮点bias在两个尺度相乘后加入。这两种bias不能仅做dtype替换而保值复用。

伪量化的per-channel/per-group为X@((W+antiquant_offset)*antiquant_scale)+bias；MX伪量化不凭空加antiquant_offset，混合FP8激活还先乘per_token_scale。K-CG同时有权重per-group antiquant_scale、per-channel scale与激活per-token scale，不把这些尺度合成任意同形广播。

A2/A3发布浮点组合中FP16 bias为FP16，BF16 bias为FP32；INT8静态的INT64 scale是编码承载，不是普通整数倍数。Tensor动态输入scale可FP32/BF16，per_token_scale为FP32；List重载的per_token_scale只能None。低位INT4目前用INT32或相应承载表示，数值量化与位打包分别核对。

950静态T-T/T-C、动态K-T/K-C/T-T/T-C、G-B与MX按组合表配对：INT8、FP8或HIFLOAT8的输入类型、bias类型、scale与输出dtype都有关联，不能对总类型列表做笛卡尔积。INT8输出仅特定静态per-channel路线，图模式明确不支持；INT32输出、FP16/BF16/FP32输出也各有尺度与输入限制。

## 950尺度形状和自动模式判定

下表的g为分组数，M/K/N为逻辑矩阵轴，尺度仍封装在相应Tensor列表中。

| 模式 | M轴group_type=0 | K轴group_type=2 |
| --- | --- | --- |
| 静态T-C/T-T | scale[g,N]或[g,1]/[g]；无per_token_scale | 同类尺度，但K分组全量化不支持INT64 scale |
| 动态K-C/K-T | scale[g,N]或[g,1]/[g]，激活尺度[M] | 激活尺度[g,M] |
| 动态T-T/T-C | 激活尺度[g,1]或[g]，scale按tensor/channel | 同类形状按每组语义解释 |
| MX，block32 | scale[g,ceil(K/64),N,2]或转置轴，激活尺度[M,ceil(K/64),2] | scale[K//64+g,N,2]，激活尺度[K//64+g,M,2] |
| G-B，K/N block128 | scale[g,ceil(K/128),ceil(N/128)]或转置轴，激活尺度[M,ceil(K/128)] | scale[K//128+g,ceil(N/128)]，激活尺度[K//128+g,M] |

末轴2是两个MX尺度打包，并非N。K轴的额外g为分组尺度存储协议，不能用全局ceil(K/64)替换。允许最后block不足时也须匹配分组元数据和实际尺度，不按完整块个数截掉尾部。

模式由shape判别，单例轴有优先级：N=1且scale[g,1]优先per-tensor；K轴M=1且激活尺度[g,1]优先per-tensor。K轴K<128、N<=128且scale二维[g,1]一律按G-B，若想非G-B用一维[g]区分。M轴g=M、K>128且激活尺度[g]选per-token；K<=128且[g,1]则随权重模式选per-tensor或per-group。K轴K<128时，M非1且N<=128选per-group；N>128随权重模式选per-token/per-group；M=1且[g,1]时N<=128选per-group，否则选per-tensor/per-group。不能只因numel相同随意squeeze尺度。

## 950低位与伪量化布局

FP4全量化的逻辑K为偶数且不为2，非转置W的逻辑N也为偶数；NZ下K/N不能1，FP4需大于2。ND表列E2M1，NZ表另列E1M2，E1M2只限NZ；主线新增该覆盖类型，不回推发布。8bit承载FP4每字节2值，INT32承载INT4每值8个低位；伪量化float32承载E2M1又是每值8个，不能把这些承载的尾轴按同一个倍率reshape。真实NZ转换不由view替代。

普通INT4伪量化per-group的group_size为32/64/128/256，K须整除；多weight的每组长度相同，weight尾轴为偶数，转置per-group长度也为偶数。单weight的antiquant_scale为[g,G,N]，多weight为[Gi,Ni]且固定不转置；多多多per-group只支持转置weight。MX A16W4用打包float32权重、E8M0 antiquant_scale[g,K/32,N]；混合FP8/FP4用UINT8/INT8权重、E8M0 antiquant_scale[g,N,K/64,2]，多weight各[N,K/64,2]，激活尺度[M,K/64,2]，需显式输出类型且bias同输出dtype。

K-CG只支持count type=1，group_size为128/192/256/512，antiquant_scale[g,G,N]、scale[g,N]、per_token_scale[M]。S8S4 K-CG的scale为[g,K/256,N]；K-C的scale和offset为[g,1,N]。主线英文offset段仍写只能None，中文去掉了该总限制，且950 S8S4 K-C条款明确FP32 offset；按窄场景限定，不能扩大所有量化offset。

scale的NZ亲和格式单独限定：仅E4M3激活/权重的MX、M轴分组、weight真实NZ且不转置，只Eager。其物理storage shape为[E,ceil(N/16),ceil(K/64),16,2]，多weight每项少E轴；不能与普通四维逻辑MX scale互换。

## 激活、图模式与调优参数

act_type为0无激活、1ReLU、2GELU_TANH、4FAST_GELU、5SiLU，3的GELU_ERF仍不支持。A2/A3只在per-token量化允许激活。950只有INT8静态T-C/动态K-C且scale FP32/BF16的全量化允许上述激活；非量化ND FP16/BF16且group_type=0/-1只支持0/2，伪量化不支持激活。不能因参数枚举存在就给任意模式加SiLU。

950图模式排除INT8输出、全量化INT4配对、MX NZ多weight、scale NZ亲和和部分per-group伪量化；MXFP4 NZ仅静态图，且E>1、K>64，不支持动态shape图。混合MX A8W4两种图模式均排除E=1或K=64。图条款又限制伪量化offset=None、部分dtype覆盖None，与混合示例及S8S4示例不完全一致；保留模式/版本差异，不用单例代码覆盖总约束。非量化FP16/BF16的NZ条款与后面“NZ仅伪/全量化”的总句也冲突，不能宣称全部组合已统一支持。

tuning_config在950只明确S8S4 K-C/K-CG。第一项0..min(M,UINT32_MAX)是预期token数，0表示未指定，当前只校验保存、不参与实际调优；第二项0/1会切换权重布局，1只支持offset非空per-channel、单weight，先[E,N,K]排布再转NZ。通用文案说后续元素预留不能盖掉这个窄分支，`[0,1]`也不是普通性能旋钮。310P不支持该参数，A2/A3旧条款仅限特定INT8单tensor单专家模式；收益需要实测。

## C++分配、Meta与GE实现边界

主线新增单三维weight专家轴1..1024检查，发布少该检查不代表更宽产品支持。主线K分组split0/1改为每weight分配[M,Ni]，旧发布会沿group_list差值分配行，迁移应看每项shape与个数；不能只验拼接后大小。其余M轴多输出的Tensor分支逐项.item读取边界，可能发生设备到主机同步。优先按目标输出结构选合法分支并测完整调用，不能概括所有GMM都无主机开销。

Tensor路径先检查aclnnGroupedMatmulV4，缺失时拒绝Tensor group_list并提示更新CANN或使用List；这不是已实测最小版本。ND后续按V5符号及dtype选择V4/V5，V4不传tuning_config；两版dtypeValid是依赖首次输入/覆盖的static const，混合dtype调用序列仍需核对实际分支。NZ要求aclnnGroupedMatmulWeightNz存在；主线S8S4识别后offset空时传quant_per_group_size=256，offset有值传0，发布恒0，不回推新S8S4协议。

两Meta共享Tensor/List实现，dtype helper仅接受FP16/BF16/FP32/INT32，公开Eager的INT8输出不等于Meta支持。主线新增空列表、部分K>0和K轴多输出检查；FP4是否转置又用shape关系判断，C++用stride，需核对非方形与打包输入的真实返回。仅Meta成功不验证尺度、边界内容、物理NZ或所有列表项。

主线GE新增非950 A4W4同时Bitcast x与weight且不先插Transpose，由graph_pass识别模式设置转置；发布仅走旧weight转换。FP4主线部分分支用keep_dim，尺度含单例轴时weight走旧扩shape；发布全部旧扩shape，不跨版本复用字节reshape。通用dtype覆盖与scale覆盖主要修改第0项、per_token_scale也只取第0项，不推导任意多列表混合dtype。

GE把输出FP16/BF16/INT32映射为内部0/1/2，FP32仅950映射3，INT8明确拒绝。dynamic_output包装按group_list长度或len(x)计算split0/1返回数，split2/3为1，没有专门按group_type修正；K轴多输出等组合须检查真实图结果个数。底层_GroupedMatmul手工构图，没有真实IrDef类型检查，旧docstring列出的窄类型不能作为FP8明确No，也不能据此认证新产品类型。

## 测试的覆盖与缺口

主线1232行测试27方法、发布1115行23方法，各4个无条件skip。已有A2 FP16/FP32分组和K轴split3的数值参考未在本次运行；新K轴split0/1分配改变尚无同文件对应图验收。test_5虽传tuning_config，但helper没有转交给算子，不能证明调优参数生效或更快。

部分量化参考尺度生成返回的FP32和编码UINT64来自不同随机阵列，调用又把小FP32直接cast成INT64；输出转INT8再以宽容差比较，不能作完整精度证明。950 FP8例取supported_output[0]只是参考第一行，常量输入可能掩盖行差；部分NZ例的权重/尺度/分组形状也不一致。

新增950 S8S4 zero用例传count type=1却给[4,8]、M=8，总量12越过M；零输入和shape/零输出检查不能证明合法分组。FP4参考直接把UINT8字节转浮点而未解包，K轴128/256也不匹配，尺度标E8M0却用二维普通尺度且缺激活尺度；不能按测试名称登记MX数值覆盖。旧A8W4 skip注释提到可能改x，但Schema未声明该别名，不据注释扩大所有GMM原地语义。

没有本次310P、950各新增模式、梯度、确定性或性能实测。验收应按产品/固定版本/后端选择一个合法组合，逐组比较逻辑矩阵值、尺度编码、bias先后顺序、有效前缀和输出列表结构，再测模型端到端收益。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 分组批量矩阵乘：torch_npu.npu_grouped_matmul

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

按分组边界对多组输入和权重执行矩阵乘，group_list 编码须与路由结果一致。

### 输入、输出与行为

将相同或相似形状的多组矩阵乘批量处理，可减少独立调用和内存访问开销；具体形状支持、分组边界与收益仍由该版参数契约及实际负载决定。

### 文档签名

```text
npu_grouped_matmul(x, weight, *, bias=None, scale=None, offset=None, antiquant_scale=None, antiquant_offset=None, per_token_scale=None, group_list=None, activation_input=None, activation_quant_scale=None, activation_quant_offset=None, split_item=0, group_type=None, group_list_type=0, act_type=0, output_dtype=None, tuning_config=None) -> List[Tensor]
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_grouped_matmul.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul.md](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/dynamic_output_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/dynamic_output_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py)（implementation）
