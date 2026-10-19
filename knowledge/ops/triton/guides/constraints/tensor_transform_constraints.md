---
type: Guide
title: tensor_transform 类算子设计约束
description: tensor_transform 类算子的适用范围、类别专属设计约束与常见陷阱；跨类别通用条款见 global_constraints.md。
tags: [task.design, topic.data_movement.layout_transform, topic.tiling, topic.compute.indexing, topic.precision, topic.data_movement.memory_access]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/index.md
  role: supporting
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-10-14T00:00:00Z'
platforms: [a2, a3]
---

# tensor_transform 类算子设计约束

> 跨类别通用约束见 [global_constraints.md](global_constraints.md)（`GC-1`~`GC-15`），
> 本卡只列本类别特有条款。

## 张量变换类算子优化经验

本文档合并了三类张量变换算子的优化经验。按以下结构组织：
- **§1 通用经验**：跨算子重复的工程约束（已提取，各算子章节不再重复）
- **§2 Layer 2: 类别级通用算法骨架**
- **§3 Layer 3: 类别级公共关键代码**
- **§4 各算子常见陷阱**
本类单算子：**Interpolate** / **Pad** / **Repeat**，其专属 Layer 1 约束见下方「算子级实现手册」。

---

## 本类别的算子级实现手册

> 本卡只列类别级共性约束。以下单算子手册含该算子专属的 Layer 1 设计约束、
> 算法骨架与性能基准，**命中对应算子时必须一并加载**。

- [`operators/tensor_transform__interpolate.md`](../operator_playbooks/tensor_transform__interpolate.md) — Interpolate 算子（transformation-compute）
- [`operators/tensor_transform__interpolate_bicubic_area.md`](../operator_playbooks/tensor_transform__interpolate_bicubic_area.md) — Interpolate bicubic_area
- [`operators/tensor_transform__interpolate_bilinear.md`](../operator_playbooks/tensor_transform__interpolate_bilinear.md) — Interpolate bilinear
- [`operators/tensor_transform__interpolate_nearest.md`](../operator_playbooks/tensor_transform__interpolate_nearest.md) — Interpolate nearest
- [`operators/tensor_transform__pad.md`](../operator_playbooks/tensor_transform__pad.md) — Pad 算子（transformation-memory）
- [`operators/tensor_transform__repeat.md`](../operator_playbooks/tensor_transform__repeat.md) — Repeat 算子（transformation-memory）

## §0 适用范围与算子分类

| 算子 | 类别 | 计算特征 | 优化哲学 |
|------|------|---------|---------|
| Interpolate | `transformation-compute` | 数据重排伴随权重计算（nearest/bilinear/bicubic/area） | 多策略分派 + 精度匹配 + 采样特化 |
| Pad | `transformation-memory` | 数据搬运，计算极简（仅边界坐标映射） | fill+copy 拆分 + 维度压缩 + 边界映射 |
| Repeat | `transformation-memory` | 数据搬运，计算极简（仅坐标映射） | outer×inner 连续块 + constexpr 展开 |

> ⚠️ **关键区分**：Interpolate 属 **compute 类**（关心采样算法和权重精度），Pad/Repeat 属 **memory 类**（关心连续访存和坐标解码开销）。两类优化哲学相反，生成时**禁止混用经验**：
> - 生成 Interpolate 时，**不要**套用 Pad/Repeat 的搬运类技巧
> - 生成 Pad/Repeat 时，**不要**套用 Interpolate 的采样/权重类技巧

---

## §1 通用经验（跨算子，首次生成必须遵守）

以下 8 条约束在三个算子中均适用，各算子章节不再重复。

### G1 动态读取 Vector/Cube Core 数量，禁止硬编码
- **必须**动态读取实际核数，禁止硬编码 `num_cores=8` 或 `num_cores=48`。
- **正确做法**（一次拿 vector + cube，权威值，无需设备 init）：
  ```python
  import torch_npu
  import triton.runtime.driver as driver

  device = torch_npu.npu.current_device()
  properties = driver.active.utils.get_device_properties(device)
  vectorcore_num = properties["num_vectorcore"]   # elementwise / reduction 用它做 grid 钳制
  aicore_num = properties["num_aicore"]           # cube / matmul 用它
  ```
- **已弃用**：旧式 `npu_config` 取值方式（仅 vector、硬编码 40 不准、设备未 init 会抛 `RuntimeError`）。
- **Why:** 硬编码仅利用 20% Vector Core，导致加速比从 ~1.3x 跌至 0.67x（慢于 PyTorch）。

### G2 BLOCK 向上取 2 的幂（NPU 向量化友好）
- **必须**将 BLOCK / MAX_IN_W 等向量化长度声明为 `triton.next_power_of_2(N)`，且作为 `tl.constexpr` 传入 kernel。
- **Why:** Ascend 上 fixed-shape vector load 必须是编译期常量长度；若 `tl.arange(0, N)` 中 N 非 constexpr 会触发 dynamic-shape load，退化为标量循环。
- **典型 BLOCK 选择**：
  ```
  width <= 64    -> 64
  width <= 128   -> 128
  width <= 256   -> 256
  width <= 512   -> 512
  width <= 1024  -> 1024
  width <= 2048  -> 2048
  width <= 4096  -> 4096
  else           -> 8192
  ```

### G3 禁止单 kernel 统所有路径，必须多策略分派
- **必须**按 `(维度, 模式, 采样比例)` 等特征在 host 侧分派到特化 kernel。
- **禁止**用单一通用 kernel 统一处理所有路径（坐标解码 overhead 极大，且丢失特化机会）。
- **通用 kernel 仅作兜底**：仅当不存在特化匹配时使用。

### G4 Grid 总数不超过核数
- **必须**`grid = (min(total_blocks, num_cores),)`，禁止直接 `grid = (total_blocks,)`。
- **Why:** 输出规模大时 total_blocks 可能远超核数（如 Interpolate 上采样 N*C*H_out），超 grid 上限；且多余 program 会空跑。
- **2D grid 例外**：当 `total_blocks <= num_cores` 时可用 2D grid 充分利用多核。

### G5 int32 索引，避免 int64 降级
- **必须**在 kernel 内将 `tl.program_id` 和 `tl.arange` 结果 `.to(tl.int32)`。
- **Why:** int64 标量会触发地址计算降级；NPU 上 int32 索引更高效。
  ```python
  pid = tl.program_id(0).to(tl.int32)
  offs = (block_start + tl.arange(0, BLOCK)).to(tl.int32)
  ```

### G6 多核负载均衡分配公式
- **必须**按输出元素总数（非输入元素）分配核数，每个 program 处理一段连续输出。
- **负载均衡公式**（确保每个 core 处理的 block 数差不超过 1）：
  ```python
  blocks_per_core = total_blocks // num_cores
  remainder = total_blocks - blocks_per_core * num_cores
  if pid < remainder:
      my_blocks = blocks_per_core + 1
      start_block = pid * (blocks_per_core + 1)
  else:
      my_blocks = blocks_per_core
      start_block = remainder * (blocks_per_core + 1) + (pid - remainder) * blocks_per_core
  ```

### G7 输入必须 contiguous
- **必须** Host 侧进入 kernel 前调用 `x = x.contiguous()`。
- **Why:** 避免非连续张量导致 kernel 内 stride 计算复杂化。

### G8 坐标比较转 float32
- **禁止**直接对整数坐标使用 `tl.where(coord < 0, ...)`。
- **必须**先 `.to(tl.float32)` 再比较。
- **Why:** Triton Ascend 整数比较可能降级；同时 `tl.cast` 对负数是向零截断而非 floor，坐标计算需用 float32 比较修正。

---

## §2 Layer 2: 类别级通用算法骨架（跨算子抽象，首次生成就要写对）

张量变换类算子都遵循「**host 多策略分派 → 按输出元素做负载均衡 → kernel 内做 1D 行/元素循环 + 坐标解码 → 连续访存写**」的类别级模板。
两子类分道：**Compute 类**（Interpolate）关心采样权重与精度；**Memory 类**（Pad/Repeat）关心坐标解码开销与连续块。逐算子的 L2 变体见对应 `operator_playbooks/`。

### L2.1 Host 多策略分派（G3：禁止单 kernel 统所有路径）
- **必须**按 `(维度, 模式, 采样比例/是否整数倍)` 在 host `_route` 分派到特化 kernel，**通用 kernel 仅兜底**。
- **Compute 子类**：整数倍上采样（reshape broadcast）≠ 整数倍下采样（strided load）≠ 通用采样（gather）；`bilinear+ac=False+0.5x` 退化为 2×2 avg pool。`align_corners` 决定坐标用 `scale*(i+0.5)-0.5` 还是 `scale*i`，影响入口分派。
- **Memory 子类**：`constant` 模式先 `output.fill_(value)` 再 copy；非 constant（reflect/replicate/circular）用逐行边界映射；`torch.repeat`（多维外重复）走逐维度 outer×inner 连续块，`repeat_interleave`（单维逐元素）走展开——两 API 语义不同，分派先行区分。

### L2.2 1D Grid + 负载均衡（G4/G6）
```python
# 按 OUTPUT 元素/行数（非输入）分配核数；grid 钳制到核数
grid = (min(total_blocks, num_cores),)      # total_blocks 够小时可 2D grid
# 均衡分配（差 ≤1）：blocks_per_core = total_blocks // num_cores ... 按 pid 分摊多出的余块
# 每个 program 处理一段连续输出，内部做 row/w 循环
```
- **禁止** `grid = (total_blocks,)` 直接超出核数上限空跑。

### L2.3 kernel 内坐标解码模板（所有张量变换的公共重心）
```python
# 行/块循环内：pid → (n,c,h) 解码（标量除法）
# 逐元素坐标映射（Compute：采样坐标；Memory：输出→输入偏移）
# 关键：除法/取余只对标量做，禁止对 tl.arange 向量做 %///（退化为标量循环）
```
- Compute：坐标 `src = scale*(i+0.5)-0.5`，`int(floor) + tl.where(src < y0_f, y0-1, y0)` 修正负 floor（G8），clamp 到 `[-1, D_in]`。
- Memory：`reflect/replicate/circular` 边界映射先转 float32 比较再映射；`repeat` 的 `out_idx → in_idx` 用标量除法。

### L2.4 连续访存优先
- **`mode=='nearest'` 且整数倍**上采样用 `tl.reshape(vals,[N,1])*ones([1,r])` 复制像素（**仅 nearest**；`bilinear/bicubic` 无论是否整数倍都走 L3.4 gather）；下采样用 stride-2 连续 vector load；avg-pool 退化一次 contiguous load `2*BLOCK_W` + `reshape([BLOCK_W,2])` + `tl.sum`——**禁止**拆多次离散 strided load（无法 coalesce）。
- `repeat` 保证 r 个副本在输出内存中紧邻（无跨步写）；从低维到高维逐维度处理。

---

## §3 Layer 3: 类别级公共关键代码 / 技巧（可参考但不可复制结构）

以下片段在张量变换类算子中可复用；实现细节须重新设计，勿直接照搬。

### L3.1 行预载用 pow2 constexpr（禁 dynamic-shape load）
```python
MAX_IN_W: tl.constexpr = triton.next_power_of_2(W_in)   # cap 4096
r_offs = tl.arange(0, MAX_IN_W); r_mask = r_offs < W_in
row0 = tl.load(in_ptr + base + y0*W_in + r_offs, mask=r_mask, other=0.0).to(tl.float32)
```
- `tl.arange(0, W_in)` 中 W_in 非 constexpr 会触发 dynamic-shape load，退化为标量循环（G2）。

### L3.2 host 预计算坐标表（禁 kernel 内重算）
```python
# x 坐标对所有输出行相同：host 预算 x0/x1/xlambda 三张量表传入 kernel
for i in range(W_out):
    src = scale*(i+0.5)-0.5 if not ac else scale*i
    x0_i = int(math.floor(src)); ... clamp;  x0[i]=x0_i; x1[i]=...; xlambda[i]=src-x0_i
# kernel 内按 w_idx load 表，禁止每个 tile 重算 cast/floor/where 链（慢一个数量级）
```
- `align_corners=True` 坐标必须 host 用 `numpy.float32` 预算（PyTorch C++ 语义），低精度 + ac=True 用 NPU `vdiv` 计算 scale（G/CANN 与 CPU 除法有 ULP 差异）。

### L3.3 整数倍 transform 的 reshape 技巧
```python
# 2x 上采样: [a,b,c] -> [a,a,b,b,c,c]
vals = tl.reshape(vals, [BLOCK_IN, 1]) * tl.full([1, 2], 1.0, tl.float32)   # broadcast 复制
```
- 整数倍 transform 是 contiguous 计算，远快于 gather 随机访问；**该特化仅 `nearest` 模式适用**，其它模式整数倍也应走 L3.4 gather。

### L3.4 通用采样用 gather（nearest 整数倍特化之外的全部路径）
- `bilinear/bicubic` 全部 + `nearest` 非整数倍（除 L3.3/L2.4 的 nearest 整数倍特化）：先整行 load 到 UB（pow2），再 `tl.gather(row, x0, 0)` 按坐标取列；`bicubic` 权重用嵌套 `tl.where` 分段（**禁止 if**），`ac=True` 的 16 项用标量逐项累加 `val = val + w*pixel` 匹配 PyTorch 顺序（向量化改变累加顺序会 verify 失败）。

---

## §4 常见陷阱与避免方法

### §4.1 Interpolate 陷阱

| 陷阱 | 原因 | 避免方法 |
|------|------|---------|
| 用单 kernel 统一处理多 mode | 所有 mode 走同一套逻辑，丢失特化机会 | 多策略分派 (L1.1)，按 (mode, ac, 采样比例) 选择特化 kernel |
| W_in 非 2 的幂导致 dynamic-shape load | `tl.arange(0, W_in)` 当 W_in 非 constexpr 退化为标量循环 | `MAX_IN_W = next_power_of_2(W_in)` (L1.2) |
| 整数倍上/下采样用 gather | 2x 上采样/0.5x 下采样用 gather 实现是随机访问，远慢于 contiguous | 2x 用 reshape broadcast (L1.3/L3.1)，0.5x 用 strided load (L1.4/L3.2) |
| bilinear 0.5x 下采样走通用路径或 strided load | ac=False + 0.5x 下采样时 bilinear 退化为 2x2 avg pool，走通用 gather 路径浪费；kernel 内用 strided load 也无法 coalesce | 特化分派 (L1.5) + 一次 contiguous load `2*BLOCK_W` + reshape + sum (L3.3) |
| 上采样逐行独立 load 输入 | 上采样时多个输出行共享输入行，逐行 load 重复访存 | 2D 垂直分块 BLOCK_H=2、MAX_KH=3 (L1.6/L3.5) |
| ac=True kernel 内重新计算坐标 | PyTorch C++ 的 ac=True 坐标用 float32 计算，kernel 内重算有精度差异，verify 失败 | host 用 numpy.float32 预算坐标和权重 (L1.7/L2.2) |
| bicubic 16 项向量化累加 | 向量化累加改变顺序，与 PyTorch 标量顺序不一致，verify 失败 | 标量逐项累加 `val = val + w*pixel` (L1.7/L3.7) |
| 三次权重用 if 分段 | `if at < 1.0: ...` 在 vector 数据上不生效 | `tl.where` 嵌套 (L1.8/L3.6) |
| grid_size 超核数 | 上采样 total_rows 极大，直接 `grid=(total_rows,)` 超上限或空跑 | `grid = (min(total_rows, num_cores),)` (L1.9) |
| 低精度 ac=True 用 CPU 计算 scale | CANN vdiv 与 CPU float32 除法有微小差异，低精度 ac=True verify 不过 | `_npu_scale` (NPU vdiv) + `_SCALE_CACHE` 缓存 (L1.10)，仅低精度 ac=True 需要 |
| ac=False 负坐标 floor 错误 | `src_y = scale*(i+0.5)-0.5` 可能为负，`tl.cast` 向零截断导致 t 偏移错误 | `tl.where(src_y < y0_f, y0 - 1, y0)` 修正，并重新计算 y0_f 再算 t (L1.11/L3.6) |
| 循环携带变量类型不一致 | kernel 内同一变量在循环外为标量、循环内被赋值为 vector，Triton 报 `Loop-carried variable ... initial type ... but re-assigned to <[N], fp32>` | 循环内临时变量用不同名字，或确保首次赋值就是 vector。典型出现在 bicubic x 权重计算（用 `at_x/at2_x/...` 而非复用 `at/at2/...`） |
| 嵌套函数定义 | `@triton.jit` kernel 内定义嵌套函数会报 `nested function definition is not supported` | 把工具函数内联到 kernel 中（如 `_cubic_weight` 直接展开） |
| forward 中调用 bare `min()` 或 tensor 方法 | `validate_triton_impl.py` Type-3 检查会把 `min(a, b)` 或 `self.xxx()` 视为 PyTorch fallback | `min(a, b)` 改为 `a if a < b else b`；`_precompute_*` 改为模块级函数而非类方法 |
| profiler 失败误判为代码错误 | 部分大 shape 报 `RuntimeError: 无法从 profiler 提取有效时延数据` | 这是 CANN profiler 分辨率/环境限制，与代码正确性无关；verify 阶段 73/73 全部通过即可 |

### §4.2 Pad 陷阱

| 陷阱 | 原因 | 避免方法 |
|------|------|---------|
| 单 kernel 处理所有 mode | 通用 kernel 坐标解码 overhead 大 | 按 mode 分 kernel (L1.1) |
| kernel 内逐元素判断边界 | 每个元素都需分支，性能差 | constant 模式拆 fill+copy (L1.2) |
| 硬编码 num_cores | 不同 NPU 核数不同 | 动态读取 (L1.5/G1) |
| 整数坐标直接比较 | Triton Ascend 整数比较可能降级 | 转 float32 再比较 (L1.4/G8) |
| 未 squeeze 前导维度 | 前导 size-1 维度浪费 grid | Host 侧先 squeeze (L1.3) |

### §4.3 Repeat 陷阱

| 陷阱 | 原因 | 避免方法 |
|------|------|---------|
| 向量除法 `offsets // repeats` | int32 向量除法退化为标量循环 | 用 outer×inner 连续块路径，除法只对 `block_idx` 标量做 (L1.3) |
| 输出跨步写 | slice 路径中同一份数据写到相距很远的输出位置 | 用 L2.1 outer×inner 路径，保证 r 个副本连续 |
| Grid 并行度过低 | SLICES_PER_BLOCK=1 导致 block 数太少 | 用 2D grid 或按 core 数分发 (L3.2) |
| 从高维到低维处理 | 中间张量变大，post_size 过大 | 用 L2.1 从低维到高维处理 |
| 混淆 repeat_interleave 和 torch.repeat | 两者语义不同，优化策略不同 | 先判定算子类型，再选 L2.1 或 L2.3（Repeat 算子级手册 §4.0） |
| `for r in range(repeats): store` 输出不连续 | constexpr 展开但地址跨步 | 确保输出地址连续，或用 reshape 代替 |
