---
type: API
title: SGL SwiGLU-OAI 的裁剪、INT8舍入与分组输出
description: 保留 swiglu_oai_quant 的gate单侧裁剪、up加一、dtype转换后截断和1536列倍数限制。
tags:
- task.implementation
- topic.compute.quantization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/swiglu_oai_quant.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_oai_quant.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/swiglu_oai_quant.py
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T16:15:45Z'
platforms:
- a2
- a3
- '950'
aliases:
- swiglu_oai_quant
---

# SGL SwiGLU-OAI 的裁剪、INT8舍入与分组输出

## 调用入口

```python
from sgl_kernel_npu.operators.activation import swiglu_oai_quant

def swiglu_oai_quant(
    x, alpha, limit, need_quant=True, group_list=None, group_list_type=None,
    *, impl="auto",
):
    ...
```

## 数学和量化约定

输入 `[...,2D]` 使用分半 `[gate|up]` 布局。gate只截上界limit，up截到±limit，然后FP32计算 `g*sigmoid(alpha*g)*(u+1)`。alpha须有限，limit须有限正数，均可由FP32表示；参与运算的浮点值须有限。

need_quant=False时转回输入dtype。开启量化时每行scale=`amax(abs(y))/127`；先把 `y/scale` 转为x.dtype，再向零截断并饱和为INT8。scale是恢复乘数，不是倒数；全零行的量化值与scale均零。不同后端可能在截断边界产生差别。

## 输入、输出及部分写入

x支持FP16/BF16/FP32 strided输入，非连续视图可经reshape/contiguous复制；D>0，前导维允许为空。分组可选非空同设备int32/int64 `[E]`：type=0的末项是累计总数R，type=1对计数求和；调用方保证非负、累计单调、`0<=R<=S`以及int32可表示，其中S为展平行数。

返回out `[...,D]` 和FP32 scale `[S]`。量化时out为INT8，否则为x.dtype。分组时只定义前R行；关闭量化时scale全部未定义。算子不改输入，空输入不启动kernel，不做token重排。

## 分发和验证边界

auto选择triton，无自动回退。Triton开启量化要求D为1536的倍数，关闭量化无该倍数要求；整行激活仍须放入片上存储，因此倍数合法不等于任意大D都支持。当前NPU须设置为输入设备。group数值不回读检查；参考分组路径可能同步设备。

显式torch_native作为对照，比较有效out和量化开启时的有效scale；不比较padding或未定义scale。需要精确定位误差时检查中间cast及截断边界，不能改成一次FP32到INT8转换。

## 旧activation分半接口的实际差异

同一固定commit还保留 `sgl_kernel_npu.activation.swiglu_oai_quant.swiglu_oai_quant`，参数顺序为(x,alpha,limit,need_quant=True,group_list=None,group_list_type=None)，无impl/registry；其JIT为旧模块的 `_swiglu_oai_quant_kernel`。这里保存旧实现Reference，**本卡原公共入口的检查、产品范围与零行INT8合同不自动传播到旧模块**。它与[旧偶奇交错OAI](/model/inference/apis/sgl_kernel_npu/sgl_legacy_swiglu_oai_interleaved.md)又是不同布局，不能因名字相同混用。

### 数学、精度与零scale

旧入口同样使用[gate|up]分半，gate限上界、up限±limit，计算g*sigmoid(g*alpha)*(up+1)。load后未显式.to(float32)，Host也不把alpha/limit强制float；中间promotion、primitive近似和最终cast由Triton类型/编译器决定。不能由公共docstring“FP32”补造旧源码中的转换。

True分支scale=amax(abs(out)).to(float32)/127，存FP32逐row scale，随后逐1536片：

```text
旧: normalized=(slice.float32/scale).to(x.dtype)
新: normalized=(slice.float32/where(scale==0,1.0,scale)).to(x.dtype)
两者: normalized.cast(int8,overflow_mode="saturate") -> masked store
```

旧行全零时存储scale=0，归一化仍执行0/0；不能保证payload为0，也不能从未执行的NaN→INT8转换编造特定整数输出。新版替换的只是归一化除数，仍存scale=0；因此公共“全零payload/scale均零”不能作为旧入口无条件合同。有限非零scale下，两者仍需保留“归一化后先回x.dtype，再饱和INT8转换”的精度步骤，不能替换成floor(z+0.5)或一次FP32→INT8。

False分支跳过scale计算、1536量化片与所有scale store，直接把激活cast到x.dtype；始终分配并返回的FP32 scale整张未初始化。该分支不继承True的除零或最后slice问题，但仍有下面的Host/寻址边界。True没有epsilon下限，不同于[旧SiTU INT8](/model/inference/apis/sgl_kernel_npu/sgl_legacy_situ_int8.md)。

### Host、group与地址对照

| 项 | 旧activation入口 | 新implementation入口/公共wrapper |
|---|---|---|
| X处理 | reshape(-1,last_dim)，无.contiguous | reshape后.contiguous，保证packed |
| group处理 | 原Tensor直接传入；E=shape[0] | group.contiguous；E=numel |
| group检查 | 自身在设备属性查询后检查type0/1与int32/int64 | 公共wrapper先做相同两检查；raw implementation自身不运行这些检查 |
| 累计编码 | 读GL[E-1]，不是GL[E] | 读GL[E-1] |
| count向量A | int64按8项/int32按16项align_up | 64/group.element_size计算alignment |
| alpha/limit | 原参数runtime传入 | float(alpha)、float(limit) |
| 空S | 无Host短路，仍查询helper与launch，最后reshape(...,-1)也须可推断 | 分配out/scale后rows==0立即返回 |
| 输出shape | empty[S,D]，return reshape(*orig_prefix,-1) | empty[S,D]，return reshape(*orig_prefix,D) |
| None group | HAS_GROUP_LIST=False，传None/E=A=1/type0和S | 同样跳过group读取 |
| 参数校验 | 没有完整dtype/device/连续/偶H/finite/positive guard | 公共书面合同亦不能当每项均有实际guard |

两者count都masked load other0、各项转int32再sum，累计只转最后一项；均无R值回读/上界clamp。旧多维group只按shape0取E，且不处理stride，不能推广为new的numel定义。旧empty group的累计可落到[-1]，没有专门拒绝；count零长向量还需满足编译前提。旧reshape可保留padded row stride，Device没有stride参数，不能借view成功宣称正确packed访问。奇H未被旧Host拒绝，C=floor(H/2)只用前2C项；行步长仍H，不是交错OAI的2C步长。

### 单JIT图、尾块与资源

四GM ptr为X/group/out/scale，runtime scalar为alpha、limit、total_rows；constexpr为TOTAL_COLS=H、HALF_COLS=D、COL_BLOCK_SIZE=1536、E/A、GROUP_LIST_TYPE、NUM_CORES=P、DTYPE_MAX=127、SCALE、HAS_GROUP_LIST，共17形参。旧helper取AIV数P，grid=(P,)，multibuffer=True，无autotune、额外Kernel或workspace。group读取后n=ceil(R/P)，每program处理[pid*n,min((pid+1)*n,R))；dense R=S，grouped R由Device得。地址row*H/row*D没有显式int64 cast，无新版SiTU的大N headroom检查。

每row整H项load再extract gate/up，True量化片仅使最终payload store masked；它不限制整行激活SSA，也不保护此前extract(size1536)。D不是1536倍数时最后片可能超过逻辑out[D]，Host自身未拒绝。公共接口书面要求的1536倍数是准入合同，不是旧Host已实现的ValueError；即使倍数合法，整行资源/arange形状仍需编译器准入。False不执行1536片，但整行资源前提仍在。

合法packed、0<=R<=S与调度整数域下，out/True scale只写前R行，padding empty未写。GM X容量SH*dx，INT8 out SD B/scale4S B，False out SD*dx B/scale4S B；有效True流量RH*dx+RD+4R，False为RH*dx+RD*dx，加count的P*E*dg或累计P*dg。逻辑cur_x为H元素、gate/up/out各D元素，算术dtype随promotion；量化片1536项、normalized FP32为6144 B后转x dtype/INT8。无手工UB/L1/L0/queue/event、atomic/barrier，逻辑SSA不等于确定物理峰值，multibuffer也不证明双buffer字节。

旧/new helper来自两个独立模块，均零参数functools.cache当前设备AIC/AIV，cache不含device，不保证共享状态或切设备后刷新。输入、group、新out/scale与可能的reshape临时需存活到当前流完成；无跨stream/alias保护。False scale和padding不可用于比较；合法有限非零scale可比较公共同数学，零scale必须保留版本差异。上述均为静态阅读，未执行任何旧Kernel验证。

[新版浮点完整源码卡](/model/inference/operators/direct/nn/activation/sgl_swiglu_oai_float.md)与[新版INT8源码卡](/model/inference/operators/direct/nn/activation/sgl_swiglu_oai_quant.md)保存其当前Direct实现；本补充避免把它们当旧Host/零scale的无条件替代，不新增重复数学Operator。


## 固定来源与验证状态

- [activation/swiglu_oai_quant.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/swiglu_oai_quant.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

- [python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_oai_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_oai_quant.py)（implementation）：旧/新halfSplit路径与helper差异证据。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py)（implementation）：旧/新halfSplit路径与helper差异证据。
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/swiglu_oai_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/swiglu_oai_quant.py)（header）：旧/新halfSplit路径与helper差异证据。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)（implementation）：旧/新halfSplit路径与helper差异证据。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py)（implementation）：旧/新halfSplit路径与helper差异证据。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
