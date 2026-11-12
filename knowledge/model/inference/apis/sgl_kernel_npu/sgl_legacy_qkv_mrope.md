---
type: API
title: SGL旧QKV RMSNorm与多轴MRoPE的频率、gate及部分旋转合同
description: 说明triton_split_qkv_rmsnorm_mrope的三轴频率选择、Q/gate解交错、全维RMSNorm后部分NeoX旋转、均衡分核与弱guard；平台未定位。
tags:
- task.implementation
- topic.attention
- topic.multimodal
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_mrope.py
  role: primary
created_at: '2026-11-09T15:36:24Z'
updated_at: '2026-11-09T15:36:24Z'
platforms: []
aliases:
- triton_split_qkv_rmsnorm_mrope
- split_qkv_rmsnorm_mrope_kernel
---

# SGL旧QKV RMSNorm与多轴MRoPE的频率、gate及部分旋转合同

## 入口与证据范围

```python
from sgl_kernel_npu.norm.split_qkv_rmsnorm_mrope import triton_split_qkv_rmsnorm_mrope

triton_split_qkv_rmsnorm_mrope(
    qkv, q_weight, k_weight, cos_sin,
    num_q_heads, num_kv_heads, head_size, eps,
    mrope_section, is_interleaved,
    rope_dim=None, q_bias=None, k_bias=None, has_gate=False,
)
```

本卡固定sgl-kernel-npu dda6d36b0cdb4081e102d14c0a2fb276fc416e69的旧norm模块，未在该固定树找到相应新implementation注册入口。它是一次纯Triton Vector launch，包含拆分、Q/K RMSNorm与多轴频率RoPE，不含矩阵投影、KV缓存写入或gate激活。当前缺少覆盖该旧入口完整数学的逐平台公开支持与活动CI证据，保留draft/platforms=[]，不猜测CANN版本，也不声明特定平台完整Operator闭包。

模型接入上下文见[Qwen3-Next/3.5混合注意力准备](/model/inference/guides/sglang_ascend/sglang_ascend_model_qwen_hybrid_attention.md)，其一段模型调用说明不替代本卡的Device合同。[普通QKV与RoPE接口](sgl_split_qkv_rmsnorm_rope.md)及[position-cache版本](/model/inference/operators/direct/transformer/posembedding/sgl_split_qkv_rmsnorm_rope_pos_cache_half_npu.md)有不同参数/频率入口，不按名称互换。

## 输入、输出与物理布局

令T=qkv.shape[0]、D=head_size、Hq=num_q_heads、Hk=num_kv_heads、Q=Hq*D、K=Hk*D、G=Q if has_gate else 0。Kernel把每行解释为紧密Q+G+2K个元素，忽略qkv实际stride与shape第1轴；cos_sin也按紧密地址解释。

| 参数/输出 | 实际消费布局与行为 |
| --- | --- |
| qkv，has_gate=False | [T,Q+2K]每行[allQ,allK,allV]，Q按[Hq,D]、K按[Hk,D]归一化 |
| qkv，has_gate=True | 首2Q元素按[Hq,2D]解释，即每head的[Q_h,gate_h]交错；其后allK、allV。不是[allQ,allGate]两个全局段 |
| q_weight/k_weight | 各读取前D项，广播所有本类head；直接乘weight，不自行做1+weight。模型须先按其norm定义准备有效gamma |
| q_bias/k_bias | 是否启用两者仅由q_bias is not None决定；q_bias缺省会忽略单独k_bias，q_bias存在而k_bias缺省没有Host成对guard |
| cos_sin | 预期物理[3,T,R]，R=rope_dim，每轴每token前R/2为cos、后R/2为sin；调用者已按位置取表，本函数没有positions参数 |
| mrope_section | Host只直接读取[0]/[1]/[2]，分别作为时间/高度/宽度轴配置；无长度、非负或总和检查 |
| rope_dim | None取D；仅按R!=D决定partial；预期正偶数R<=D，否则extract/reshape不能按目标数学解释，Host未校验 |
| q_output/k_output/v_output | 新连续[T,Q]/[T,K]/[T,K]，均继承qkv.dtype/device；Q/K为归一化和旋转结果，V原值复制 |
| gate_output | 新[T,G]，与qkv同dtype/device；G0时仍返回[T,0]Tensor，启用时复制解交错gate，不做sigmoid/SiLU |

Host没有统一检查rank、dtype、NPU、同device、连续性、各权重/bias/cache容量、head正数/整除、eps有限正值、R合法性或索引乘法范围。以下是固定body的地址和算法事实，不把未拒绝的输入扩成正式支持域。

## 三轴频率选择与旋转公式

对旋转半维坐标d=0..R/2−1，逐token i读取三轴cos/sin；时间cos地址i*R+d，高度再加T*R、宽度再加2T*R，sin各在本轴cos后加R/2。

| 选择 | 时间mask | 高度mask | 宽度mask |
| --- | --- | --- | --- |
| is_interleaved=False | d<section_t | section_t<=d<section_t+section_h | section_t+section_h<=d<section_t+section_h+section_w |
| is_interleaved=True | 非高度且非宽度 | d%3==1 且 d<=3*section_h | d%3==2 且 d<=3*section_w |

特别是interleaved分支的时间mask取补集，section_t在该分支不参与计算。非interleaved若三section之和小于R/2，剩余坐标的三mask都False，cos/sin读other0后相加得到0，旋转输出相应变0；它不是自动保留原坐标。Host未检查这些配置，调用者应使频率轴定义与模型一致。

三轴分别masked load并other0，相加后转FP32，选中的半表广播为两份[cos_half,cos_half]和[sin_half,sin_half]。**is_interleaved选择多轴频率排列，不改变旋转配对**：本kernel始终把旋转前缀切成两个半向量x1/x2，组成[-x2,x1]，即NeoX半区配对，而非相邻偶/奇维配对。

Q/K各head先在完整D维FP32计算rstd=1/sqrt(sum(x*x)/D+eps)，normalized=x*rstd*weight，可选再加bias。R<D时只对normalized的前R维做rot=normalized_prefix*cos+[-x2,x1]*sin，再insert_slice回前缀；后D−R维保留归一化/affine结果。R==D直接以旋转结果作为全部Q/K。store处转qkv.dtype，norm与RoPE之间没有显式BF16/FP16中间物化；V按输入dtype直接复制，gate先读转FP32再转回输出dtype。

## 分核、调用链与资源

get_vectorcore_num每次查询torch.npu.current_device的num_vectorcore，<=0抛RuntimeError；没有无参数@cache。这与很多旧norm helper首次设备缓存不同。函数没有把current device切到qkv.device，调用方须使当前NPU、输入和stream环境相容。

设C为查询核数。front_core_num在T%C非零时取T%C，否则取C；frontRows=ceil(T/C)，tailRows=floor(T/C)。仅当T>C才设tail_core_num=C−front_core_num，否则tail0。blockDim=min(C,front+tail)。前front个program负责frontRows个连续token，后tail个负责tailRows个；后段起点front*frontRows+(pid−front)*tailRows，覆盖不重叠。T<C且非空只启动T个program；T为C倍数时全部C个front program分相同整行数。

```text
Host query当前NPU vector核→计算Q/K/G/R与balanced token slices→分配四输出
→split_qkv_rmsnorm_mrope_kernel(blockDim)
  每program先load一次Q/K weight和可选bias
  对自己连续token区逐token：
    读Q或[Q_h,gate_h]；读K/V
    三轴masked load cos/sin→按axis mask合并→复制半表
    Q/K完整D RMSNorm和affine
    NeoX半区旋转前R维；partial时insert回完整normalized
    写Q/K/V和可选gate
```

T0没有Host早退：front_core_num=C、frontRows0、blockDim=C；每program仍在零次token循环前载入weight/bias。不能把输出为空推导为不launch、不读任何输入，或者允许无效权重指针。

JIT显式do_not_specialize num_tokens、front_core_num及两种每核token数；head、Q/K宽、eps、bias、axis排列、R和gate尺寸等为constexpr。每次Host把section三项作为运行参数传入。读Q/K/V/gate没有全局特征尾mask，tl.arange直接使用D、Q、K或Q+G；Triton形状/切片准入须由匹配编译器满足，Host未补齐或选择另一body。

新增输出GM共T*(Q+2K+G)*sizeof(qkv.dtype)字节，无显式workspace、TQue或跨program通信/atomic。主要逻辑工作集为FP32的Hq×D Q、Hk×D K、可选Hq×2D gate读取、归约向量、Q/K旋转前缀及cos/sin R表；weight/bias每program读一次跨本核token复用，V仅复制。局部slice/insert/broadcast可能被编译器别名或物化，固定Python源码未给物理UB/寄存器/L1/L0字节、double buffer或pipe事件，不能用逻辑张量长度相加声称容量已通过。不同program只写自己的token输出，无自有跨program barrier；输入/输出Tensor寿命仍由Torch/Triton异步框架管理。

## 扩展解析、fake与适用边界

模块导入时优先从triton.language.extra.cann.extension解析extract_slice/insert_slice；未导入该扩展或缺少对应属性时，改从tl取同名属性。若两者都缺失会在导入解析失败；没有自动Torch数学fallback。该通用primitive/编译器与安装二进制不在本固定源文件的实现闭包内。

triton_split_qkv_rmsnorm_mrope_fake只按参数分配上述四个empty Tensor，没有RMSNorm或RoPE数值，也不查询core；源文件没有为它注册torch.library fake装饰器。函数存在不证明图编译已经调用或正确lower到真实kernel，不能把shape占位结果当数值输出。

当前Source中的gate解交错、三轴频率、RMSNorm后partial旋转和弱guard已经保存；平台/编译器/运行数值/图捕获仍需独立证据。本次知识提取未执行上游、编译、真机、数值、图或性能测试。

## 固定源码

- [norm/split_qkv_rmsnorm_mrope.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_mrope.py)：Host、两解析helper、唯一JIT与未注册fake函数。
