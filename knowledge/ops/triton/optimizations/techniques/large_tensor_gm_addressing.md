---
type: Optimization
title: 大 tensor 的 2D GM 寻址限制与 1D 平铺/M 切块
description: 大缓冲的偏移一旦超过 2^31 元素，int32 偏移会触发 vector core exception（invalid GM address 类）；改用 int64 偏移或 1D 平铺并按 M 切块可正常执行。
tags: [task.optimization, topic.memory, topic.data_movement.layout_transform]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/865691e2e9b656bc58008170207b4108d92e8dd1/docs/zh/triton_api/Memory_Pointer_Ops/tl.make_block_ptr.md
  role: primary
created_at: '2026-11-21T00:00:00Z'
updated_at: '2026-11-21T00:00:00Z'
platforms: ['950']
---
# 大 tensor 的 2D GM 寻址限制与 1D 平铺/M 切块

## 现象
- 触发条件不是 buffer 大小本身，而是**偏移/地址实际超过 2^31 元素**：整网格 kernel 用 `pid * BLOCK + arange` 计算 int32 偏移时，8 GiB（4.295e9 元素）会报 `vector core exception`（`rtDeviceSynchronizeWithTimeout`，device error type 3，error code 507035）；同 shape 改 int64 偏移则整缓冲回读正确。
- 单 program 只写首/中/末 tile 的探针在 4 / 8 / 12.9 / 20.5 GiB 上，2D 与 1D、int32 与 int64 偏移都未报错且回读正确——说明"大 buffer 就崩"的说法不成立，必须看偏移是否越界。
- 1D 平铺 + int64 偏移可正常执行；2D tile 的行 stride 过大属性能选型问题（见
  [多输出 GEMM 链的融合与单 launch 化](multi_output_gemm_chain_fusion.md) 的面板切分条目；原「矩阵约束 L1.1」已删除），
  不是本卡的正确性边界。
- **探针口径（两条路径必须区分）**：整网格探针按 `idx = pid * BLOCK + tl.arange(0, BLOCK)` 计算，`pid` 为 int32，
  `pid * BLOCK` 在 device 侧以 int32 求值，元素数越过 2^31 时该乘积本身溢出；单 program 探针的 tile 起始下标
  由 host 以 Python int 传入（落 i64 标量），tile 内 `arange` 仍是 int32，乘法前已提升为 i64，所以 8 GiB 的末 tile
  也能通过。**"单 program 通过"只说明该路径没触发 int32 乘法溢出，不能据此判定整网格安全。**

## 做法
- 大缓冲改成 1D 平铺 + int64 偏移（或保留 2D 但用 int64 计算偏移）。
- 按 M 切块，使单块元素数 < 2^31（bf16 约 4 GiB）；块内仍可用 int32 偏移。
- 1D 平铺路径可作为 2D 路径的对照验证手段。

## 规则
- 大 shape 先跑 1D 平铺 smoke；2D 失败时不要先怀疑数值。
- sketch 记录大缓冲的寻址方式与切块大小。

**范围**：本节数据仅来自 Ascend950PR（957c/V100、CANN 25.7.rc1.7、torch 2.14.0、triton-ascend 3.6.0）；
**A2 未验证**，其他 SoC/编译栈需按上面的最小探针重跑后再引用。

## 实验环境与实测数据

**软硬件范围（本节全部数据均来自这一环境）**

| 项 | 值 |
|---|---|
| SoC / 板 | Ascend950PR（Chip 957c，Chip Version V100），单片 HBM 约 84 GiB |
| 设备 | 单卡运行，`ASCEND_RT_VISIBLE_DEVICES=2` |
| CANN | 25.7.rc1.7 |
| PyTorch / torch_npu | 2.14.0+cpu / 2.14.0 |
| Triton | triton-ascend 3.6.0 |
| Python / OS | 3.10.22 / Linux 6.8.0-149-generic x86_64 |

**最小探针（整网格路径，bf16，`BLOCK=8192`）**

```python
import torch, torch_npu, triton, triton.language as tl

BLOCK = 8192


@triton.jit
def fill(out_ptr, BLOCK: tl.constexpr, OFF64: tl.constexpr):
    pid = tl.program_id(0)
    if OFF64:
        idx = pid.to(tl.int64) * BLOCK + tl.arange(0, BLOCK).to(tl.int64)
    else:
        idx = pid * BLOCK + tl.arange(0, BLOCK)          # int32 乘法，越 2^31 元素即溢出
    tl.store(out_ptr + idx, tl.full((BLOCK,), 1.0, dtype=tl.bfloat16))


def run(gb, off64):
    n = int(gb * 1024**3) // 2                            # bf16 元素数
    buf = torch.zeros(n, dtype=torch.bfloat16, device="npu")
    fill[(n // BLOCK,)](buf, BLOCK=BLOCK, OFF64=off64)
    torch.npu.synchronize()
    return bool((buf.float().cpu() == 1.0).all().item())


print(run(4.0, False), run(4.0, True))   # 4 GiB（2^31 元素内）：True True
print(run(8.0, True))                    # 8 GiB + int64：True
print(run(8.0, False))                   # 8 GiB + int32：回读错误或 vector core exception
```

单 program 探针（只写首/中/末 tile）与此不同：tile 起始下标由 host 以 Python int 传入（i64 标量），
tile 内 `arange` 仍是 int32，乘法前已提升为 i64，因此 8 GiB 的末 tile 也能通过；它只说明该路径没触发
int32 乘法溢出，不能据此判定整网格安全。

**实测（bf16，`BLOCK=8192`，整网格覆盖全缓冲）**

| 缓冲 | 元素数 | int32 偏移 | int64 偏移 |
|---|---|---|---|
| 2 GiB | 1.07e9 | 回读全对 | 回读全对 |
| 4 GiB | 2.147e9（=2^31） | 回读全对 | 回读全对 |
| 3 GiB | 1.611e9 | 回读全对 | 回读全对 |
| 6 GiB | 3.221e9 | **vector core exception** | 回读全对 |
| 8 GiB | 4.295e9 | **vector core exception**（code 507035） | 回读全对 |

单 program 探针（只写首/中/末 tile）：4 / 8 / 12.9 / 20.5 GiB × {2D, 1D} × {int32, int64} 全部通过，
回读正确。

**判据补充（3 / 6 GiB 两个新测点）**：3 GiB（1.611e9 元素 < 2^31）int32 正常；6 GiB（3.221e9 元素 > 2^31）
int32 已报 `vector core exception`，int64 正常。因此边界与"元素数是否越过 2^31"一致，而不是某个固定 GiB 数；
换 dtype 时按 `2^31 × itemsize` 换算。

**复核方式**：与上表同环境，分配目标大小的 bf16 buffer，用整网格 kernel（`pid * BLOCK + arange`）
写满并回读；再对同 shape 换成 int64 偏移对照。记录报错原文与回读结果，确认"偏移是否越界"这一变量。

## 适用性

- 数据来自上表单 SoC、单栈；`2^31` 是 int32 偏移的表示上限，与 SoC 无关，但报错形态与栈版本有关。
- 原始问题出现在 12.9–20.5 GB 的 buffer（对应 6.9e9–1.1e10 元素，均超过 2^31）；更小的 buffer 只要
  偏移越界同样会触发，所以按"元素数/偏移范围"判断而不是按 GB 判断。
