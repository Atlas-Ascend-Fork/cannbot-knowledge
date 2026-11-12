---
type: Operator
title: "GateMultiplyLargeContiguous 950 Direct Invoke 算子知识"
description: "闭合N不少于16777216且双连续的BF16×FP32 gate乘法自有Kernel域，保留全入口Torch缺源、设备缓存与950未验证边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/elementwise/gate_multiply.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/gate_multiply.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/elementwise/gate_multiply.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
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
created_at: "2026-11-09T09:56:03Z"
updated_at: "2026-11-09T09:56:03Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# GateMultiplyLargeContiguous 950 Direct Invoke 算子知识

## 算子速览

精确 `sgl_kernel_npu.implementation.triton.elementwise.gate_multiply.gate_multiply(y,gate)`，独立冻结 `y.numel()≥16777216、y/gate均contiguous` 的自有Kernel域。BF16y提升FP32乘FP32gate再BF16写出，保持此前归一化舍入；不计算sigmoid或norm。此域全部自有Host/单Device闭合，选VV；原全入口的小/非连续Torch核心数学分支仍缺源，不以本卡代表全域。

draft保留950公开未验证、原始Direct不调publiccheck、设备属性cache与资源/整数边界；无当前实测收益。已有[公开API](../../../../apis/sgl_kernel_npu/sgl_gate_multiply.md)全文读并复用。

## 接口与语义

### 计算语义

`out=BF16(FP32(y)*gate)`。gate已由调用方算sigmoid，输入y已完成BF16norm舍入。FP32乘法、最终BF16store，显式enable_fp_fusion=False；公开报告与表达式有限值逐位一致/NaN位置一致，这是上游合同，不是本次运行或NaNpayload位同证明。

### 输入、输出与属性

| 项 | 冻结合同 |
|---|---|
| y | NPU BF16，任意shape、连续，N≥16777216 |
| gate | 同shape/同NPU FP32、连续，已完成sigmoid |
| requires_grad | 两者均False（推理合同）；Direct未调用门面check |
| out | empty_like(y)新BF16同shape/device，输入不写 |
| 不在本域 | N<threshold或任一非连续，原入口返回外部Torch核心表达式 |

### 入口与版本

本入口参数(y,gate)，短路径无新增wrapper符号，scope由冻结semantic_predicate给定。auto/triton转发；public_check_inputs原会验证dtype/同device/shape/无grad，Direct绕过。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0来自README/CI配置非本次环境；完整Triton二进制未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

入口先按N与contiguous检查分支，本冻结域确保false，不进入:47Torch表达式。with torch.npu.device(y.device)上下文→empty_like→helper核数P→_multiply grid(P,)、B4096、enable_fp_fusionFalse。非空/阈值已由predicate确保，无输出copy。Direct没有重复公共dtype/shape/gradguard。

### 参数、Workspace 与生命周期

只分配2N B输出，没有全尺寸FP32 y或乘积GM临时，无workspace/POD/ACLNN。device上下文确保当前选择y.device，但helper无参cache仍可能复用先前设备核数，需核对属性相容；不能把有deviceguard解释为cache已按devicekey区分。输出/输入异步存活、stream及context退出后当前设备恢复归Torch/Triton合同，未显式hostwait。

### 启动图与失败传播

import→分支predicate→deviceguard→output→helper→单Kernel→return并退出devicecontext。无本域fallback或其它算法Kernel；异常直接传播。包原生库是导入依赖而非本math图。source全域:47仍未闭合，不将其排除伪写为完整全入口支持。

## Route 与参数设计

### 分核与资源计算

T=ceil(N/4096)，program p循环block=p+jP<T；每block4096连续元素，tail offsets<N。余数映射唯一覆盖所有输出，无跨program共享写。N是runtime并do_not_specialize，gridP；图捕获前需要目标工具链正常预热，不宣称函数运行时自动预热成功。

### Route 选择

| Route | 条件 | 设备 |
|---|---|---|
| R-001 | 冻结大连续域、公共BF16/FP32推理合同 | _multiply |
| 非本卡域 | 小/非连续 | 外部Torchmath缺源，不建成功Operator |

### 模板/实现执行矩阵

唯一dtype组合BF16y/FP32gate/BF16out、block4096；没有autotune、物理硬件分支或Cube/tl.dot/AIC/MIX节点。原source无arch35guard，大连续950会尝试同body，不能据此称已验证/有收益。

### 隐藏性能 Guard

阈值16777216在910C测得，仅决定分支，不是所有SoC最优或资源证明。4096逻辑SSA不等物理UB字节；N/offset/iteration算术须实际JIT可表示，源码未显式int64转。Pcache跨device与physicallowering仍外部。

### POD/ABI

| 字段 | 分类/消费 |
|---|---|
| Y/G/O | runtimeTensor指针，BF16读/FP32读/BF16写 |
| N | runtime、do_not_specialize→cdiv/mask |
| B | constexpr4096→arange/blockstride |
| grid | (P,)；P由num_programs用于循环 |
| enable_fp_fusion | False launchflag，非POD字段 |

无序列化结构/字节offset，JIT标量位宽与pointerABI外部，不猜测。

### Route 源码闭包

全54行Direct/Device、publiccheck与helper已读。本predicate下只可达_multiply，自有math全闭合；另一核心Torch分支明确外于冻结域而未作普通前处理。根setup→stage_runtime完整Python包→build_wheel/setup_refactor，elementwise/backendinit无Device；devicecontext/empty为框架前处理，不隐藏数学。

## Kernel 实现

### 公共执行流程

每blockmaskedloady并toFP32、maskedloadgate、FP32乘、maskedstore自动转换BF16；没有中间GM、归约、通信或atomic。

### Route R-001：固定4096元素融合乘法

#### 适用条件

##### 选择证据

N≥16777216、双连续且公共dtype/shape/device合同；第42–47条件false，with分支真实launch，N维无specialize。

#### Device 数据流

##### 函数级调用链

`gate_multiply→torch.npu.device→helper→_multiply→tl.load/to(float32)/mul/store`，没有未知自有函数或Cube。

##### 源码等价伪码

for b=pid;b<ceil(N/4096);b+=P：i=b4096+arange4096；yf=loadY(i<N,0).float32，g=loadG(i<N,0)；storeO(yf*g,i<N)。没有显式把g转FP32，因为合同本身FP32。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| yload/toFP32 | 4096BF16→4096FP32，逻辑8KB/16KB但不等同时分配 |
| gate/product | 各4096FP32逻辑16KB |
| GM y/gate/out | 完整2N/4N/2N B，总8N B |
| workspace/TQue/TBuf/UB | 无显式分配，N/A；compiler物理复用/spill未知 |

##### 分层内存布局

`GMBF16y/GMFP32gate→FP32SSA[4096]→FP32product→GMBF16out`。无全尺寸FP32临时GM，源码不证明全部SSA在何种寄存器/UB。

##### 字节账与复用顺序

每完整block逻辑32768B读写总量（y8192+gate16384+out8192），tail m时8m B；完整8N B。输出allocation2N B，输入只读，异步生命周期依框架；无workspacehandoff/二次Kernel/显式free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 顺序 | load→FP32mul→store，SSA/enable_fp_fusionFalse由compiler执行，无显式event |
| program间 | 输出不交叠，无atomics/barrier |
| 尾 | 两load/store同offset<N，补0不写无效尾 |
| 精度 | 已BF16y再提升、gateFP32、storeBF16，不提前改变归一化舍入 |
| NaN | 上游要求位置一致，不把NaNpayload当位同；本次未运行 |
| stream | 当前框架stream/allocator管理，未host同步 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| _multiply | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/gate_multiply.py#L21-L27) |
| predicate/guard/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/gate_multiply.py#L42-L54) |

## 算子特定优化

### Trick T-001：提升乘法与BF16写出融合为一次流式遍历

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/gate_multiply.py#L21-L27)：

```python
@triton.jit(do_not_specialize=["N"])
def _multiply(Y, G, O, N, B: tl.constexpr):
    for block in range(tl.program_id(0), tl.cdiv(N, B), tl.num_programs(0)):
        offsets = block * B + tl.arange(0, B)
        y = tl.load(Y + offsets, offsets < N, other=0).to(tl.float32)
        g = tl.load(G + offsets, offsets < N, other=0)
        tl.store(O + offsets, y * g, offsets < N)
```

#### 机制与设计原因

只在任务SSA里保留FP32提升/乘积，避免物化全尺寸两份FP32GM中间值，逻辑数据流8N B。没有复现910C阈值收益或估算实际DMA事务。

#### 迁移边界

输入已BF16舍入且gateFP32，必须保持最终storeBF16与禁用fp-fusion的实际参数；小/非连续原分支不能由此卡推出完整源码闭包。

#### 错误做法

把此函数当sigmoid/norm融合，或把y在归一化前提升改变已有舍入。

### Trick T-002：当前设备上下文内选择输出与核数

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/gate_multiply.py#L48-L54)：

```python
    with torch.npu.device(y.device):
        out = torch.empty_like(y)
        _, num_vectorcore = get_device_properties()
        _multiply[(num_vectorcore,)](
            y, gate, out, y.numel(), B=4096, enable_fp_fusion=False
        )
        return out
```

#### 机制与设计原因

deviceguard包围分配与launch；runtimeN保持动态，block4096固定。helper已有无参cache限制，guard不自动使其device-sensitive。

#### 迁移边界

调用前满足同device合同、设备cache属性相容；runtimeN的编译/图预热仍由Triton处理。

#### 错误做法

因有deviceguard就宣称任何跨设备cache均更新，或将threshold当950的实测收益结论。

## 模板与实现对比

唯一冻结大连续路线闭合；原全入口fallback缺源仍defer。source无archguard与文档arch35说明分开记录，draft不把未验证写成明确不支持。publiccheck仅门面而非Direct可达。

## 平台差异

本卡950归属arch35；arch22公开支持，融合threshold报告在A3/910C；arch35Triton未验证，doc还称表达式路径而source无archguard。950卡只表示固定源码大连续路线及待验证事实，不声称公开已验收/收益；README/architecture映射归属、CANN9.1.0 CI非本次运行。

## 限制与失败边界

predicate必须严格、Direct缺guard，推理dtype/device/shape和异步生命周期由调用者确保。物理资源/JIT整数域/cache相容未完整guard，无编译、真机、测试/校验或性能结果；draft保留平台未验证与不支持的区别。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/elementwise/gate_multiply.md) | `gate_multiply` | BF16×FP32/阈值/arch35未验证 |
| [Direct/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/gate_multiply.py) | `gate_multiply/_multiply` | 54行；冻结只48–54自有域 |
| [publiccheck/适配](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/elementwise/gate_multiply.py) | `_check_inputs/_triton_impl` | Direct不调用check |
| [elementwise包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/__init__.py) | `module init` | 无Device |
| [设备helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | current_device、无参cache、两核数assert |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacyAPI已全文读并链接，原gate全域不产卡；此独立predicate仅创建新scoped两平台目标，不覆盖API。全部固定同repo唯一primary，无verified。
