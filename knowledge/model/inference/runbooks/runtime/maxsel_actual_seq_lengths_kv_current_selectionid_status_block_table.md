---
{
  "type": "Runbook",
  "title": "GLM-5.2 offload Scheme B：AscendC kernel-side 当前-token 直写算子替代 host blend（精度修复 + 可入 npugraph_ex）",
  "description": "Ascend NPU（构建目标ascend910_93，实际产品未确认，CANN cann-9.1.0-beta.1）GLM-5.2 KVCache offload + gather prefetch（Scheme B，11 层裁剪权重 smoke：4 卡、pa_block_size=128、topk=2048、unquant bf16）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# GLM-5.2 offload Scheme B：AscendC kernel-side 当前-token 直写算子替代 host blend（精度修复 + 可入 npugraph_ex）

## 适用场景

Ascend NPU（构建目标ascend910_93，实际产品未确认，CANN cann-9.1.0-beta.1）GLM-5.2 KVCache offload + gather prefetch（Scheme B，11 层裁剪权重 smoke：4 卡、pa_block_size=128、topk=2048、unquant bf16）。当 host 侧用 `selected_kv = buf*(1-mask) + cur*mask` 形式的 blend 修补 selection 缓冲"脏当前-token 槽位"导致 eager 从第 8 个 token 起精度发散、且该 host 索引操作无法进 npugraph_ex 时，用单个 AscendC in-place 算子把直写下沉到 kernel。

## 触发与观测

- 触发（source 0 seq 1，任务书引既有诊断）：Scheme B 双 bug——① npugraph 入图 507011、② eager 第 8 token 起精度发散；诊断结论两个 bug 都由 host 侧 `scatter_current_token` 引入：`selTopKBlockSize=1` 路径下当前 token 的真实 selection 槽位由 insertIdx 决定，`PostHandleTopk`/`SwapMaxTopkLast` 在 block_size<=1 时整个被跳过，host 假设的 `actual_seq-1` 槽位从根上就错。
- 修复后观测（source 0 seq 190/253）：standalone NPU 算子测试 `RESULT: PASS`；eager 4 卡 `model run success`，decode 输出与 baseline 逐字节一致（`teas.case Phar OutputspreviewModelCreating基斯坦ilih gallon JeansPalindrome世界第一...`）。

## 探针与操作

- 新算子 `scatter_current_token_to_selection`（ops/ascendc/src/，镜像 scatter_nd_update_asc 模板：op_host def/proto/tiling + op_kernel；CMake `op_add_subdirectory` 自动发现新目录）。kernel 语义（source 0 seq 111 文件头注释逐字）：
```c
 * Per (batch, seq) row r:
 *   maxSel = actual_seq_lengths_kv[r] - 1            // the current token's selectionId
 *   find slot s in status[r, 0:topk] with status==maxSel  // the current token's real slot
 *   phys = block_table[r][s / selKvBlockSize] * selKvBlockSize + (s % selKvBlockSize)
 *   selected_kv_nope.view(-1, kvCacheDim)[phys] = cur_token_nope[r]
 *   selected_kv_rope.view(-1, kRopeDim)[phys]   = cur_token_rope[r]   // skipped if ifQuant
```
  关键设计：所有 DMA 地址在 kernel 内从 GM 值（status/block_table）计算，不用 host 侧值依赖的高级索引（507011 stale-pointer 家族规避）；写为每行单次 in-place DataCopyPad，不扰动 npugraph 冻结内存池。
- torch 侧注册（source 0 seq 141 逐字）：in-place schema + PrivateUse1/Meta 双实现（npugraph_ex 只需要 Meta 纯 shape，GLM-5.2 不走 torchair GE converter）：
```python
    m.def("scatter_current_token_to_selection(Tensor(a!) selection_kv_cache, Tensor(b!) selection_k_rope, "
        "Tensor selection_kv_block_table, Tensor selection_kv_block_status, Tensor cur_token_nope, "
        "Tensor cur_token_rope, Tensor actual_seq_lengths_kv, int if_quant=0) -> ()");
```
- 加载方式：`torch.ops.load_library(custom_ops_lib*.so)` 注册全部 `torch.ops.custom.*`（含 Meta），只把 gather 手工挂到 torch_npu；**不要 `import custom_ops`**（其 `__init__` 会整批覆盖可用的 torch_npu 内建算子如 npu_moe_gating_top_k）。aclnn ABI 顺序：in-place/输入张量按 def 顺序，后接属性。
- 编译注意（source 0 seq 167-176）：`CeilAlign` 不是全局 AscendC helper，是 gather kernel 自己的私有成员函数——新 kernel 须自带对齐 helper；kernel 混合 UB 标量读（GetValue 后 DMA）与 DMA 写时用 `--cce-auto-sync=on` 保守同步。安装 `.run` 会整体替换 vendors/customize 包，须全量 build 而非 `-n` 单算子包。

## 机制与判别

- 精度根因判别：host blend 的槽位假设错误（insertIdx 决定真实槽位 vs 假设 actual_seq-1）；kernel 侧改为运行时扫描 `status[r,0:topk]==maxSel` 找真实槽位，物理地址公式与 gather kernel ProcessGatherTopK（L525-531，selKvBlockSize=128）完全一致，保证写入行即 gather/SFA 读出行。
- standalone 判别（source 0 seq 190）：构造跨 block 场景（slot→phys 含 3048/4096/6344 多物理块映射）、status 末列（actual_seq 计数列）不参与扫描、只写 batchseq 行——物理行映射、末列排除、无越界写均 PASS，Meta dispatch 无异常。
- 507011 残余与 kernel scatter 无关的证据：换 kernel scatter 后首次 npugraph 仍 507011，但 plog 故障 kernel 是侧流 `GatherSelectionKvCache_..._2`（见另一卡 w13-s1-c5），非新算子。

## 验证信号

- 设备级（等级：设备功能，单卡 standalone + 4 卡 e2e）：算子单测 RESULT: PASS（source 0 seq 190）；eager 4 卡 model run success + 输出与 baseline 逐字节一致（source 0 seq 253）；kernel-side scatter + 主流 prefetch 后 npugraph_ex 入图成功、零 507011/illegal/fault、输出逐字节一致（source 0 seq 256-259）。
- 局限：11 层裁剪权重 + 4K 短序列 + 小 batch 的 bring-up 规模；性能非目标（本工作点 prefetch 整体净负的结论见原仓 progress 记录，不在本卡断言）。

## 适用与失效边界

- 适用：npu_gather_selection_kv_cache offload 体系（selection_kv_cache/block_table/status 布局不变）；需要把"按值定位槽位再直写"下沉为可 capture 的 in-place 自定义算子的同类场景。
- 失效/不覆盖：ifQuant=1（rope 空张量路径）未在板测覆盖（smoke 为 unquant）；status 扫描假设每行恰好一个匹配槽位（重复 maxSel 行为未定义）；性能收益未测量；`--cce-auto-sync=on` 的保守同步对性能的影响未评估。

## 附：断言存档

- GLM-5.2 offload Scheme B host blend 精度发散（第 8 token 起）根因是槽位假设错误：selTopKBlockSize=1 路径下当前 token 的真实 selection 槽位由 insertIdx 决定，PostHandleTopk/SwapMaxTopkLast 在 block_size<=1 时整个被跳过，host 假设 actual_seq-1 槽位从根上就错；修复=新 AscendC 算子 scatter_current_token_to_selection 在 kernel 内扫描 status[r,0:topk]==actual_seq-1 找真实槽位，物理地址 phys = block_table[r][s/selKvBlockSize]*selKvBlockSize + s%selKvBlockSize 与 gather kernel ProcessGatherTopK 完全一致。
