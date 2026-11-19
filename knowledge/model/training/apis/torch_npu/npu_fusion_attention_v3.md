---
type: API
title: npu_fusion_attention_v3：训练图模式、张量随机数与更新边界
description: 限定A2训练V3六Tensor返回，区分公开BNSD图合同、CPU变长前缀及主线TND workspace/out更新路径。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fusion_attention_v3.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention_v3.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention_v3.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention_grad.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention_grad.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/_fa3_graph_handler.py
  role: implementation
created_at: '2026-11-10T04:49:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
---

# npu_fusion_attention_v3：训练图模式、张量随机数与更新边界

## 版本与公开支持

OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的文档均只列A2训练。它是[V1](npu_fusion_attention.md)支持图模式的变体，公开aclgraph合同限定input_layout="BNSD"。普通Schema自TorchNPU v2.6分支接入；主线新增的out/infer/workspace辅助接口自v2.7分支接入。发布文档的新增功能提示与具体软件依赖仍须按发布配套核对。

两版普通前向/反向均显式检查SocVersion<Ascend950，950直接拒绝；不是产品表未列出的未知状态。A3没有在本卡来源公开确认，不据宽泛芯片比较条件扩充平台。固定提交与Lint通过均不代表运行验证。

发布属于ascend_26_0_pt28。本文另读PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的FA3图处理器，描述其实现边界；该PyTorch与OpPlugin主线不是已经确认的软件配套，不能把两个独立源码段拼成部署承诺。

## 调用、六返回与迁移

```python
attention_out, softmax_max, softmax_sum, softmax_out, seed, offset = torch_npu.npu_fusion_attention_v3(
    query, key, value, head_num, input_layout,
    pse=None, padding_mask=None, atten_mask=None,
    scale=1., keep_prob=1., pre_tockens=2147483647,
    next_tockens=2147483647, inner_precise=0, prefix=None,
    actual_seq_qlen=None, actual_seq_kvlen=None,
    sparse_mode=0, gen_mask_parallel=True, sync=False,
    softmax_layout="", sink=None)
```

六项均Tensor：attention_out；FP32 softmax_max/sum；预留softmax_out；Philox seed/offset。V1的后三项为整数并含numels，V3不返回numels，不能继续按七项解包；V3前向也没有公开dropout_mask、seed、offset输入，不搬用V1/V2外部mask的参数。窗口保留pre_tockens/next_tockens拼写，与[V2](npu_fusion_attention_v2.md)不同。

普通路径attention_out按V的Dv分配、布局随Q；统计非TND为[B,Nq,Sq,8]、TND物理分配[T,Nq,8]，softmax_out为shape[0]Tensor。keep_prob=1时不生成有效dropout，seed/offset分配为empty的一元素INT64，未初始化有效随机数值；不能读取这些占位值作为随机种子或断言恒0。

0<keep_prob<1时，Eager从默认生成器取Philox元数据并返回CPU INT64[1]Tensor；capture使用生成器的NPU状态Tensor克隆，并把图内offset加到返回offset。文档CPU/NPU设备差异应保留，不能把两项转换成Python整数再捕获。反向通过这两项重建同一mask，numels由Q/K布局及变长前缀重新计算，不是显式传入。

## 输入与变长前缀

Q/K/V/PSE dtype一致，可FP16/BF16/FP32，ND、相同布局，支持BSH/SBH/BSND/BNSD/TND。普通训练非TND B为1..2M，TND B为1..2K，S/T为1..1M，Nq1..256且Nq/Nkv为非零整数。文档同时写K/V shape相同和Dq=Dk≥Dv、D1..768；实现按Dv分配不能裁定所有不等D组合的后端支持。

TND的actual_seq_qlen/kvlen是**一维CPU INT64 Tensor**累计前缀，不是V1/V2的Python列表、NPU Tensor或独立长度列表。例如独立[2,2,2]传CPU tensor([2,4,6])。host转换器对连续INT64零拷贝读取，其他dtype/非连续输入会复制/转INT64；这条宽容实现不能代替公开dtype要求，也不建议将浮点长度截断后使用。将前缀放CPU是本接口约束，不因图模式就改成NPU输入。

前向TND检查两项非空等长；普通反向从前缀直接读取首项并按Q列表长度访问KV列表，缺少前向同等的非空/等长检查。因此手工调用grad_v3时必须保持同一有效前缀，不能把默认None视作可用于TND反向。前缀长度文档同时写1..2K和varlen最大1K，保留其冲突，需明确实际后端上限。

中间零长度batch用重复前缀，如[2,4,4,6,8]，此时禁PSE；尾部batch不参与则另用[2,5,9,0,0]规则。host dropout大小按相邻前缀差乘积累计，尾0分支须单独验证，不把文档输入允许推导为全部dropout组合已验。发布约束中的actual_seq_kv_len是文字拼写问题，实际关键字为actual_seq_kvlen。

普通代码在转大写前选TND稀疏分支、检查softmax_layout，反向部分大小分支还用原input_layout比较。调用用文档大写值，避免把报错中case-insensitive理解成所有大小写组合等价。

## 掩码、PSE与精度

atten_mask为BOOL/UINT8，True/1遮蔽、False/0参与；非TND可BNSS/B1SS/11SS/SS，TND仅maxSq×maxSkv的SS且不允许整行全True padding。mask=None全计算，mode及窗口无效。padding_mask不支持，传None。

mode0默认mask、1完整自定义、2左上因果、3右下因果、4右下band、5非压缩prefix、6压缩prefix、7/8分别为mode3/2外部切Q的变长场景。TND允许0..8除5，其余布局0..6；mode1/2/3/5/6忽略窗口，mode0/4要求窗口与mask吻合，mode7/8不支持PSE。2048×2048因果压缩矩阵的上三角为True；mode6用3072×2048的三角+矩形格式。图与文档的完整窗口负值、prefix形状、外切累计长度示例见[V1](npu_fusion_attention.md)，这些同源约束在V3文档亦完整核对，不直接采用推理FIA模式编号。

prefix要求B≤32；Sq>Skv时宽度[0,Skv]，否则[Skv-Sq,Skv]。mode7只有最后一段band、pre≥last_Skv且next≤0；mode8只有第一段band、pre≥first_Skv，next按实际切分配置；单batch按band要求，K/V不切。模式不会自动完成分布式切分和通信。

PSE非TND可BNSS/BN1Skv/1NSS；满足文档给定Sq>1024或变长等长因果下三角等ALiBi条件时可保留最后1024行，shape为BN1024Skv或1N1024Skv，不泛化到任意位置编码。公开公式scale*(pse+QK^T)后Mask/Softmax/Dropout再乘V；不能拿V2其他pse_type公式直接替换。sink为FP32[head_num]的Softmax归一化偏置，普通路径与workspace更新路径的可用性不同。

inner_precise0/1保留、2处理无效行可能降低性能；mode3且Sq>Skv可自动启用，但不绕过TND整行padding限制。softmax_layout仅""或TND，TND值仅用于TND输入；普通非950有相应V4/V5后端分支且转换为same_as_input，缺符号时不静默保证新布局。大规模B/S/N/D可触发timeout/trap，文档建议切轴，没有普适尺寸阈值。

## 捕获随机数与副流

Eager mask生成走整数seed/offset ACLNN接口，必要时回退StatelessDropOutGenMask；capture走aclnnDropoutGenMaskV2Tensor。外部手动提取seed.item()或转CPU不是这条捕获协议的一部分。默认parallel=True在secondary stream生成DSA mask，capture首次通过事件建立原流到副流依赖并设置生成器的secondary_stream_capture_state，避免逐算子重复建立捕获状态。

同步开关、事件与生成器状态共同决定执行顺序，不单凭parallel=True宣称加速。keep_prob=1的占位随机数不应参与梯度有效性判断；有dropout时须同时保留前向返回的seed/offset、统计和输出，交给同版本反向消费。相同手动随机种子、不同capture/replay序列的等价性需要实测，不靠Tensor化接口名自动保证。

## 主线workspace/out图更新扩展

主线OpPlugin另有forward/grad的.out，以及infer_output/get_max_workspace辅助接口；发布快照无这组扩展。out Schema明确输出Tensor别名突变：前向六个、反向五个。其预分配输出、workspace、CPU前缀管理须由同版本框架调用，不当作普通V3改名版直接调用。

该主线扩展的workspace路径只支持TND、要求两个CPU前缀非空；前后向workspace查询均拒绝sink，前向out也明确拒绝sink。直接调用反向out且sink非空时，代码仅检查GradV5符号，没有执行计算后便返回预分配输出，是另一静态无写入分支风险，不能把普通入口的sink支持推广到out。

out/最大workspace调用VarLenScoreV5及UnpaddingScoreGradV5，直接透传softmax_layout字符串，而普通入口把TND改same_as_input；两者统计排布不能仅因参数同名就假定一致。查询最大workspace本身还分配临时输出、可能调用dropout生成helper和推进RNG，不是零副作用的整数大小查询。需要把整个框架的准备/捕获/更新顺序纳入验证。

PyTorch主线FA3处理器在CANN≥9.1.0时对非BNSD接管：普通入口预查询workspace、推输出形状、改为out，重放更新项为两个actual_seq CPU前缀。BNSD明确绕过处理器，不能据此说BNSD没有普通aclgraph支持。其代码意图拒绝TND且keep_prob<1并要求用图分区回退Eager，不在本卡推荐该组合。

处理器还有静态适配边界：它选择所有非BNSD布局，底层workspace却只接受TND，因此BSH/SBH/BSND不因被handler选中就可成功；keep_prob读取先取kwargs默认1的or表达式，可能忽略位置传参的dropout值；应按实际参数形式验收。处理器将softmax_out预分配为与max同shape，而普通入口为[0]；后处理返回out列表。Python out适配、当前Schema和CANN必须作为同一版本组合核验，不能将各独立主线片段直接拼装。

## Autograd与测试证据

Autograd保存前四输出和seed/offset Tensor，生成Q/K/V/PSE/sink五类输入梯度；grad_v3返回dQ、dK、dV、dPSE、dSink。无PSE时Eager的dPSE最终undefined，无sink时dSink为空FP32占位。TND反向依赖前向CPU前缀，而不是仅靠seed/offset便可恢复整个形状合同。

与V1共享的forward测试中，V3有8个方法：BSH/TND/GQA的Eager及dropout比对，另有4个图相关方法；grad文件V3有4个方法，包含2个图重放。全部限定Ascend910B。图示例实际使用BSH和TND，范围宽于公开文档的BNSD承诺；TND图方法虽调用backward，主要断言重放后的attention输出，不能称所有梯度都已核验。单独grad的两个Eager方法只断言dQ，图方法分别断言dQ/dK/dV。

没有把测试函数存在当作通过记录；本卡未执行上游、设备、图捕获或性能测试，无新增verified。部署应按公开产品、实际软件组合、布局及dropout分支验证输出、统计排布、全部所需梯度、连续多次重放的RNG及前缀更新，主线workspace扩展另作验证。

- [软件栈来源与适用性](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fusion_attention_v3.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention_v3.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention_v3.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention.py)（example）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention_grad.py)（example）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention.py)（example）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention_grad.py)（example）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/_fa3_graph_handler.py)（implementation）
