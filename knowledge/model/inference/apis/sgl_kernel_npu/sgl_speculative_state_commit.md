---
type: API
title: "SGL 投机状态快照提交与卷积窗口回滚接口"
description: "区分旧mover、KDA目的stride mover、通用scatter与卷积rollback的真实布局、负step、别名和异步生命周期；平台未定位，不冒充完整Operator。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/mamba_state_update_triton.py
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/speculative_state_scatter.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_mamba_state_update.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/scripts/run_kernel_tests.sh
    role: supporting
created_at: "2026-11-09T13:44:57Z"
updated_at: "2026-11-09T13:44:57Z"
platforms: []
aliases:
  - move_intermediate_cache
  - move_intermediate_cache_kda
  - conv_state_rollback
  - speculative_state_scatter_npu
---


# SGL 投机状态快照提交与卷积窗口回滚接口

本卡固定到 sgl-kernel-npu 提交 dda6d36b0cdb4081e102d14c0a2fb276fc416e69，整理四个 legacy Python Direct helper 的合同与实现边界。它是 API Reference 草稿，平台仍未定位，不声明完整 Operator、source_closed、图捕获、数值或性能验收。四个接口共享投机状态管理主题，但快照复制与窗口右移是不同状态操作，不能互相替换。

## 先按状态语义和布局选入口

| 入口 | 真实操作 | 状态轴与stride | 返回/可变对象 |
|---|---|---|---|
| move_intermediate_cache | 每request取指定srcslot/step快照，覆盖所有层对应dstslot | src[L,S,D,H,V,K]仅前三轴传stride，HVK tail按dense物理线性；dst[L,P,H,V,K]只前两轴用真实stride，tail也按dense物理顺序 | 返回原ssm_states对象；原地写dst |
| move_intermediate_cache_kda | 同快照复制，适配目的VK平面非连续视图 | src同前、HVK tail仍dense；dst真实layer/slot/H/V/K strides全部用于地址 | 返回原ssm_states对象；原地写dst |
| speculative_state_scatter_npu | 每request取指定snapshot，支持1..3维一般tail | dst[L,P,*tail]、src[L,S,D,*tail]，tail逻辑shape相同；两侧每个tail stride均参与地址 | 返回原dst；原地写dst |
| conv_state_rollback | 按draft宽与最后step把卷积窗口的旧前缀右移到对应位置 | state[L,P,W,C]所有四轴stride参与；不从snapshot缓冲读完整历史 | 有request时返回原state；空request直接返回None |

前两mover的高层复制目标相近，实际地址规则、tile/loop和空输入不同；通用scatter也不能当成旧mover的逐字alias。rollback只做窗口内右移，不计算卷积，不检查接受token，也不替SSM快照复制。调用方须同时维护模型要求的两类状态，不能仅据一个helper返回成功视作整轮状态机已提交。

四个实际导入：

```python
from sgl_kernel_npu.mamba.mamba_state_update_triton import (
    move_intermediate_cache,
    move_intermediate_cache_kda,
    conv_state_rollback,
)
from sgl_kernel_npu.mamba.speculative_state_scatter import speculative_state_scatter_npu
```

## 快照mover的输入与合同

```python
move_intermediate_cache(
    ssm_states, intermediate_state_cache,
    dst_indices_tensor, src_indices_tensor, last_steps_tensor,
    h_block_size=2,
)
move_intermediate_cache_kda(
    ssm_states, intermediate_state_cache,
    dst_indices_tensor, src_indices_tensor, last_steps_tensor,
    h_block_size=1,
)
```

| 参数 | shape/意义 | Host实际检查与转换 | 调用方仍须保证 |
|---|---|---|---|
| ssm_states | 通常[L,P,H,V,K]目的池 | 读取前两stride；KDA再读末三stride；不复制/不转换 | rank/shape、dtype/device、容量、别名与合法stride |
| intermediate_state_cache | [L,S,D,H,V,K]候选源 | 按六维解包；读取layer/slot/step实际stride | tail HVK为dense物理顺序；层数/尾维与dst兼容 |
| dst_indices_tensor | [R]目的slot | 只assertlen与last_steps相等，不转换 | 整数、连续/实际load所需布局、同device、非负且<P |
| src_indices_tensor | [R]源slot | 同上 | 非负且<S |
| last_steps_tensor | [R]源step | 不转换；Device先load并判断<0 | 非负有效值<D；负值表示本request跳过 |
| h_block_size | 默认2或KDA1 | 直接constexpr，不round或guard | 正POT静态arange前提及compiler资源 |

Host未验证两个state Tensor同dtype；预期是同dtype快照复制。若混dtype，tl.store会沿目的pointer类型处理，但本卡不把任意混合格式扩大为有效合同。metadata未自动cast/contiguous或迁移device；不能把通用scatter的预处理能力套给这两个旧mover。

generic mover按grid=(R,)启动，R0没有earlyreturn，会形成零grid，runtime结果未验证；KDA mover在R0直接返回ssm_states，不提交JIT。两者都没有过滤Host nonzero/动态压缩，负step在Device统一跳过。

### 真实地址与tile

记source前三stride为sL/sS/sD，destination前两为dL/dS：

```text
src_base = src + I64(l)*sL + I64(src_idx)*sS + I64(step)*sD
dst_base = dst + I64(l)*dL + I64(dst_idx)*dS
src_tail = h*V*K + v*K + k
generic dst_tail = h*V*K + v*K + k
KDA dst_tail = h*dH + v*dV + k*dK
```

每program对应一个request索引，先读dst/src/laststep三个metadata；step<0直接return，其它负slot没有单独mask。再按层循环、H按h_block_size分片：

- generic BLOCK_V=nextPOT(V)，BLOCK_K=nextPOT(K)，一次处理整个V宽，没有V外层循环；逻辑tile[h_block_size,BLOCK_V,BLOCK_K]，联合H/V/K mask，load other0。
- KDA BLOCK_V64、BLOCK_K=nextPOT(K)，H片内再for v_start=0..V step64，覆盖全部V片/尾；目的地址用真实dH/dV/dK，但src tail仍dense，不能宣称任意source非连续tail受支持。
- source/destination slot、step只检查step<0，没有正向上界检查，也没有对重复dstslot、src/dst跨request重叠做atomic或串行化。

generic目的视图非连续时，真实tailstride被忽略：它复制到目的base后的**物理线性HVK顺序**，不会维护任意目的logical view的逐元素对应。若调用方确实要求物理reshape后的内容，这可以是其合同；若要求按该view的H/V/K逻辑元素复制，须用KDA或通用scatter适合的stride规则。不能把所有非连续dst都简单说成“调用必失败”，也不能依据前两stride真实就宣称全tail strides都正确。

## 通用stride快照scatter

```python
speculative_state_scatter_npu(dst, src, dst_indices, src_indices, step_indices)
```

预期dst[L,P,*tail]，src[L,S,D,*tail]，tail rank1..3且shape逐轴相同；数据Tensor同dtype/device。source Host按真实顺序检查：

1. dst.ndim≥3且src.ndim=dst.ndim+1；两者layer数及tail shape相同、dtype/device相同；三个indices必须1D且numel相等。
2. R0直接return dst，此时尚未检查indices设备和tail rank1..3；不能把这个空请求返回当成后续约束均已验证。
3. 非空请求要求indices设备等于dst设备，tail rank1..3；将tail前面补到三维的1，缺失stride补0，读取dst[0,0].numel作为tail_numel。
4. BLOCK=min(1024,nextPOT(tail_numel))，TAIL_GRID=ceil(tail_numel/BLOCK)，LOGICAL_GRID=R*L*TAIL_GRID，PHYSICAL_GRID=min(48,LOGICAL_GRID)。
5. 三metadata分别.to(torch.int32).contiguous后提交JIT，return原dst。没有数据contiguous、dtypecast、目的statecopy。

每physicalprogram以PHYSICAL_GRID步长处理所有logicalpid，拆成request/layer/tailtile。tail线性index经TAIL_DIM_1/2拆为三坐标，source与dest各自layer/slot/step/tailstride参与，不要求dense tail。metadata每个logicaltile都读，转换为I64再组地址。源码核心mask：

```text
valid = dst_idx>=0 and src_idx>=0 and step_idx>=0
mask = valid and tail_offset<tail_numel
value=tl.load(src+src_strided_offset,mask,other=0)
tl.store(dst+dst_strided_offset,value,mask)
```

因此任意一项负索引会关闭该request所有data读写，但metadata仍被读取、地址表达式仍可被构造；这不是无操作kernel或无需有效indices buffer。非负slot/step的上界仍未检查，cast I64→I32的大值窄化可能改变值/符号，不能把“转I32连续”当值域验证。

fixed48是Host上限常量，不是查询到的当前硬件核数。gridstride网络能覆盖logical_grid大于48的任务；没有每请求固定一个physicalprogram的假设。Host没有明确处理非空请求下的空layer/slot/tail：dst[0,0]索引、nextPOT/TAIL_GRID与零physicalgrid等边界不能改写成可靠no-op。数据dtype相等虽检查，metadatadtype没有限定为I32/I64，实际会尝试.toI32，调用方仍应提供合法整数索引。

此helper docstring提到negative device mask方便graph capture；可从source确认没有按索引内容执行Host nonzero/tolist或动态压缩。本次未执行图捕获，不因此声明任何框架/设备组合capture已通过。

## 卷积窗口回滚

```python
conv_state_rollback(
    conv_states,       # [L,P,W,C]
    state_indices,     # [R]
    step_indices,      # [R]
    draft_token_num,
)
```

Host先取R=state_indices.shape0，R0直接无值return，因此返回None且不再校验state rank、indexrank/相等长度。非空时检查state4D、两index1D且同长度，取四轴实际stride，把indices各转I32/连续，grid=(R,)启动；无same-device、data dtype、slot/step值域、draft正数或channelPOT完整检查。

每program读I64 state_idx、step_idx，step<0直接return；否则shift=(draft_token_num−1)−step。shift≤0不回滚；0<shift<W时遍历全部层，从window_idx=W−shift−1向0递减，读原位置再写window_idx+shift。下降顺序是同program右移防覆盖机制，不能改成正向覆盖后继续读。只移动旧前缀到右侧，前shift项保持旧值，不清零、不从inputtokens重建。

```text
for layer:
 for q=0..W-shift-1:
   w=W-shift-1-q
   src=layer*sL+state_idx*sP+w*sW+arange(C)*sC
   dst=layer*sL+state_idx*sP+(w+shift)*sW+arange(C)*sC
   data=load(src); store(dst,data)
```

这里arange(C)未nextPOT且没有channel mask，C须满足正常静态arange前提；非POT/非正C的编译行为未验证，不把它虚构为已运行错误或已兼容。shift≥W时上述loop无有效移动，source未另行报错；state_idx负值/超上界也没有保护。相同state_idx若出现在多个request，两个program可能重复移位或并发覆盖，无锁/atomic，不保证与串行单次右移等价。source/dest是同一state对象，真实四轴stride被保留，返回原对象/stride，未分配新的state。

## step索引、接受数量与bonus边界

两个mover和scatter直接把last_steps/step_indices作为source快照的**零基step轴下标**；rollback用同样的step值计算D−1−step，D是draft_token_num。它们都不执行“接受长度减一”、去bonus或从token数推snapshot编号，也没有num_accepted_tokens输入。

因此外层接受数量（尤其包含bonus的计数）不能未经协议转换直接当这里step下标。固定两实现文件没有定义外层计数是否含bonus，也没有唯一转换公式；调用方必须根据保存快照时的step编号和接受协议传正确下标，本卡不凭命名补造accepted−1或accepted−2。负step的源码含义是跳过：mover/rollback在Deviceearlyreturn，scatter通过负值mask。已经被接收的token数量、最后候选step和bonus模型输入是三种不同量，边界由实际调用方决定。

测试定义中mover的last_step_pos来自0..D−1，直接索引src[:,srcslot,step]，明确了这层API的step含义；它没有建立所有上层接受协议。某条reference函数对负step仍按shift=(D−1)−step做右移，而实际rollback kernel先step<0跳过，这个固定来源内部差异必须保留，不能挑较宽参考覆盖Device行为。

## 内存、异步生命周期与错误边界

四个接口均没有自有GMworkspace/ACLNNexecutor或持久metadata缓存。mover数据不做Hostcopy，直接写caller目的；scatter/rollback只可能为index.toI32.contiguous生成临时metadata Tensor，不创建私有目的state。已I32且连续时转换可alias；其它情况新增对应R*4B索引copy。没有tensor_cache、nonzero压缩或设备属性cache，不能沿用GDN chunk metadata的identity失效结论。

逻辑每有效快照request读取/写入L*tail_numel个元素；generic/KDA tail_numel=H*V*K。generic本地逻辑tile=h_block_size*nextPOT(V)*nextPOT(K)元素；KDA=h_block_size*64*nextPOT(K)；scatter为BLOCK≤1024的一维tile；rollback每window位置处理C元素。primitive load/store与compiler UB/reg/排布属于Triton边界，source没有InitBuffer/TQue/TBuf、显式dynamicUB、手工event或物理UB字节账；不把这些logicaltile升格为完整Operator资源闭包。

同program load→store/迭代次序依JIT compiler memorydependency，程序之间无跨核同步/原子或目的去重。source未显式同步Device、record_stream或自由释放；return原Tensor不等于异步搬移已完成，调用方应保持state/source/metadata到消费并用框架stream排序保护后续读取。源码没有检测src/dst/storage互alias是否安全，跨program读写同一片不能由单program的下降窗口循环推得安全。

Python形状assert/ValueError与Tensor转换错误直接传播；JIT/primitive失败无fallback，不转Torch或其它helper。若metadata非法或index值越界，source没有统一错误码或自动恢复，不能用空域/负step已有mask概括所有输入均有保护。

## 来源证据与平台缺口

两份实现文件已完整读取，所有三种快照JIT和rollback body均可定位。旧test_mamba_state_update.py定义BF16 snapshot copy、V65/128/129尾域、目的物理布局以及四轴stride窗口回滚比较；这些是测试定义，本次没有执行。

run_kernel_tests.sh将test_mamba_state_update.py从活动MAMBA_TESTS中注释，并写出strided-dst mismatch背景；KDA专用mover和通用scatter也没有在该活动列表中找到精确支持条目。不能将A3/950整组matrix、函数doc的“NPU”或fixed48独立提升为四个入口的公开整卡产品范围，所以本卡保留draft与platforms: []，不填写agnostic或猜测CANN版本。

可按实际用途核对：原始目标slot是否唯一、source/step上界、src/dst各tailstride、正/负step、空请求返回、非POT维度前提、copy后底层storage及下一轮状态消费。上述为可复核维度，不构成本次已通过的验证记录，也不将Reference当作正式VV Operator替代。

## 相关接入知识

- [Ascend混合线性注意力的SSM提交与卷积恢复](../../guides/integration/sglang_ascend/sglang_ascend_attn_hybrid_state_commit.md)：对应外层接受后双状态恢复；该Guide不替本页证明平台或自动转换接受计数。
- [Ascend KDA状态与专用mover](../../guides/integration/sglang_ascend/sglang_ascend_attn_kda_state.md)：对应V/K转置目的池与legacy通用mover区别；仍须按本页真实source stride合同选择入口。
