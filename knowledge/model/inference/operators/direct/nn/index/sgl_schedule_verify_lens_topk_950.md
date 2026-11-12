---
type: Operator
title: "ScheduleVerifyLensTopk 950 Direct Invoke 算子知识"
description: "闭合验证长度调度的prep、条件排名、finalize多Kernel图与GM统计交接，记录稳定键、二次比较、int32原子及runtime预算缓存。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/schedule_verify_lens_topk_triton.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/schedule_verify_lens_topk.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py
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
created_at: "2026-11-09T09:34:10Z"
updated_at: "2026-11-10T07:06:47Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# ScheduleVerifyLensTopk 950 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.sample.schedule_verify_lens_topk.schedule_verify_lens_topk_triton(*,confidence,budget,cfg)`，FP32生存概率累乘→全局候选稳定排名/预算分配→每请求验证长度限幅。非空调用必有prep/finalize，budget>0且n>0才有rank；这是多Kernel唯一逻辑算子，排名实际两两比较、O(n²)，名字TopK不表示次线性算法。

完整自有Host、三Kernel、内部GM scratch与cache图闭合；draft明确合法cfg/输入未guard、int32排名范围、框架流/分配边界及无本次运行证据。全文读过的[API合同](../../../../apis/sgl_kernel_npu/sgl_schedule_verify_lens_topk.md)复用。

## 接口与语义

### 计算语义

B请求、G=gamma、M=cfg.resolved_max_verify_len()、C=min(M,G)、n=BC。`S[r,p]=prod_{j≤p} float32(confidence[r,j])`；候选p<C且S≥eps_s。排序键S降序、p升序、r升序，选择前min(budget,n)个合法候选，budget≤0不选。每请求count→`min(max(min_verify_len+count,max(min_verify_len,1)),M)`转int32。合法M=min_verify_len=0时尽管中间lower1，最后min使输出0。真实max/min顺序不能被反向上下界的泛化clamp语义替代。

### 输入、输出与属性

| 项 | 合同/真实处理 |
|---|---|
| confidence | NPU[B,G] FP16/BF16/FP32、值[0,1]；非连续先.contiguous() |
| budget | Python int，≤0跳rank，正值转int并min(n)传runtime |
| cfg | 提供resolved_max_verify_len()、min_verify_len、survival_eps；调用方保证0≤min≤M≤G+1、eps_s≥0 |
| output | 新int32[B]同device；输入不写 |
| 校验 | launcher直接解包shape/读cfg，没有完整dtype/device/cfg/valueguard |

### 入口与版本

冻结短路径加包名前缀即精确Direct。auto/triton门面转发；torch_native累乘/稳定排序/scatter-add是独立外部reference，不并入此图。固定SGL commit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI固定配置，非本次环境；完整Triton二进制未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

解包B/G、调用cfg方法求M、计算C/n；B0直接返回emptyint32[0]，不读cfg其它属性/不编译。非空分配selected_extra[B]int32、survival[B,C]FP32、verify_lens[B]int32，再confidence.contiguous()。不读取置信度值到Host。cfg方法是调用方对象行为，不是自有Device实现；输入连续化由外部Torch完成，可能额外一次copy。

### 参数、Workspace 与生命周期

内部GMscratch=4B+4n B，返回GM输出4B B，合计4n+8B B；非连续输入额外临时B*G*d B（已有contiguous输入不要求复制）。没有调用方workspace或POD/ACLNN，GM临时不能因此写成“零scratch”。Python引用存活贯穿三launch，函数返回时局部引用释放时点与异步回收安全归Torch allocator/stream合同；代码无手动free/wait。

### 启动图与失败传播

B0纯Host；非空`contiguous→prep→[budget>0&&n>0时rank]→finalize→返回`。同次顺序依赖框架当前流排队，源码未提供event或host同步；跨线程/跨流规则归调用环境。cache只保存compiledlaunchers：
key=(device,dtype,B,G,M,int(min),confidence.data_ptr()%16)，预算/threshold/pointers/currentstream为runtime。miss编译prep/finalize，rank按需首次编译；rankwarmup使用2/0.5代表值保持runtime ABI，实际调用传min(int(budget),n)/float(eps_s)。不得把2/0.5当真实调度参数。异常直接传播，无fallback或回滚。

## Route 与参数设计

### 分核与资源计算

prep gridB，一program一请求，G_P2=next_power_of_2(max(G,1))。rank U=ceil(n/16)program，每program16目标、对所有n候选按128循环；pair逻辑tile16×128=2048。final gridceil(B/256)，每program256请求。全部无Cube/tl.dot/AIC/MIX自有节点，外部contiguouscopy不是隐藏Cube实现。

### Route 选择

| Host路线 | 条件 | 可达节点 |
|---|---|---|
| H-000 | B0 | 无Device/GM中间 |
| H-001 | B>0且budget≤0或n0 | R-001→R-003 |
| H-002 | B>0且budget>0且n>0 | R-001→R-002→R-003 |
| cache冷/热 | 任意非空图 | 可选编译，相同数学节点；rank可迟编译 |

### 模板/实现执行矩阵

| Route/节点 | 输入 | 输出 | specialization |
|---|---|---|---|
| R-001 prep | FP16/BF16/FP32 confidence | FP32survival/int32zero | G/C/G_P2 |
| R-002 rank | FP32survival、runtimebudget/eps | int32selected_extra原子累加 | C/n/BLOCK_C16/BLOCK_CP128 |
| R-003 finalize | int32counts | int32verify_lens | min/lower/M/B/BLOCK256 |

两类完整Host图的节点与资源均闭合，不把每Kernel另立逻辑算子。数据dtype实例仅prep读入转换有差异。

### 隐藏性能 Guard

rank O(n²)比较、U次完整survival扫描，n小/大成本不可按TopK库推断。rank累加与selected_extra为int32，须保证计数和sum可表示；Host没有n/int32 guard。prep即使C<G也读全部G并累乘，C0/G0仍执行prep以清零selected_extra；不能把其读流量简单写4n。无物理UB容量guard，逻辑pairtile不能代替实际资源。

### POD/ABI

| 节点 | 字段逐项/消费 |
|---|---|
| prep runtime | confidence_ptr输入；survival_ptr/selected_extra_ptr写 |
| prep constexpr | gamma=G行步长/读mask；cols=C输出步长/写mask；G_P2=arange/cumprod长度 |
| rank runtime | survival_ptr读、selected_extra_ptr原子RMW、budget=intbudget截n、survival_eps=float阈值 |
| rank constexpr | cols=C商余；n=BC边界；BLOCK_C16目标；BLOCK_CP128比较候选 |
| finalize runtime | selected_extra_ptr读、out_ptr写 |
| finalize constexpr | min_verify_len=int(min)；lower_bound=max原cfgmin,1；max_len=int(M)；bs=B；BLOCK256 |
| grids | B / ceil(n/16) / ceil(B/256) |

没有自定义POD/序列化偏移；JIT ABI/标量位宽外部，源码明确rank/count中间int32与row.to(int64)指针项。超大尺寸其它算术仍需可表示域。

### Route 源码闭包

166行含全部launcher/cache/三个Kernel，public转发已读；cfg外部方法/contiguous/Tritonprimitive边界明确。根setup→stage_runtime完整Python包→build_wheel/setup_refactor，sample/backend初始化无Device。不把外部reference补成自有图，不遗漏rank跳过分支。

## Kernel 实现

### 公共执行流程

prep完整定义survival与selected_extra初值；rank只读survival并原子累加计数；final只读计数并写验证长度。GM交接按同次框架流顺序，三Kernel无并行图/跨核自旋等待。

### Route R-001：生存概率与计数初始化

#### 适用条件

##### 选择证据

所有B>0Host图均运行，即使budget≤0、C0或G0。gridB、G_P2至少1。

#### Device 数据流

##### 函数级调用链

`launcher→_schedule_topk_prep_kernel→load.to(FP32)/cumprod/store`，无其它自有helper。

##### 源码等价伪码

r=programid；g=arange(G_P2)；conf=load(conf+rG+g,g<G,other1).FP32；surv=cumprod(conf)；g<C写survival[rC+g]；selected_extra[r]=0。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| conf/surv | G_P2 FP32，各逻辑4G_P2 B，非实际并存buffer证明 |
| GMconfidence | 每行G*d读，完整BGd B |
| GMsurvival | 完整4BC=4n B写 |
| selected_extra | 4B B清零 |
| 物理UB/workspace | 无显式分配/请求，compiler外部 |

##### 分层内存布局

`GMconfidence[B,G]→FP32SSA[G_P2]→inclusivecumprod→GMsurvival[B,C]`并清零GMcount[B]。padding1不改变合法前缀乘积；没有对padding统计GM写入。

##### 字节账与复用顺序

本节点读BGd、写4n+4B B。survival/count均由Host分配；prep写完经框架流顺序交给rank或final；count即使无候选也必有定义值。无额外静态workspace。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| cumprod | FP32 inclusive，具体扫描树/舍入由Triton；近阈值/近概率排序可能变化 |
| 尾列 | g<G load其他1，g<C store；C≤G合法配置下无需超输入 |
| 请求间 | 每program独占survival行/count槽，无原子 |
| G0/C0 | G_P2=1，G0无confidence读取，C0无survival写；count仍清零 |
| 交接 | prep→rank/final的框架流顺序，未显式event/hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| prep | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py#L10-L26) |
| 预分配 | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py#L94-L106) |

### Route R-002：全局稳定排名与原子计数

#### 适用条件

##### 选择证据

仅B>0、budget>0、n>0。C>0避免商余除0；runtimebudget被min到n。

#### Device 数据流

##### 函数级调用链

`launcher→_schedule_topk_selected_extra_kernel→load→pair compare/where→sumint32→atomic_add`；无外部topk调用或自有未知Kernel。

##### 源码等价伪码

每program目标c=pid16+[0,16)，拆r/p并loadsp，sp<eps替换-inf；rank初始化0。遍历cp0=0..n步128，load候选spp/无效0，同阈值替换-inf，按[概率降序,p升序,r升序]比较是否排目标之前，AND cp<n，再axis1sum累加rank。selected=(sp≥eps)&&(rank<budget)，mask c<n对selected_extra[r]原子加0/1。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模 |
|---|---|
| 目标sp/mp/rank/r/p | 各16lanes，rankint32 |
| 比较候选spp/mpp/rp/pp | 各128lanes |
| pairgt/eq/poslt/poseq/reqlt/before | 各16×128逻辑布尔；实际融合/存储未知 |
| survivalGM | 目标读4n B，加每program扫全n：4nU B |
| countGM | n次合法atomic_add(int32)，含selected0；逻辑RMW各4B读+4B写，不等于物理事务保证 |

##### 分层内存布局

`GMsurvival[n]→SSA targets16 + candidates128→pairmatrix16×128→rank16→GMcount[B]atomic`。无需n×n GM矩阵；O(n²)计算不意味着GM分配4n² B。

##### 字节账与复用顺序

逻辑load总4n(1+U) B，另n次int32原子RMW；count接prep初始0，final必须在所有rankKernel工作完成后按框架流消费。原子冲突只在同请求内，数值为整数可加；仍要求count≤int32上限，不证明超大n安全。无新GM分配或workspace。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| rank | 对每目标遍历全部候选；排位键包含p/r形成合法候选的唯一顺序 |
| 阈值 | sp≥eps；非法候选mp=-inf，合法概率≥0/eps≥0时不会排合法目标前；无候选时selectedfalse |
| 比较尾 | cp<n参与beforemask；c<n同时保护目标survival的tl.load与最终atomic，padding目标仍可参与中间逻辑但不作为有效目标读写 |
| 原子 | int32add允许多program同请求累加，无自有跨核barrier；Kernel结束→final需流顺序 |
| 整数 | rank/sum/countint32，溢出域未guard；预算/threshold runtime类型归JIT ABI |
| FP32 | 读prep舍入后的S，近概率可能改变排序，NaN/不在[0,1]不属合同 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| rankKernel | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py#L48-L85) |
| 按需编译/真实runtime值 | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py#L146-L164) |

### Route R-003：验证长度限幅

#### 适用条件

##### 选择证据

所有B>0图在prep和可选rank之后执行，gridceil(B/256)。

#### Device 数据流

##### 函数级调用链

`launcher→_schedule_topk_finalize_kernel→loadint32→maximum/minimum→store`，没有另一自有节点。

##### 源码等价伪码

i=pid256+arange256；i<B读count，extra转int32；lens=minVerify+extra；lens=max(lens,lower)；lens=min(lens,M)；i<B写verify_lens。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| extra/lens | 各256int32逻辑1024B，实际物理分配外部 |
| GMcount/output | 各4B B读/写 |
| workspace/UB | 无新增分配，N/A |

##### 分层内存布局

`GMcount[B]→maskedSSA[256]→加min/先max后min→GMout[B]`；无statistics回读Host。

##### 字节账与复用顺序

本节点读4B、写4B B；所读count已由prep及可选rank定义，全部3节点执行顺序形成完整lifetime。返回只暴露verify_lens，scratch局部引用后续回收归framework异步allocator规则。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 输入就绪 | 前序Kernel流顺序，源码无独立event |
| 尾块 | i<B load/store，无越界输出 |
| M0 | 合法min0时先max到1再min到0，最终0；不假装上下界有序 |
| int32 | min+extra仍需不溢出；Host未guard极大配置 |
| 写集合 | 独立256块，无atomic/跨核barrier |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| finalize | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py#L29-L45) |
| 最终launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py#L165-L166) |

## 算子特定优化

### Trick T-001：稳定排序转为两两计数，无n×n GM物化

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py#L76-L85)：

```python
        gt = mpp[None, :] > mp[:, None]
        eq = mpp[None, :] == mp[:, None]
        pos_lt = pp[None, :] < p[:, None]
        pos_eq = pp[None, :] == p[:, None]
        req_lt = rp[None, :] < r[:, None]
        before = gt | (eq & (pos_lt | (pos_eq & req_lt)))
        before = before & cpmask[None, :]
        rank += tl.sum(before.to(tl.int32), axis=1)
    selected = valid_c & (rank < budget)
    tl.atomic_add(selected_extra_ptr + r, selected.to(tl.int32), mask=cmask)
```

#### 机制与设计原因

为每候选统计全局“排在之前”数量，稳定键显式包含位置/请求；rank<budget即选择，用atomic_add汇总每请求。pairmatrix仅逻辑tile，GM只需n个survival和B个count；计算仍二次，不能宣称适合任意大候选集。

#### 迁移边界

合法概率/阈值、int32rank容量、顺序键及原子/后序流依赖；改变stabletie顺序会改变各请求预算。

#### 错误做法

以原始flatten索引升序替代p再r升序（row-major为r再p），或把TopK名字当库排序/次线性性能证据。

### Trick T-002：runtime预算与阈值的迟编译launcher

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py#L147-L159)：

```python
        if launchers[1] is None:
            # Representative non-special scalar values keep budget/epsilon in
            # the compiled ABI (even when a later call uses budget=1 or eps=0).
            rank = _schedule_topk_selected_extra_kernel.warmup(
                survival,
                selected_extra,
                2,
                cols,
                n,
                0.5,
                BLOCK_C=16,
                BLOCK_CP=128,
                grid=(triton.cdiv(n, 16),),
```

#### 机制与设计原因

rank仅在首次正预算/非零候选时编译，代表值2/.5避免把后续预算1/阈值0特殊常数固化；真实预算/阈值每次传入。缓存只保存编译对象，scratch/输出/当前stream不固化。

#### 迁移边界

实际JIT对scalar specialization的语义归Triton版本，源码选择代表值的意图可见；新增影响编译的属性需核对cachekey。

#### 错误做法

把代表值2/.5当数学固定参数，或缓存首轮Tensor/stream给后续调用。

## 模板与实现对比

唯一逻辑算子有2或3Kernel图；B0无Kernel。prep清零count对跳rank图至关重要，连续化是外部Torch节点而非隐藏自有实现。所有scratch/交接均显式记账，物理UB/register没有编译产物则不填造数。

## 平台差异

本卡950归属arch35；公开doc arch22/35支持，并报告Ascend910_9362/950上游验证；只作为上游报告，不是本次复测，也不等于所有A2/A3产品实测。README/architectures映射A2/A3、950；CANN9.1.0 CI配置与实际compiler版本/资源要区分。

## 限制与失败边界

调用方负责合法cfg/预算/概率范围/device，Host未强制；NaN或非法阈值/尺寸不在证明域。rank/原子count为int32、复杂度二次，资源/整数上限未guard。无构建、运行、测试/校验或物理分配/性能结论；draft不宣称完整部署安全，未擅自修源。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/schedule_verify_lens_topk_triton.md) | `schedule_verify_lens_topk_triton` | 稳定排序/cfg范围/上游产品验证报告 |
| [Direct及三Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py) | `schedule_verify_lens_topk_triton/_schedule_topk_*` | 完整166行/GM scratch/cachedlaunchers |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/schedule_verify_lens_topk.py) | `_triton_impl` | 关键字转发，无新增guard |
| [sample包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/__init__.py) | `module init` | 无附加Device |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117同主题API已完整阅读并链接，新增该唯一Direct两平台实现卡；不混入build_out_tokens/接受长度验证等其它数学语义。全部同repo固定source恰一primary、无verified。
