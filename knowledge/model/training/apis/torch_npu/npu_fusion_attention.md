---
type: API
title: npu_fusion_attention：版本化训练掩码、Dropout与图边界
description: 按固定版本说明A2与950训练入口，补齐稀疏压缩掩码、TND外切、随机数重建及Meta/图转换限制。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/npu_patches.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fusion_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DropoutGenMaskKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention_grad.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DropoutGenMaskKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention_grad.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fusion_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fusion_attention.py
  role: implementation
created_at: '2026-11-09T02:02:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- '950'
---

# npu_fusion_attention：版本化训练掩码、Dropout与图边界

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_fusion_attention(query, key, value, head_num, input_layout, pse=None, padding_mask=None, atten_mask=None, scale=1., keep_prob=1., pre_tockens=2147483647, next_tockens=2147483647, inner_precise=0, prefix=None, actual_seq_qlen=None, actual_seq_kvlen=None, sparse_mode=0, gen_mask_parallel=True, sync=False, softmax_layout="", sink=None, dropout_mask=None, seed=0, offset=0) -> (Tensor, Tensor, Tensor, Tensor, int, int, int)
```

这是训练 Attention 的融合入口，发布文档只确认 A2，且明确暂不支持图模式或 aclgraph。返回 attention_out、FP32 softmax_max、FP32 softmax_sum、预留 Tensor、seed、offset、mask 长度共七项；不要按推理 FIA 的双返回解包。

## 参数与组合限制

- Q/K/V/pse 的 dtype 一致，支持 FP16/BF16/FP32、相同输入布局；K/V shape 一致，Q/K 的 D 相等且 Dk≥Dv，D≤768，Q 头数≤256，Q/KV 头数比为非零整数。
- 布局支持 BSH/SBH/BSND/BNSD/TND；TND 必传 actual_seq_qlen/kvlen 的累计长度。存在零长度 batch 或尾部不参与计算时来源另有规则，不能用一般递增规则代替。
- mask 的 True/1 表示遮蔽，False/0 表示参与。mask=None 时 sparse_mode 与 pre_tockens/next_tockens 不生效；这两个参数名在此接口保留 tockens 拼写。
- keep_prob∈(0,1]，1 表示不丢弃。自定义 dropout_mask 应与其生成时的 seed/offset 配套；第四个返回 Tensor 为预留值，不当作概率矩阵。
- padding_mask 尚不支持。softmax_layout="TND" 需要框架≥7.2.0、CANN≥8.3.RC1；sink 为 FP32(head_num,)，需要框架≥7.3.0、CANN≥8.5.0。支持训练入口不代表其全部新参数可用于旧包。
- prefix、varlen 外切和稀疏压缩 mask 的完整边界见下文；不照搬推理接口的 sparse_mode。

## 验证与模型关联

先在 keep_prob=1 时按 mask 极性比对参考，再验证 dropout 复现、七返回及反向需要的统计；新版本图能力必须读取对应版本来源。 本卡为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/npu_patches.py#L138)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)


## 主线平台与完整参数边界

本卡同时核对OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，以及TorchAir发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013、主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c。发布属于ascend_26_0_pt28；两个主线不能仅凭日期视为配套。

发布文档仅列A2训练，主线另列Ascend950系列（包含旧称Atlas A5）PR/DT；两版均明确训练用途、暂不支持图模式/aclgraph。未列A3不等于另有明确拒绝，但本卡不认证A3。C++内有950分支也不能反推发布文档未承诺的950完整支持。

Q/K/V/pse均为FP16/BF16/FP32且dtype相同，输入为ND、布局一致。主线A2的HeadDim为1..768，950为1..512；非varlen B为1..2M，varlen B为1..2K，S及T=B*S为1..1M。Q头数1..256，Nq/Nkv为非零整数，>1为GQA，=1为MHA。Dq=Dk、Dk≥Dv；文档同时声称K/V shape一致，与允许Dv较小存在冲突。Eager实际按V的D分配attention输出；主线Meta已跟随Dv修正，发布Meta仍empty(query.shape)，不能将发布FakeTensor形状作为Dv不同路径的依据。

输出不是普通Softmax概率矩阵：attention_out的布局随Q、尾维随V；softmax_max/sum为FP32，非TND逻辑[B,N,Sq,8]、TND物理分配[T,N,8]，具体逻辑排布还受softmax_layout控制；第四项为shape[0]预留Tensor。后三项为整数seed、offset、numels，numels是dropout覆盖元素数，不能当UINT8存储字节数。

## PSE、sink与精度模式

PSE非变长支持BNSS、BN1Skv、1NSS；主线增加TND展平说明：逐batch拼接N*Sq_i*Skv_i，总长度为各batch之和。满足非变长Sq>1024，或TND各batch Sq=Skv且mode0/2/3因果下三角等前提时，ALiBi可只保留原PSE最后1024行，shape为BN1024Skv或1N1024Skv；它是有条件的压缩合同，不能截断任意相对位置偏置。

两版公式及发布公式图为scale*(pse+QK^T)之后Mask/Softmax/Dropout再乘V，主线新PSE示例的CPU参考却按scale*QK^T+pse，且只打印误差。两者对PSE缩放不同；底层算子在此仅透传pse与scale，不能从包装层裁定公式。需要非单位scale、非零PSE的同版本数值验收，不能照抄任一示例当已验证公式。

sink为FP32[head_num]，示例将它作为每头额外logit拼入Softmax分母，随后去掉对应列再乘V；它不同于给每个输出向量加偏置。文档要求TorchNPU≥7.3.0、CANN≥8.5.0，但还须核对具体后端分支：非950有sink时分别要求FlashAttentionScoreV3或VarLenScoreV5及对应梯度符号；950前向ScoreV4分支未传format_sink，而梯度分支传入sink。这是静态前后向不一致风险，不能认证950所有sink组合。

inner_precise=0/1为保留值，2使能无效行处理以降低整行mask的精度损失，可能降低性能；某些场景如mode3且Sq>Skv会自动使能。与此同时文档明确TND不支持整行全True的padding mask，不能用inner_precise=2绕过该输入约束。计算量过大出现timeout/trap时文档建议切轴；B/S/N/D均影响工作量，没有所有形状通用的安全阈值。

## 掩码、窗口与压缩格式

atten_mask为BOOL/UINT8，True/1遮蔽，False/0参与，支持BNSS/B1SS/11SS/SS；TND仅SS，维度按maxSq/maxSkv。无mask时固定全计算，sparse_mode及两个窗口参数不生效。allMask表示输入完整矩阵，并非要求矩阵全True。

|sparse_mode|语义及输入合同|
|--|--|
|0|defaultMask，无mask全计算；有mask时窗口必须匹配原矩阵，按左上角解释。next=0且pre≥Sq是因果；band的非负pre/next分别限制前后范围。|
|1|完整自定义mask，忽略pre/next。|
|2|左上因果，忽略pre/next，使用2048×2048压缩mask。|
|3|右下因果，忽略pre/next，使用相同2048×2048压缩mask。非方阵时与mode2不同。|
|4|右下角为起点的band，pre/next范围需有交集，mask与窗口匹配，输入2048×2048压缩mask。|
|5|非压缩prefix，每batch给prefix长度，mask为BNSS/B1SS；忽略pre/next，TND不支持。|
|6|压缩prefix，输入3072×2048：上2048×2048为因果压缩区，下1024×2048左半0右半1；忽略pre/next。|
|7|仅TND，来自mode3的模型外部Q切分，最后一个batch为band；pre≥last_Skv、next≤0，不支持PSE。|
|8|仅TND，来自mode2的模型外部Q切分，第一个batch为band；pre≥first_Skv，next按真实切分配置，不支持PSE。|

mode2/3/4/7/8所称压缩下三角是计算保留区域；输入布尔mask实际主对角线以上为True、下方及对角为False，不要把三角方向与mask极性反转。mode7/8仅一个batch时按band要求配置，仍传2048×2048压缩mask。

mode0的负窗口也有约束：next<0时pre≥abs(next)，且abs(next)<Skv；pre<0时next≥abs(pre)，且abs(pre)<Sq。mode1/2/3/5/6会忽略窗口，不能靠设置pre/next改变这些模式的语义。

prefix要求B≤32。Sq>Skv时prefix长度范围[0,Skv]，Sq≤Skv时[Skv-Sq,Skv]。文案同时称“基于rightDownCausal”及“起点左上角”，图示显示每batch左侧完整prefix矩形与因果保留区，不能用一行“右下三角”概括。非方阵边界要核对实际mask和输出，而不是仅凭模式名推导。

## TND累计长度与模型外切

actual_seq_qlen/kvlen为INT64列表的累计长度，TND两项必须非空且等长；不是含首个0的cu_seqlens整表。普通零长度batch用重复前缀，如独立长度[2,2,0,2,2]传[2,4,4,6,8]，此时不支持PSE。尾部batch不参加计算则另有特例：[2,3,4,5,6]后两项跳过时传[2,5,9,0,0]，不能把这条尾0规则推广为任意乱序前缀。文档同时写列表长度1..2K及varlen最大1K，存在内部不一致，部署时需明确实际后端上限。

mode7/8是模型脚本先切Q的S轴，K/V不切，算子不会自动完成多卡通信。文档mode7示例：卡1最后band pre=6、next=-2，Q前缀[3,5]、KV前缀[3,9]；卡2仍mode3，Q[2,7,11]、KV[6,11,15]。mode8示例：卡1仍mode2，Q[3,5]、KV[3,7]；卡2第一个band pre=4、next=1，Q[3,8,12]、KV[4,9,13]。这些数组与切分位置共同决定语义，不能只换sparse_mode数字。

C++在将input_layout转大写之前就检查是否精确等于"TND"并选稀疏范围、校验长度；softmax_layout="TND"也先要求input_layout精确"TND"。虽然最终报错声称case-insensitive，调用建议传文档大写值，避免小写tnd绕过变长检查后进入不同分支。传入实际长度列表还参与后端路径选择，非TND调用不要附带与布局不符的变长列表。

## Dropout随机数、外部掩码与反向重建

keep_prob是保留概率，(0,1]；生成器_npu_dropout_gen_mask的p为丢弃概率，因此传p=1-keep_prob。外部mask必须使用同版本内部生成接口，不是直接把[B,N,Sq,Skv]的BOOL矩阵当作掩码。其UINT8存储长度为ceil(numels/128)*16字节，测试按little bitorder解包；这里只说明消费者合同，不自建后端内部打包格式。TND的numels按Nq*sum(Sq_i*Skv_i)计算，GQA不能按Nkv替代。

文档将内部seed=0解释为默认种子、非0解释为指定值，但两版V2R2+包装在无外部mask且0<keep_prob<1时，无条件从默认NPU生成器philox_engine_inputs(10)取得新seed/offset并覆盖输入值；不应承诺仅在调用参数写seed=42便固定内部dropout。外部mask路径则保留调用方提供的seed/offset，必须与生成该mask时一致；seed=0不等于任意调用之间自动复现。

外部mask还存在重要静态缺口：前向局部numels只在TND初始化，非TND通常由内部mask生成helper赋值；显式外部mask会跳过helper，非TND返回numels可能未初始化。两版Autograd都未保存/透传外部dropout_mask，而是用返回的seed/offset/numels重建反向mask，因而不能把“相同外部mask两次前向相等”当作完整训练梯度正确性。TND尾0跳过规则与host端相邻差乘积累计numels也应单独验收，不能仅因文档允许尾0就认证所有dropout组合。

非950内部mask在0<keep_prob<1时由DSA生成，950helper保留随机数元数据而不生成mask，交给ScoreV4的seed/offset路径。gen_mask_parallel=True使用secondary stream，False在当前流；sync及前后事件控制流依赖，不能当作吞吐提升的普遍承诺。概率近0/1的EPSILON内部分类分支不扩大公开keep_prob合法区间。

## 版本、Meta与图转换限制

softmax_layout仅""或TND，只有input_layout=TND可配置；默认统计逻辑NTD，传TND时以same_as_input送后端。文档注明TorchNPU≥7.2.0、CANN≥8.3.RC1；非950还检查对应VarLenScoreV4/UnpaddingScoreGradV4符号，缺失时不能静默当新布局。Meta的物理shape本身不保证统计数据在内存中的NTD/TND解释一致。

主线Meta将seed/offset/numels都置0，并在950首次提示torch.compile可能优化掉这些整数、固定随机种子仍与Eager不同；发布Meta没有该警告。两版反向Meta始终给dpse=None，而Eager有PSE时分配dpse，不能用Meta形状证明PSE梯度路径完整。

两个固定TorchAir转换器均只接受input_layout为BSH/BNSD且keep_prob约等于1，其他路径抛NotImplementedError。它们把PSE对应real_shift/pse_shift写None，忽略传入pse；签名未接入softmax_layout/sink/dropout_mask/seed/offset新前向参数，梯度只返回旧四项，而当前Schema为五项。前向将GE四项顺序重新排为attention在首、再补整数0；不能把旧GE转换器存在等同于当前公开训练API完整图支持，也不能凭转换器绕过文档明确的图限制。

V2R1旧C++条件分支不接sink，反向四输出，与当前v2.1..newest Schema存在差异；前向还把seed/offset参数再次声明局部量，发布950梯度softmax_layout字符数组也只初始化最后一字节。这些是旧分支的静态可构建性/接口风险，未编译未运行，不据此声称发布PT2.8已观察相同故障。

## 测试证据与验收边界

两个版本测试文件仅空白/末尾换行不同：forward15个方法、grad6个方法，均限定Ascend910B，部分实际调用V3而非本API。V1的BSH前向比对CPU；TND/GQA含输出、max/sum及Autograd dQ/dK/dV比对；单独grad文件的V1两个方法只断言dQ，虽CPU计算了dK/dV也不能称全部梯度已验。外部mask方法检查shape，复现方法比较同mask两次前向，没有数值参考、返回numels及外部mask反向断言。图重放方法调用V3，不能挪作V1的aclgraph支持证据。

主线文档基础mode0..4及prefix示例有误差断言；新增PSE/sink示例仅打印最大误差，外部mask示例仅打印形状和随机元数据。当前核对未执行这些上游脚本、算子、设备或性能测试，无新增verified。部署应分别验输出、统计排布、整数元数据和全部实际训练梯度，特别覆盖Dv变化、非方阵prefix、尾0变长及dropout、950 sink/编译随机数；不得将此静态入库当作这些组合已认证。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention.md)（primary）

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fusion_attention.md)（constraint）

- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention.md)（constraint）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp)（implementation）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DropoutGenMaskKernelNpuOpApi.cpp)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention.py)（example）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention_grad.py)（example）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DropoutGenMaskKernelNpuOpApi.cpp)（implementation）

- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention.py)（example）

- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention_grad.py)（example）

- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fusion_attention.py)（implementation）

- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fusion_attention.py)（implementation）
