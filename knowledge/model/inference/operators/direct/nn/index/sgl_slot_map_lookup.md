---
type: Operator
title: SlotMap槽位查找 A3 Direct Invoke 算子知识
description: 说明slot_map_lookup的固定TopK2048、32字节行读取与UB Gather、两组流水缓冲、非法索引sentinel及命中标志值域。
tags:
- task.implementation
- task.lookup
- topic.data_movement
- topic.memory
- topic.programming_model
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sparsity_driven_kv_offload/ops.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sparsity_driven_kv_offload/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/slot_map_lookup/op_host/slot_map_lookup.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/slot_map_lookup/op_kernel/slot_map_lookup_kernel.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/defines.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_slot_map_lookup.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/scripts/prepare_kernel_tests.sh
  role: supporting
created_at: '2026-11-09T13:15:17Z'
updated_at: '2026-11-09T13:15:17Z'
platforms:
- a3
cann_versions:
- 9.1.0
---

# SlotMap槽位查找 A3 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `sparsity_driven_kv_offload.slot_map_lookup`→Torch op→手写Host→ACLRT；Direct Invoke，无ACLNN pair |
| 计算语义 | 对请求和逻辑token查slot；非法索引输出0/-1，合法索引保留slot并算`min(slot+1,1)` |
| 输入输出 | 连续int32 map[S,C]、req[B]、topk[B,2048]；新int32 hit/pos[B,2048] |
| 执行类型 | 单AIV_VECTOR，entry明确KERNEL_TYPE_AIV_ONLY；MTE2+UB Gather+MTE3，无Cube |
| Kernel 路线 | R-001，单body内含合法/非法req及合法/非法token子路径 |
| 核心资源 | 五TBuf各含两槽，合计6208B；无workspace |
| 来源闭包 | direct_implementation_closed：Python、schema、Host标量、entry/body、helper及构建闭合 |
| 验证状态 | draft；本次知识提取未执行编译、真机、数值或性能测试 |

## 接口与语义

### 计算语义

若req不在[0,S)或token不在[0,C)，position=-1、hit=0。合法索引读取`slot_map[req,token]`原int32，position不再按slot值裁剪，hit实际为`Mins(Adds(slot,1),1)`。当slot遵循-1表示miss、0..INT32_MAX-1表示有效槽时，hit才是0/1；slot=-2会得到-1，不能将本体改写成对任意负值都等价的`slot>=0`。INT32_MAX的加法边界未被Host拒绝，不声明其溢出规则。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| slot_map | [S,C]连续NPU | int32 | S/C正，C为8倍数；slot值协议caller负责 |
| req_indices | [B]连续同NPU | int32 | B正；非法设备值有miss分支 |
| topk_indices | [B,2048]连续同NPU | int32 | T固定2048，任意宽度不支持 |
| token_on_device/device_token_pos | Python按topk shape新分配 | int32 | Torch原始接口使用caller提供可变输出，原生返回空 |
| block_dim | 默认0 | int64→uint32 | 0取当前平台AIV核数，正值不得超过该核数 |

### 入口与版本

固定dda6，A3-only集合门控Host、Kernel及PrivateUse1注册，链接no_workspace_kernel。该宏默认用于arch22家族，本卡只冻结A3，不推出A2产品验收；950默认不编入。CANN9.1依据kernel CI实际容器与prepare脚本的legacy整体构建配置，不是本次编译事件，也不意味着专属slot测试进入了活动CI分组。框架初始化仍需加载原生sgl库。

## Host/Launcher 执行流程

### 参数校验与前处理

Python分配两个int32 empty_like输出。Host检查五Tensor同NPU、连续、rank分别2/1/2/2/2、dtype全int32；S/C/B/T落uint32、S*C与B*T不超过UINT32_MAX，block_dim非负且可表示。要求S/C/B正、T=2048、C%8=0、batch对应及输出shape相符。输出shape与topk batch的部分比较先窄化到uint32，不能把直接绕过Python分配的极端大shape视为另有完整范围证明。

Host查询PlatformAscendCManager的AIV核数A>0；G=block_dim>0?block_dim:A，要求G≤A。没有数据cast/contiguous复制、Host索引值读回或页表生成。非法输入抛错，无fallback。

### 参数、Workspace 与生命周期

五Tensor均record_stream到current NPU stream，EXEC_KERNEL_CMD转换为裸指针/标量tuple供OpCommand捕获，未捕获Tensor对象。无DeviceGuard，caller须使current设备与全部Tensor一致，并按Host排队与异步执行契约保活。输入map不能与并发更新或输出错误alias；Python输出独立分配不代表原生Torch接口会检测caller传入重叠区。workspace=0。

### 启动图与失败传播

```mermaid
flowchart LR
  H[分配输出与Host guard] --> L[OpCommand current stream]
  L --> K[slot_map_lookup AIV单Kernel]
  K --> O[hit与position GM]
```

entry五地址+四uint32标量，G作为launch参数；没有跨Kernel交接边。helper闭包固定返回0，没有检查ACLRT launch返回值；实际错误与完成时机仍由匹配Runtime/OpCommand处理。record_stream不是CPU完成同步，读取输出须遵循外部流契约。

## Route 与参数设计

### 分核与资源计算

T=2048，tile=64，故每请求恰32个完整task。总Q=32B，采用整除base=Q/G、extra=Q%G：核c的begin=c*base+min(c,extra)，长度base+[c<extra]。无task的核在缓冲取值和flag初始化前返回。B*T≤UINT32_MAX也约束32B，无任意T尾块路线。

每缓冲两槽：topkIdx/pos/token/offset各2*64*4=512B；slotLine为2*65*8*4=4160B。UB总6208B。Host只查询核数，不按UB容量另选tile，6208≤匹配平台实际可用UB是必要条件，不能把未查询的容量写成Host guard。

### Route 选择

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 双缓冲slot行读取 | KernelSlotMapLookup | 全部Host guard通过，A3，T2048 | 抛错，无替代body |

```text
Host guard → G=显式正数或平台核数 → launch单body
每task：req非法→直接填miss；req合法→读topk与slot行→Gather
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 | 无TilingKey，task内runtime索引分支 | S/C/B正、C%8=0、T2048、连续int32、A3 | 单AIV slot_map_lookup | KernelSlotMapLookup::Init/Process/SplitRange | 五双槽TBuf、显式MTE2/S/V/MTE3事件 | 无task早返；非法索引不是新Host Route |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| T固定 | T=2048 | 64tile、8元素Gather及整块DataCopy | R-001 | 抛错 | Host slot_map_lookup |
| map行对齐 | C%8=0 | 每token加载包含目标的完整8int32/32B行 | R-001 | 抛错 | Host/Process |
| 地址乘积 | S*C、B*T≤UINT32_MAX | uint32 row/output offset | R-001 | 抛错 | Host |
| 核数 | 0<G≤AIV可用数 | worker分配及launch | R-001 | 抛错 | Host |
| slot值协议 | Host无值域检查 | Adds+Mins不是任意整数布尔比较 | R-001 | 无fallback，caller保证 | Process |

### POD/ABI

无自定义POD；生成ACLRT stub的物理封送布局在外部，以下为entry参数顺序，不虚构结构offset。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| entry | slot_map | GM_ADDR | 参数0 | int32基址 | ConvertType(map) | slotMapGm | S*C |
| entry | req_indices | GM_ADDR | 参数1 | int32基址 | ConvertType(req) | GetValue(b) | B |
| entry | topk_indices | GM_ADDR | 参数2 | int32基址 | ConvertType(topk) | DataCopy | B*T |
| entry | token_on_device | GM_ADDR | 参数3 | int32基址 | caller/Python output | DataCopy出 | B*T |
| entry | device_token_pos | GM_ADDR | 参数4 | int32基址 | caller/Python output | DataCopy出 | B*T |
| entry | size | uint32/32 | 参数5 | 请求槽数 | map.size0窄化 | req范围 | 正 |
| entry | max_context_len | uint32/32 | 参数6 | 逻辑token数 | map.size1窄化 | row/index范围 | 8倍数 |
| entry | bs | uint32/32 | 参数7 | batch | req.size0窄化 | task总量 | 正 |
| entry | topk | uint32/32 | 参数8 | token数/行 | topk.size1窄化 | task与GM步长 | 固定2048 |
| launch | blockDim | uint32/32 | entry外参数 | 核 | effectiveBlockDim | GetBlockNum/Idx | ≤当前AIV核数 |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 | 唯一body | Python→Host slot_map_lookup | 上述entry/launch参数 | slot_map_lookup AIV_ONLY | KernelSlotMapLookup、AscendC primitives | legacy A3集合/no_workspace_kernel |

## Kernel 实现

### 公共执行流程

entry创建TPipe，Init将GM绑定并分配五TBuf；Process分配task区间，按iter%2复用slot。SDK搬运/Gather/Vector指令与自动同步、编译ABI是primitive/生成代码边界，算子自有分核/地址/helper都在固定源码内。无Cube、dot、反向或另一个算法fallback。

### Route R-001：双槽slot行读取

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Python | sparsity_driven_kv_offload/ops.py | slot_map_lookup | 输出empty_like int32 | Torch op |
| Host | slot_map_lookup/op_host/slot_map_lookup.cpp | slot_map_lookup | guard及G核数 | launch |
| entry | slot_map_lookup/op_kernel/slot_map_lookup_kernel.cpp | slot_map_lookup | KERNEL_TYPE_AIV_ONLY | Init/Process |

#### Device 数据流

##### 函数级调用链

```text
Python → Host slot_map_lookup → EXEC_KERNEL_CMD → ACLRT_LAUNCH_KERNEL
  → KernelSlotMapLookup::Init → Process → SplitRange
  → current MTE2 → previous Gather/Vector → MTE3 → drain
```

##### 源码等价伪码

```text
split Q=32B tasks across G; if no tasks return
for slot in 0,1: sentinelLine[slot,64,0:8]=-1
seed MTE3_MTE2 flags0,1
for iter=0..localTasks inclusive:
  cur=iter%2; prev=(iter+1)%2
  if iter>0:
    if !skip[prev]:
      wait MTE2_V(prev)
      for g=0,8,..56: pos[g:g+8]=Gather(slotLines,byteOffsets[g:g+8])
      hit[0:64]=min(pos[0:64]+1,1)
    set/wait V_MTE3(prev); copy hit/pos64items to GM
    set MTE3_MTE2(prev)
  if iter==localTasks: break
  wait MTE3_MTE2(cur)
  task=begin+iter; b=task/32; gm=b*T+(task%32)*64
  save gm/len64; req=reqIndices[b]
  if req<0 or req>=S:
    set/wait MTE2_V(cur); hit=0; pos=-1; skip[cur]=true; continue
  skip[cur]=false
  DataCopy topk64; set/wait MTE2_S(cur)
  for i=0..63:
    x=topk[i]
    if x<0 or x>=C: byteOffset[i]=64*8*4
    else:
      byteOffset[i]=(i*8+(x&7))*4
      DataCopy8 int32 slotLines[i*8] <- map[req*C+(x&~7)]
  set MTE2_V(cur)
wait MTE3_MTE2(0), MTE3_MTE2(1)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM map | req*C+(x&~7) | S*C int32；单次8元素 | row-major | caller | MTE2 | caller | C8对齐避免整行读取越row尾 |
| GM topk | b*T+tile*64 | 64int32/有效task | contiguous | caller | MTE2→scalar | caller | T2048故无不足64尾 |
| GM hit/pos | 同topk地址 | 各B*T int32 | contiguous | MTE3 | caller | Python新Tensor或原生caller | 不检测错误alias |
| UB topkIdxBuf | slot*64 | 2*64*4=512B | int32 | MTE2 | scalar GetValue | pipe | depth2子区 |
| UB posResultBuf | slot*64 | 512B | int32 | Gather/Duplicate | MTE3 | pipe | 两槽 |
| UB tokenResultBuf | slot*64 | 512B | int32 | Adds/Mins或Duplicate | MTE3 | pipe | 两槽 |
| UB slotLineBuf | slot*65*8 | 4160B | int32、每token8元素 | MTE2/初始sentinel | Gather | pipe | 每槽末32B全-1 |
| UB mteOffsetBuf | slot*64 | 512B | uint32 byte offsets | scalar SetValue | Gather | pipe | 非元素offset |

正常task读取topk256B，最多64条slot行各32B，不去重相同token/同一cache line；输出两路各256B。Gather每8项一组，baseOffset=0、count=8，offset已乘4。非法token只指向UB sentinel，不发该token的GM slot读取；非法req不读该task topk/slot，直接生成整tile miss。

##### 分层内存布局

```mermaid
block-beta
  columns 5
  idx["topkIdx · 2×64×4=512B"]
  pos["pos · 2×64×4=512B"]
  tok["hit · 2×64×4=512B"]
  lines["slotLines含sentinel · 2×65×8×4=4160B"]
  off["offsets · 2×64×4=512B"]
```

##### 字节账与复用顺序

```text
UB_total = 4*512+4160 = 6208 bytes
workspace_total=0；dynamic_ub=N/A
必要条件6208<=实际可用UB；Host无UB自适应selector
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| 槽0/1载荷/结果 | 当前MTE2/scalar/V | 下一轮prev Gather/MTE3 | 两轮后current | MTE3_MTE2→MTE2_V及V_MTE3 | 不能删非法req专门bridge |
| sentinel32B | 开始Duplicate -1 | 非法token Gather | 本调用不覆盖 | 同V执行顺序及SDK自动同步边界 | 不当真实第65token输出 |
| gmOffset/len/skip数组 | 当前task | 下一轮prev | 同槽下一task | 同Process标量迭代 | 无task核提前返回 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| topk到scalar | MTE2_S set/wait | topk DataCopy | GetValue | index UB | int32原值 |
| slot行到Gather | MTE2_V set/wait | slot DataCopy | Gather | slotLines | invalid用-1sentinel |
| Vector到输出 | V_MTE3 set/wait | Gather/算术/填充 | DataCopy出 | pos/hit | 无浮点舍入 |
| 输出到同槽复用 | MTE3_MTE2 set/wait | 旧输出MTE3 | 新输入MTE2 | 两槽 | 结尾等待0/1 drain |
| 非法req写V | MTE3_MTE2后MTE2_V bridge | 旧MTE3 | Duplicate | pos/hit | 0/-1，不执行Gather |

显式事件号使用槽0/1，每迭代先提交prev结果再处理current，末次只drain。源码注释表达pipeline重叠意图，不是本次观测的重叠率或吞吐。T2048将所有task固定64，不能由Device参数保留topk推导Host支持任意尾tile。

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | slot_map_lookup/op_host/slot_map_lookup.cpp | slot_map_lookup | 固定T与C8/核数/uint32 guard |
| Kernel entry/router | slot_map_lookup/op_kernel/slot_map_lookup_kernel.cpp | slot_map_lookup | AIV_ONLY单entry |
| Device body/helper | 同上 | Init/Process/SplitRange | 双槽、整行point lookup及Gather |

## 算子特定优化

### Trick T-001：整32B行读取与UB sentinel Gather

#### 触发与源码依据

- 适用R-001，合法req，token逐项决定真实行或sentinel。
- Golden来源：[byte offset与8元素行读取](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/slot_map_lookup/op_kernel/slot_map_lookup_kernel.cpp#L165-L173)。

**官方源码（固定Commit连续逐字摘录）**：

```cpp
                if (topkIdx < 0 || static_cast<uint32_t>(topkIdx) >= max_context_len) {
                    mteOffsetLocal.SetValue(i, SENTINEL_LINE_OFFSET_BYTES);
                } else {
                    const uint32_t topkIdxU = static_cast<uint32_t>(topkIdx);
                    const uint32_t lineBase = topkIdxU & ~SLOT_LINE_MASK;
                    const uint32_t lineOffset = topkIdxU & SLOT_LINE_MASK;
                    mteOffsetLocal.SetValue(i, (slotLineBase + lineOffset) * sizeof(int32_t));
                    AscendC::DataCopy(slotLineLocal[slotLineBase], slotMapGm[slotRowOffset + lineBase],
                                      SLOT_LINE_ELEMS);
```

#### 机制与设计原因

GM每点扩为32B行，UB再按byte offset Gather目标slot，非法位置共用已填-1行；将数据搬运与命中标志运算分离。C%8=0令合法末token所在完整行仍在map行内。不同token仍可能重复加载相同行，不宣称已去重、减少总GM字节或一定快于标量读取。

#### 迁移边界

- 适用：连续int32行、C8对齐、固定64项tile。
- 前提：每槽65条UB行、byte offset单位及Gather契约。
- 失效：C不对齐或任意TopK须重做guard与tail，当前Host拒绝。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；不能将byte offset直接当int32元素offset，亦不能把sentinel占用漏出UB账。

### Trick T-002：非法请求分支补齐MTE2到V的复用依赖

#### 触发与源码依据

- 适用R-001，req_id<0或req_id≥S，同槽可能刚被旧MTE3读取。
- Golden来源：[非法req的Vector桥接](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/slot_map_lookup/op_kernel/slot_map_lookup_kernel.cpp#L146-L151)。

**官方源码（固定Commit连续逐字摘录）**：

```cpp
                AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(curBuf);
                AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(curBuf);
                AscendC::Duplicate(tokenLocal, static_cast<int32_t>(0), TOPK_TILE_LEN);
                AscendC::Duplicate(posLocal, static_cast<int32_t>(-1), TOPK_TILE_LEN);
                slotSkipV[curBuf] = true;
                continue;
```

#### 机制与设计原因

MTE3_MTE2只阻挡新MTE2，非法req不发正常MTE2工作却直接由V写结果；bridge把旧输出完成依赖传到V，之后skip标志避免下一轮Gather覆盖miss。它是算法真实分支的同步，不能因没有slot加载就删掉。

#### 迁移边界

- 适用：双槽V直接填充与DMA复用场景。
- 前提：保留事件槽号、旧MTE3完成链及下一轮skip。
- 失效：改流水深度/事件协议须重新证明，源码无替代实现。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供实际运行反例；源码注释解释删除bridge的依赖缺口，不将其写成已复现故障。

## 模板与实现对比

| 对比维度 | R-001合法req | R-001非法req子路径 | 设计选择依据 |
|---|---|---|---|
| 命中条件/优先级 | 0≤req<S | 其他req | task内判断 |
| 模板与 dtype | Gather+Adds+Mins int32 | Duplicate0/-1 int32 | 同一body，不另Hostkey |
| 循环与分核 | 相同32B task分配 | 相同 | T2048 |
| Queue/TBuf/寄存器/dynamic UB/通信 window | 同一6208B双槽TBuf | 同样分配 | 不能按跳过载入扣UB |
| 内存总占用与复用 | 两槽/两个GM输出 | 相同 | 无workspace |
| 搬运/Vector/SIMT/NDDMA/通信 API | 读topk及slot行 | 不读topk/slot，直接填miss | 均写64结果 |
| 同步、精度与 tail | MTE2_V→V_MTE3 | bridge→V_MTE3 | 全64，无浮点 |
| fallback/失败边界 | slot值协议仍caller负责 | 确定0/-1 | 非法token另走UB sentinel |

## 平台差异

| 项目 | A2 | A3 | Ascend 950 |
|---|---|---|---|
| 支持状态 | arch22构建信号，本卡未冻结验收 | 本卡draft | 默认A3集合不编入 |
| Host/Launcher | 不外推产品保证 | 读取AIV核数并限制G | 不凭文件存在推支持 |
| Kernel/资源 | 未作独立确认 | AIV_ONLY/6208B必要预算 | 无950正式卡 |

## 限制与失败边界

- slot值必须遵守-1或有效非负槽协议，Host不检查；hit实际公式不是任意整数的非负比较，position也不是强制-1的值域归一化。
- map与输出/索引错误alias、并发写map或current设备不匹配没有自动修复，caller须满足异步owner/stream协议。
- 原生Torch接口某些shape比较先窄化，Python正常分配契约不能向下提升为所有极端大shape的强拒绝保证。
- 专属测试定义block_dim0/1/2/8/16/24/32/48、非法req/token、T非2048及错误map dtype；参考对slot做>=0，但数据仅-1或常规正槽，未覆盖<-1/INT32_MAX边界。本次未运行。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | python/sgl_kernel_npu/sgl_kernel_npu/sparsity_driven_kv_offload/ops.py | slot_map_lookup | 分配与返回 |
| 包导出 | python/sgl_kernel_npu/sgl_kernel_npu/sparsity_driven_kv_offload/__init__.py | exports | 公开调用 |
| 包装载 | python/sgl_kernel_npu/sgl_kernel_npu/__init__.py | _load_sgl_kernel_npu | 原生库 |
| Torch ABI | csrc/pytorch_extensions.cpp | schema/impl | 输出可变及宏 |
| Host | csrc/sparsity_driven_kv_offload/slot_map_lookup/op_host/slot_map_lookup.cpp | slot_map_lookup | guard/核数/stream |
| entry/body | csrc/sparsity_driven_kv_offload/slot_map_lookup/op_kernel/slot_map_lookup_kernel.cpp | KernelSlotMapLookup | 完整数据/事件流 |
| launcher | csrc/utils/torch_helper.h | EXEC_KERNEL_CMD | 裸参数/错误边界 |
| 声明宏 | csrc/utils/defines.h | HOST_API | 可见性 |
| 构建 | cmake/legacy_kernels.cmake | no_workspace_kernel | A3 Host/Device接线 |
| 场景 | csrc/sparsity_driven_kv_offload/README.md | data path | primitive用途 |
| 测试 | tests/python/sgl_kernel_npu/test_slot_map_lookup.py | TestSlotMapLookup | 定义用例 |
| CI矩阵 | .github/workflows/pr-test-kernels.yml | kernel groups | CANN9.1/A3构建配置 |
| CI调用 | .github/workflows/pr-test-kernel-group.yml | prepare step | 容器接线 |
| CI构建 | scripts/prepare_kernel_tests.sh | build.sh -a kernels | legacy整体构建 |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 五地址+四u32 | 单位、顺序和G在launch | entry |
| 调用顺序 | guard→record_stream→launch | current设备及owner | Host/helper |
| workspace/内存 | 6208B、两槽、65行/槽 | sentinel与offset区 | Init |
| 同步 | MTE3_MTE2、MTE2_S/V、V_MTE3 | 非法reqbridge与drain | Process |
| 精度与尾块 | int32原slot与实际min(slot+1,1) | 固定2048/64/8粒度 | Gather/Vector |
| 失败边界 | guard抛错，非法设备索引miss | 不扩大slot值或产品范围 | Host/Process |
