---
type: Operator
title: "LayerNormFwd A2/A3 Direct Invoke 算子知识"
description: "闭合独立输出的分组LayerNorm六种bias门控路线及groupmajor统计，保留Direct宽度截断、padding均值和48行编译准入边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/layer_norm_fwd.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/layer_norm_fwd.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml
    role: supporting
created_at: "2026-11-09T10:02:32Z"
updated_at: "2026-11-10T07:18:34Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# LayerNormFwd A2/A3 Direct Invoke 算子知识

## 算子速览

精确 `sgl_kernel_npu.implementation.triton.norm.layer_norm_fwd.layer_norm_fwd`，独立冻结 `is_rms_norm=false` 与独立output（outNone或无输入别名的预分配）。分组LayerNorm减均值、可选bias/SiLU前后门控，返回out、FP32mean、FP32rstd。六个有效bias/gate路线、自有Host/Device闭合，无dot/Cube，VV。

draft保留Direct绕过公共check、BLOCK_M48arange与padding/宽度guard缺失、设备缓存/资源及无运行边界；LN/RMS/inplace其它域独立任务。已全文读的[公开API](../../../../apis/sgl_kernel_npu/sgl_layer_norm_fwd.md)链接复用。

## 接口与语义

### 计算语义

x[M,N]，H=group_size或N，G=N/H。若z存在且norm_before_gatefalse，u=x*SiLU(z)，否则u=x。m=mean(u)，v=mean((u-m)²)，a=(u-m)/sqrt(v+eps)；y=a*weight+bias（可无）；若z存在且norm_before_gatetrue，再乘SiLU(z)。SiLU=z*sigmoid(z)，activation参数忽略。stats[g*M+row]为group-major，不能按row-major解释。

### 输入、输出与属性

| 项 | 合同/入口差别 |
|---|---|
| x | NPU三浮点dtype二维[M,N]、末stride1、N/H正整除、storage行无物理重叠；Direct未验证 |
| weight/bias | weight必需[N]末stride1，bias可None否则同shape；同device浮点 |
| z | None或同shape、末stride1，可独立行stride；FP32load后SiLU |
| group_size | None或正H且N%H0，H≤F=65536//dx；这些公共guard不在Direct链 |
| out | None用empty_like或独立[M,N]、末stride1预分配，返回该out，dtype取outdtype |
| eps/flags | eps建议正有限；冻结is_rms_norm=false，norm_before_gate控制有z时顺序，activation忽略 |
| stats | rstdFP32[G*M]；meanFP32[G*M]，输入device |

### 入口与版本

Direct签名(x,weight,bias,eps,z=None,out=None,group_size=None,norm_before_gate=True,is_rms_norm=False,activation=None)，本predicate必须显式保持。不包含原地写x任务。auto/triton仅转发；torch_native独立参考不并入图。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`；CANN9.1.0来自README/CI非本次运行，完整Tritonbinary未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

Direct直接解包M/N，H默认N、G=N//H，outNone才empty_like，分配stats；BLOCK_N=min(F,nextpow2H)，BLOCK_M48，helper取P，Kc=min(ceil(M/48),P)，grid(Kc,G)。没有publicshape/stride/group/widthguard，亦无dtype/device/eps/别名验证；M0没有专门快速返回，grid0运行行为未证。不连续化、不读设备值。

### 参数、Workspace 与生命周期

statsGM8GM B，output逻辑MNdy B，outNone新分配/预分配不新建；无请求方workspace/POD/ACLNN/其它scratch。helper无参cache/current_device、双核数assert，未绑定xdevice；metadata和output/输入异步存活依Torch/Triton，未显式stream/wait/warp/stage。当前合同为独立输出：输入存储须保持有效且完成前不得并发改写；原x只读，可并发读取。输出及统计量须在正确同步确认Kernel完成后消费。

### 启动图与失败传播

import→Direct参数/输出stats分配→helper→单JITKernel→return(out,mean,rstd)。heuristics以B/Z是否None生成HAS_BIAS/HAS_Z；无fallback/CPU核心数学。publicshape/stride/宽度检查只在门面调用前执行，Direct不借用它们；异常直接传播，package原生库仅导入前提。

## Route 与参数设计

### 分核与资源计算

Kc=min(ceil(M/48),P)，group g∈[0,G)，program p∈[0,Kc)轮转rowstart=p48+j48Kc。每tile48行×BLOCK_N列，W/bias在循环外按group偏移预读；stats指针+=gM，X/Y/Z列偏移+=gH。合法H整除N且H≤F时全覆盖；超H时非自动列分块。

### Route 选择

固定IS_RMS_NORM=false，六有效执行类=HAS_BIAS两状态×Z无/前门控/后门控三类。HAS_Zfalse时norm_before_gate两bool实例语义和执行读集合相同，表中合并并明确未漏实例。outputNone/独立prealloc同数学Kernel，allocationHost路线区别已列。

### 模板/实现执行矩阵

| Route | HAS_BIAS | HAS_Z/NORM_BEFORE_GATE |
|---|---|---|
| R-001 | false | false / both |
| R-002 | false | true / false |
| R-003 | false | true / true |
| R-004 | true | false / both |
| R-005 | true | true / false |
| R-006 | true | true / true |

三浮点输入和合法输出/参数dtype，全部显式loadFP32/输出转换，statFP32；不同norm/inplace单独冻结，不混卡。无dot/Cube/AIC/MIX自有节点，选VV而非目录推定。

### 隐藏性能 Guard

BLOCK_M48直接tl.arange(0,48)非二次幂，具体CANNextension准入未固定，不断言编译失败。DirectH>F使BLOCK_N=F<H，只处理group前F列/统计仍除H/尾输出不写，源码无throw；不能把public“Feature dim too large”当Direct可达保护。LN xload未other，mean先sum整BLOCK_N，H非二次幂时maskedlane是否0不能凭源码确认；后续xbarwhere无法修复已污染mean。物理UB、行offset整数域无完整guard。

### POD/ABI

| 字段 | 分类/消费 |
|---|---|
| X/Y/W/B/Z | runtimeTensor，X/W/B/Z读、Y写；B/Z可None |
| Mean/Rstd | runtime stats指针；各groupmajor写 |
| stride_x_row/stride_y_row/stride_z_row | runtime实际行元素stride，ZNone传0 |
| M/N | runtime行数/组宽H（DeviceN不是Host总宽N） |
| eps | runtime→sqrt分母 |
| BLOCK_M/BLOCK_N | constexpr48/min(F,nextpow2H) |
| HAS_BIAS/HAS_Z | heuristicsconstexpr，由B/ZNone状态 |
| NORM_BEFORE_GATE/IS_RMS_NORM | constexpr顺序/false |
| grid | (Kc,G)；group程序id1 |

无自定义POD/序列化字节offset；JITABI/整数位宽/physicalbuffer外部，不虚构tiling结构。

### Route 源码闭包

完整162行Direct/Device与public全部适配/guard、helper已读；核心无外部Torch数学，框架只分配/metadata。根setup→stage_runtime完整Python包→build_wheel/setup_refactor，norm/backendinit无Device；sigmoid/reduction/sqrt与physicalallocation为外部primitive边界。

## Kernel 实现

### 公共执行流程

groupmajor指针偏移→W/bias预读→48行轮转maskedload→可选pregate→LNstatsstore→affine→可选postgate→真实strideoutputstore。输出独立于所有输入。

### Route R-001：bias=false gate=none

#### 适用条件

##### 选择证据

冻结IS_RMS_NORM=false、outNone或独立预分配无输入别名；HAS_BIAS=false，HAS_Zfalse，两种NORM_BEFORE_GATE均无有效分支，heuristics只依据B/Z指针是否None。

#### Device 数据流

##### 函数级调用链

`layer_norm_fwd→helper→_layer_norm_fwd_1pass_kernel_npu→loadFP32→mean/centeredvariance→affine→stats/outputstore`。无其它自有Kernel/Cube节点。

##### 源码等价伪码

group g、program p轮转rowstart=p48+j*48Kc。load W[gH+cols]一次；每tile rows48、colsBLOCK_N按全M/Hmask读xFP32；u=x；mean=sum(u)/H，xbar=where(cols<H,u-mean,0)，var=sum(xbar²)/H并存mean[gM+rows]；rstd=1/sqrt(var+eps)存统计；a=(u-mean)*rstd*W；按真实Ystride与row/colmask写出。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| x/u/xbar/y | 各48×BLOCK_N FP32逻辑张量，单张量192*BLOCK_N B，不等实际物理峰值 |
| z | 不读取 |
| W/bias | BLOCK_N逻辑lane，合法H；W总Kc*N*dw B，bias0 |
| mean/rstd | 各48FP32；两GM数组各4GM B |
| out | 新建或独立提供MN*dy逻辑payload |
| UB/workspace | 无显式分配/请求，compilerphysicalallocation外部 |

##### 分层内存布局

`GMstridedx→FP32tile[48,BLOCK_N]→mean/centeredvar→rowrstd→affine→GMout；stats以group-major另写GM`。x/zload均未指定other；LNmean先sum全BLOCK_N，若maskedlane无确定0会污染mean。

##### 字节账与复用顺序

合法H≤F、G=N/H、rowstorage不交叠域，逻辑流量 `MN*(dx+dy) + Kc*N*(dw) + 8GM` B；独立output可能保留layout，按真实stride寻址，不把payload字节当GMspan。statsallocation8GM B，outNone另由empty_like分配，预分配则本调用不新建；无scratch/workspace。输入/输出/统计异步存活归框架。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 精确边界 |
|---|---|
| 划分 | group列区间[gH,(g+1)H)、48行块轮转唯一，逻辑输出不交叠 |
| x/Y别名 | 本冻结域输出不alias输入，不改变x/参数 |
| padding | load未other，mean无colmasksum：BLOCK_N>H时零padding需具体primitive合同，不能假定 |
| gate | 无zload/SiLU；norm_before_gate不影响算式 |
| 精度 | x/W/bias/Z显式FP32，1/sqrt；outdtype转换，statsFP32，无量化 |
| 行尾 | rows<Mmaskload/store/stats；cols<Hmask，BLOCK_M48arange扩展准入另核对 |
| 同步 | SSA依赖/循环交compiler，无显式barrier/atomic，跨流消费归框架 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| heuristics/weight | [Device前段](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L14-L53) |
| load/gate/stats | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L55-L84) |
| affine/postgate/output | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L86-L102) |


### Route R-002：bias=false gate=pre

#### 适用条件

##### 选择证据

冻结IS_RMS_NORM=false、outNone或独立预分配无输入别名；HAS_BIAS=false，HAS_Ztrue/NORM_BEFORE_GATEfalse，heuristics只依据B/Z指针是否None。

#### Device 数据流

##### 函数级调用链

`layer_norm_fwd→helper→_layer_norm_fwd_1pass_kernel_npu→loadFP32→x*SiLU(z)→mean/centeredvariance→affine→stats/outputstore`。无其它自有Kernel/Cube节点。

##### 源码等价伪码

group g、program p轮转rowstart=p48+j*48Kc。load W[gH+cols]一次；每tile rows48、colsBLOCK_N按全M/Hmask读xFP32及zFP32；u=x*(z*sigmoid(z))；mean=sum(u)/H，xbar=where(cols<H,u-mean,0)，var=sum(xbar²)/H并存mean[gM+rows]；rstd=1/sqrt(var+eps)存统计；a=(u-mean)*rstd*W；按真实Ystride与row/colmask写出。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| x/u/xbar/y | 各48×BLOCK_N FP32逻辑张量，单张量192*BLOCK_N B，不等实际物理峰值 |
| z | 48×BLOCK_N FP32逻辑，GM读MN*dz B |
| W/bias | BLOCK_N逻辑lane，合法H；W总Kc*N*dw B，bias0 |
| mean/rstd | 各48FP32；两GM数组各4GM B |
| out | 新建或独立提供MN*dy逻辑payload |
| UB/workspace | 无显式分配/请求，compilerphysicalallocation外部 |

##### 分层内存布局

`GMstridedx/z→FP32tile[48,BLOCK_N]→mean/centeredvar→rowrstd→affine→GMout；stats以group-major另写GM`。x/zload均未指定other；LNmean先sum全BLOCK_N，若maskedlane无确定0会污染mean。

##### 字节账与复用顺序

合法H≤F、G=N/H、rowstorage不交叠域，逻辑流量 `MN*(dx+dy+dz) + Kc*N*(dw) + 8GM` B；独立output可能保留layout，按真实stride寻址，不把payload字节当GMspan。statsallocation8GM B，outNone另由empty_like分配，预分配则本调用不新建；无scratch/workspace。输入/输出/统计异步存活归框架。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 精确边界 |
|---|---|
| 划分 | group列区间[gH,(g+1)H)、48行块轮转唯一，逻辑输出不交叠 |
| x/Y别名 | 本冻结域输出不alias输入，不改变x/参数 |
| padding | load未other，mean无colmasksum：BLOCK_N>H时零padding需具体primitive合同，不能假定 |
| gate | FP32SiLU乘x后求统计 |
| 精度 | x/W/bias/Z显式FP32，1/sqrt；outdtype转换，statsFP32，无量化 |
| 行尾 | rows<Mmaskload/store/stats；cols<Hmask，BLOCK_M48arange扩展准入另核对 |
| 同步 | SSA依赖/循环交compiler，无显式barrier/atomic，跨流消费归框架 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| heuristics/weight | [Device前段](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L14-L53) |
| load/gate/stats | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L55-L84) |
| affine/postgate/output | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L86-L102) |


### Route R-003：bias=false gate=post

#### 适用条件

##### 选择证据

冻结IS_RMS_NORM=false、outNone或独立预分配无输入别名；HAS_BIAS=false，HAS_Ztrue/NORM_BEFORE_GATEtrue，heuristics只依据B/Z指针是否None。

#### Device 数据流

##### 函数级调用链

`layer_norm_fwd→helper→_layer_norm_fwd_1pass_kernel_npu→loadFP32→mean/centeredvariance→affine→SiLUgate→stats/outputstore`。无其它自有Kernel/Cube节点。

##### 源码等价伪码

group g、program p轮转rowstart=p48+j*48Kc。load W[gH+cols]一次；每tile rows48、colsBLOCK_N按全M/Hmask读xFP32及zFP32；u=x；mean=sum(u)/H，xbar=where(cols<H,u-mean,0)，var=sum(xbar²)/H并存mean[gM+rows]；rstd=1/sqrt(var+eps)存统计；a=(u-mean)*rstd*W再乘z*sigmoid(z)；按真实Ystride与row/colmask写出。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| x/u/xbar/y | 各48×BLOCK_N FP32逻辑张量，单张量192*BLOCK_N B，不等实际物理峰值 |
| z | 48×BLOCK_N FP32逻辑，GM读MN*dz B |
| W/bias | BLOCK_N逻辑lane，合法H；W总Kc*N*dw B，bias0 |
| mean/rstd | 各48FP32；两GM数组各4GM B |
| out | 新建或独立提供MN*dy逻辑payload |
| UB/workspace | 无显式分配/请求，compilerphysicalallocation外部 |

##### 分层内存布局

`GMstridedx/z→FP32tile[48,BLOCK_N]→mean/centeredvar→rowrstd→affine/gate→GMout；stats以group-major另写GM`。x/zload均未指定other；LNmean先sum全BLOCK_N，若maskedlane无确定0会污染mean。

##### 字节账与复用顺序

合法H≤F、G=N/H、rowstorage不交叠域，逻辑流量 `MN*(dx+dy+dz) + Kc*N*(dw) + 8GM` B；独立output可能保留layout，按真实stride寻址，不把payload字节当GMspan。statsallocation8GM B，outNone另由empty_like分配，预分配则本调用不新建；无scratch/workspace。输入/输出/统计异步存活归框架。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 精确边界 |
|---|---|
| 划分 | group列区间[gH,(g+1)H)、48行块轮转唯一，逻辑输出不交叠 |
| x/Y别名 | 本冻结域输出不alias输入，不改变x/参数 |
| padding | load未other，mean无colmasksum：BLOCK_N>H时零padding需具体primitive合同，不能假定 |
| gate | FP32normaffine后乘SiLU，不改变前序统计 |
| 精度 | x/W/bias/Z显式FP32，1/sqrt；outdtype转换，statsFP32，无量化 |
| 行尾 | rows<Mmaskload/store/stats；cols<Hmask，BLOCK_M48arange扩展准入另核对 |
| 同步 | SSA依赖/循环交compiler，无显式barrier/atomic，跨流消费归框架 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| heuristics/weight | [Device前段](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L14-L53) |
| load/gate/stats | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L55-L84) |
| affine/postgate/output | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L86-L102) |


### Route R-004：bias=true gate=none

#### 适用条件

##### 选择证据

冻结IS_RMS_NORM=false、outNone或独立预分配无输入别名；HAS_BIAS=true，HAS_Zfalse，两种NORM_BEFORE_GATE均无有效分支，heuristics只依据B/Z指针是否None。

#### Device 数据流

##### 函数级调用链

`layer_norm_fwd→helper→_layer_norm_fwd_1pass_kernel_npu→loadFP32→mean/centeredvariance→affine→stats/outputstore`。无其它自有Kernel/Cube节点。

##### 源码等价伪码

group g、program p轮转rowstart=p48+j*48Kc。load W[gH+cols]及bias一次；每tile rows48、colsBLOCK_N按全M/Hmask读xFP32；u=x；mean=sum(u)/H，xbar=where(cols<H,u-mean,0)，var=sum(xbar²)/H并存mean[gM+rows]；rstd=1/sqrt(var+eps)存统计；a=(u-mean)*rstd*W+bias；按真实Ystride与row/colmask写出。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| x/u/xbar/y | 各48×BLOCK_N FP32逻辑张量，单张量192*BLOCK_N B，不等实际物理峰值 |
| z | 不读取 |
| W/bias | BLOCK_N逻辑lane，合法H；W总Kc*N*dw B，biasKc*N*db B |
| mean/rstd | 各48FP32；两GM数组各4GM B |
| out | 新建或独立提供MN*dy逻辑payload |
| UB/workspace | 无显式分配/请求，compilerphysicalallocation外部 |

##### 分层内存布局

`GMstridedx→FP32tile[48,BLOCK_N]→mean/centeredvar→rowrstd→affine→GMout；stats以group-major另写GM`。x/zload均未指定other；LNmean先sum全BLOCK_N，若maskedlane无确定0会污染mean。

##### 字节账与复用顺序

合法H≤F、G=N/H、rowstorage不交叠域，逻辑流量 `MN*(dx+dy) + Kc*N*(dw+db) + 8GM` B；独立output可能保留layout，按真实stride寻址，不把payload字节当GMspan。statsallocation8GM B，outNone另由empty_like分配，预分配则本调用不新建；无scratch/workspace。输入/输出/统计异步存活归框架。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 精确边界 |
|---|---|
| 划分 | group列区间[gH,(g+1)H)、48行块轮转唯一，逻辑输出不交叠 |
| x/Y别名 | 本冻结域输出不alias输入，不改变x/参数 |
| padding | load未other，mean无colmasksum：BLOCK_N>H时零padding需具体primitive合同，不能假定 |
| gate | 无zload/SiLU；norm_before_gate不影响算式 |
| 精度 | x/W/bias/Z显式FP32，1/sqrt；outdtype转换，statsFP32，无量化 |
| 行尾 | rows<Mmaskload/store/stats；cols<Hmask，BLOCK_M48arange扩展准入另核对 |
| 同步 | SSA依赖/循环交compiler，无显式barrier/atomic，跨流消费归框架 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| heuristics/weight | [Device前段](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L14-L53) |
| load/gate/stats | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L55-L84) |
| affine/postgate/output | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L86-L102) |


### Route R-005：bias=true gate=pre

#### 适用条件

##### 选择证据

冻结IS_RMS_NORM=false、outNone或独立预分配无输入别名；HAS_BIAS=true，HAS_Ztrue/NORM_BEFORE_GATEfalse，heuristics只依据B/Z指针是否None。

#### Device 数据流

##### 函数级调用链

`layer_norm_fwd→helper→_layer_norm_fwd_1pass_kernel_npu→loadFP32→x*SiLU(z)→mean/centeredvariance→affine→stats/outputstore`。无其它自有Kernel/Cube节点。

##### 源码等价伪码

group g、program p轮转rowstart=p48+j*48Kc。load W[gH+cols]及bias一次；每tile rows48、colsBLOCK_N按全M/Hmask读xFP32及zFP32；u=x*(z*sigmoid(z))；mean=sum(u)/H，xbar=where(cols<H,u-mean,0)，var=sum(xbar²)/H并存mean[gM+rows]；rstd=1/sqrt(var+eps)存统计；a=(u-mean)*rstd*W+bias；按真实Ystride与row/colmask写出。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| x/u/xbar/y | 各48×BLOCK_N FP32逻辑张量，单张量192*BLOCK_N B，不等实际物理峰值 |
| z | 48×BLOCK_N FP32逻辑，GM读MN*dz B |
| W/bias | BLOCK_N逻辑lane，合法H；W总Kc*N*dw B，biasKc*N*db B |
| mean/rstd | 各48FP32；两GM数组各4GM B |
| out | 新建或独立提供MN*dy逻辑payload |
| UB/workspace | 无显式分配/请求，compilerphysicalallocation外部 |

##### 分层内存布局

`GMstridedx/z→FP32tile[48,BLOCK_N]→mean/centeredvar→rowrstd→affine→GMout；stats以group-major另写GM`。x/zload均未指定other；LNmean先sum全BLOCK_N，若maskedlane无确定0会污染mean。

##### 字节账与复用顺序

合法H≤F、G=N/H、rowstorage不交叠域，逻辑流量 `MN*(dx+dy+dz) + Kc*N*(dw+db) + 8GM` B；独立output可能保留layout，按真实stride寻址，不把payload字节当GMspan。statsallocation8GM B，outNone另由empty_like分配，预分配则本调用不新建；无scratch/workspace。输入/输出/统计异步存活归框架。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 精确边界 |
|---|---|
| 划分 | group列区间[gH,(g+1)H)、48行块轮转唯一，逻辑输出不交叠 |
| x/Y别名 | 本冻结域输出不alias输入，不改变x/参数 |
| padding | load未other，mean无colmasksum：BLOCK_N>H时零padding需具体primitive合同，不能假定 |
| gate | FP32SiLU乘x后求统计 |
| 精度 | x/W/bias/Z显式FP32，1/sqrt；outdtype转换，statsFP32，无量化 |
| 行尾 | rows<Mmaskload/store/stats；cols<Hmask，BLOCK_M48arange扩展准入另核对 |
| 同步 | SSA依赖/循环交compiler，无显式barrier/atomic，跨流消费归框架 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| heuristics/weight | [Device前段](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L14-L53) |
| load/gate/stats | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L55-L84) |
| affine/postgate/output | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L86-L102) |


### Route R-006：bias=true gate=post

#### 适用条件

##### 选择证据

冻结IS_RMS_NORM=false、outNone或独立预分配无输入别名；HAS_BIAS=true，HAS_Ztrue/NORM_BEFORE_GATEtrue，heuristics只依据B/Z指针是否None。

#### Device 数据流

##### 函数级调用链

`layer_norm_fwd→helper→_layer_norm_fwd_1pass_kernel_npu→loadFP32→mean/centeredvariance→affine→SiLUgate→stats/outputstore`。无其它自有Kernel/Cube节点。

##### 源码等价伪码

group g、program p轮转rowstart=p48+j*48Kc。load W[gH+cols]及bias一次；每tile rows48、colsBLOCK_N按全M/Hmask读xFP32及zFP32；u=x；mean=sum(u)/H，xbar=where(cols<H,u-mean,0)，var=sum(xbar²)/H并存mean[gM+rows]；rstd=1/sqrt(var+eps)存统计；a=(u-mean)*rstd*W+bias再乘z*sigmoid(z)；按真实Ystride与row/colmask写出。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| x/u/xbar/y | 各48×BLOCK_N FP32逻辑张量，单张量192*BLOCK_N B，不等实际物理峰值 |
| z | 48×BLOCK_N FP32逻辑，GM读MN*dz B |
| W/bias | BLOCK_N逻辑lane，合法H；W总Kc*N*dw B，biasKc*N*db B |
| mean/rstd | 各48FP32；两GM数组各4GM B |
| out | 新建或独立提供MN*dy逻辑payload |
| UB/workspace | 无显式分配/请求，compilerphysicalallocation外部 |

##### 分层内存布局

`GMstridedx/z→FP32tile[48,BLOCK_N]→mean/centeredvar→rowrstd→affine/gate→GMout；stats以group-major另写GM`。x/zload均未指定other；LNmean先sum全BLOCK_N，若maskedlane无确定0会污染mean。

##### 字节账与复用顺序

合法H≤F、G=N/H、rowstorage不交叠域，逻辑流量 `MN*(dx+dy+dz) + Kc*N*(dw+db) + 8GM` B；独立output可能保留layout，按真实stride寻址，不把payload字节当GMspan。statsallocation8GM B，outNone另由empty_like分配，预分配则本调用不新建；无scratch/workspace。输入/输出/统计异步存活归框架。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 精确边界 |
|---|---|
| 划分 | group列区间[gH,(g+1)H)、48行块轮转唯一，逻辑输出不交叠 |
| x/Y别名 | 本冻结域输出不alias输入，不改变x/参数 |
| padding | load未other，mean无colmasksum：BLOCK_N>H时零padding需具体primitive合同，不能假定 |
| gate | FP32normaffine后乘SiLU，不改变前序统计 |
| 精度 | x/W/bias/Z显式FP32，1/sqrt；outdtype转换，statsFP32，无量化 |
| 行尾 | rows<Mmaskload/store/stats；cols<Hmask，BLOCK_M48arange扩展准入另核对 |
| 同步 | SSA依赖/循环交compiler，无显式barrier/atomic，跨流消费归框架 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| heuristics/weight | [Device前段](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L14-L53) |
| load/gate/stats | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L55-L84) |
| affine/postgate/output | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L86-L102) |

## 算子特定优化

### Trick T-001：groupmajor统计与循环外affine预读

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L38-L53)：

```python
    # Map the program id to the row of X and Y it should compute.
    pid_m = tl.program_id(0)
    group = tl.program_id(1)
    if not IS_RMS_NORM:
        Mean += group * M
    Rstd += group * M
    W += group * N
    if HAS_BIAS:
        B += group * N

    # Load weight once (broadcasted over rows)
    cols = tl.arange(0, BLOCK_N)
    col_mask = cols < N
    w = tl.load(W + cols, mask=col_mask).to(tl.float32)
    if HAS_BIAS:
        b = tl.load(B + cols, mask=col_mask).to(tl.float32)
```

#### 机制与设计原因

group*M定位stats，group*H定位W/B；每program预读H向量并复用多个48行块，逻辑W读取Kc*N*dw。statslayout是[G,M]展平，不是输入行优先。

#### 迁移边界

DeviceN=组宽H，HostN=总宽；组整除/末维连续及实际行stride分别需要满足。读取参数不能与原地覆写发生跨任务依赖。

#### 错误做法

stats按mG+g消费、把W预读次数写成MN，或把DeviceN当总宽导致错group。

### Trick T-002：直接中心化方差而非E[x²]-E[x]²

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py#L73-L84)：

```python
        # Compute statistics per row
        if not IS_RMS_NORM:
            mean = tl.sum(x, axis=1) / N  # [BLOCK_M]
            xbar = tl.where(col_mask[None, :], x - mean[:, None], 0.0)
            var = tl.sum(xbar * xbar, axis=1) / N
            tl.store(Mean + rows, mean, mask=row_mask)
        else:
            xbar = tl.where(col_mask[None, :], x, 0.0)
            var = tl.sum(xbar * xbar, axis=1) / N

        rstd = 1.0 / tl.sqrt(var + eps)  # [BLOCK_M]
        tl.store(Rstd + rows, rstd, mask=row_mask)
```

#### 机制与设计原因

方差使用(x-mean)²的均值，减少差值型方差的消减误差来源；但mean本身对padding没有显式补0保证，不能因此宣称所有H数值可靠。没有精度/性能实测。

#### 迁移边界

真实H作分母、epsilon合法、FP32中间可定义；BLOCK_M48与maskedload的具体工具链合同、physical资源需匹配。

#### 错误做法

只修方差padding便宣称meanpadding也修好；混入out=x原地语义。

## 模板与实现对比

本卡冻结LN及独立output，另外三域各自独立卡。gate前/后数学分别展开，activation不参与分发。元信息合法不等于Direct实际验证；所有staticpadding/宽度/alias前提精确保留。

## 平台差异

本卡A2/A3归属arch22；公开arch22/35均支持，README/architectures映射A2/A3、950，无hardwarebranch。CANN9.1.0 CI为配置非本次运行/A2实测；arange48、maskedload与physicalallocation须匹配工具链，draft不表示明确不支持平台。

## 限制与失败边界

Direct缺publicguard，H>F截断、LNpaddingmean、BLOCK_M48准入需核对；assert可关闭。独立out不应alias任何输入。finite输入仍可能FP32溢出，无编译、上游运行、测试/校验、真机或物理资源/性能证据，draft保留条件。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/layer_norm_fwd.md) | `layer_norm_fwd` | 分组LN/RMS/门控/统计/平台 |
| [Direct/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/layer_norm_fwd.py) | `layer_norm_fwd/_layer_norm_fwd_1pass_kernel_npu` | 162行；冻结RMS=false/inplace=false |
| [publicguard/适配](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/layer_norm_fwd.py) | `layer_norm_fwd/_triton_impl` | Direct不调用公共shape/stride/widthcheck |
| [设备helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | current_device、无参cache、两核数assert |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [norm包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/__init__.py) | `module init` | 无附加启动节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacy公开API与教学LayerNormExample已全文读；API链接复用，教学反向/锁不属于此入口，不拿其实现补当前forward。只新建本LN/independent独立两平台卡，source同repo一primary、无verified。
