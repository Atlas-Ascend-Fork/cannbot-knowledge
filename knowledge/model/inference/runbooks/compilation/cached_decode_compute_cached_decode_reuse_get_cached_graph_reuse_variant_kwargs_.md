---
{
  "type": "Runbook",
  "title": "cache_compile 单 trace 约束下的 python-bool 分支拆双静态图（GLM-5.2 MTP IndexShare E8）",
  "description": "Ascend NPU 上以 `torch.npu.npugraph_ex.inference.cache_compile` / torchair `cache_compile`（ge_cache）为 decode 建静态图时，被缓存函数内存在**逐步翻转的 python bool 分支**（本例 GLM-5.2 MTP IndexShare variant A′ 的 `reuse_shared_topk`：step-0 由 indexer 计算 top-k，之后复用冻结的 `shared_mtp_topk`）。",
  "tags": [
    "task.implementation",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-20T14:17:03Z",
  "platforms": []
}
---

# cache_compile 单 trace 约束下的 python-bool 分支拆双静态图（GLM-5.2 MTP IndexShare E8）

## 适用场景

Ascend NPU 上以 `torch.npu.npugraph_ex.inference.cache_compile` / torchair `cache_compile`（ge_cache）为 decode 建静态图时，被缓存函数内存在**逐步翻转的 python bool 分支**（本例 GLM-5.2 MTP IndexShare variant A′ 的 `reuse_shared_topk`：step-0 由 indexer 计算 top-k，之后复用冻结的 `shared_mtp_topk`），需要在不触发 guard 重编译的前提下让两种分支都能入图。

## 触发与观测

任务输入：eager A′ IndexShare 已落地并 byte 验证（next_n=0/1/2/3 输出一致，share 在 next_n>=2 生效）；`model_infer.py mtp_post_process` 每步设置 python bool `input_dict_mtp['reuse_shared_topk']`，经 `decode(**model_inputs)` 进入被 cache_compile 包裹的 `main_decode_mtp`。若把该 bool 留在被 trace 的函数内，单图要么冻结首次 trace 的分支（share 失效），要么触发 guard 重编译——wiki（npu-graph-mode）确认约束：cache_compile 要求被缓存函数构成全图且**同一缓存函数只能触发一次 Dynamo trace**，guard 不同的路径应拆成独立封装。

## 探针与操作

E8 双图实现（全部改动限于 `models/glm-5.2/models/modeling_glm.py`，+84/-3；非 MTP / index_share 关闭路径保持单图 byte-identical）：

1. `__init__`（diff 逐字）：
```
+        self.cached_decode_compute = None
+        self.cached_decode_reuse = None
```
三重条件 `self.is_mtp and getattr(config, "index_share_for_mtp_iteration", False)` 下同时构建两图：
```
+                self.cached_decode_compute = self.get_cached_graph(reuse_variant=False)
+                self.cached_decode_reuse = self.get_cached_graph(reuse_variant=True)
```
2. 两个专用绑定方法烘焙常数（不用 lambda——cache_compile 需要模块方法/单次 trace）。compute 变体（diff 逐字）：
```
+        kwargs.pop("reuse_shared_topk", None)
+        kwargs.pop("shared_mtp_topk", None)
+        out = self.forward(
+            is_prefill=False,
+            reuse_shared_topk=False,
+            shared_mtp_topk=None,
+            **kwargs
+        )
```
reuse 变体只 pop `reuse_shared_topk` 并传 `reuse_shared_topk=True`，让 `shared_mtp_topk` 经 `**kwargs` 保持为固定 shape int32 图输入（图内永不为 None）。
3. `get_cached_graph(reuse_variant=None)` 路由 cache_model；cache_dir 以 `CASE_NAME` 为基加 `_compute` / `_reuse` 后缀，磁盘隔离且跨运行稳定。
4. `decode()` 在图外按 python bool 选图：`graph = self.cached_decode_reuse if kwargs.get("reuse_shared_topk", False) else self.cached_decode_compute`。

## 机制与判别

- 常数烘焙 vs guard：分支谓词是 python bool（非 tensor），dynamo 会把它 trace 成常数或 guard；拆成两个绑定方法后每张图内该值是烘焙常数（注释明确 "a baked-in python constant, NOT a trace-time guard"），选图逻辑在图外。
- 输入纪律：compute 图必须让 `shared_mtp_topk` 完全 absent（pop 掉、传 None），否则首 trace 会把缺省形态固化；reuse 图必须让它始终是固定 shape int32 输入。两图输入签名不同正是靠各自包装方法显式增删 kwargs 实现。
- 缓存目录：同一 `CASE_NAME` 派生 `_compute`/`_reuse` 两个 cache_dir；ge_graph offload GE-converter 懒加载块由类级 `_offload_ge_converter_done` 保证只注册一次（第一张图编译时），第二张跳过。
- 判别：非 MTP / `index_share_for_mtp_iteration=False` 走原单图分支（`self.cached_decode = self.get_cached_graph()`），行为不变。

## 验证信号

- 静态验证（本轨迹内实际完成）：`ast.parse` 两文件通过；`py_compile modeling_glm.py` 通过；git diff +84/-3 全部限于 cache_compile 块；grep 核对引用一致性（cached_decode_compute/reuse、main_decode_mtp_compute/reuse、decode 分派）。等级：静态检查。
- **运行级验证缺口**：板上 ge_graph/npugraph_ex 运行验证由用户执行（任务明确禁止本 agent 跑模型，shell 无 NPU），本轨迹内未出现运行结果；eager A′ 的 byte 验证是既有前置工作，不覆盖双静态图路径。

## 适用与失效边界

- 适用：cache_compile/npugraph_ex 静态图 + 逐步翻转 python bool 门控的任何特性开关（MTP IndexShare、scheme 选通等）；需要两张图输入签名不同（有的输入只在某一分支存在）的场景。
- 失效/风险：双图使编译时间与 cache 目录翻倍；bool 若来自 tensor `.item()` 则不能在图外判（会引入同步）；本实现未经运行验证，采前必须板上跑 MTP next_n=0..3 输出一致性回归；torchair/torch_npu 版本变化可能改变 guard 行为。

## 附：断言存档

- cache_compile 要求同一缓存函数只触发一次 Dynamo trace；逐步翻转的 python bool（reuse_shared_topk）留在被 trace 函数内会冻结首次分支或触发 guard 重编译。E8 双图方案：两个专用绑定方法烘焙常数——main_decode_mtp_compute pop 掉 reuse_shared_topk/shared_mtp_topk 并传 reuse_shared_topk=False, shared_mtp_topk=None（该图内张量 absent）；main_decode_mtp_reuse 只 pop reuse_shared_topk 并传 True，shared_mtp_topk 经 **kwargs 保持固定 shape int32 图输入——decode() 在图外按 python bool 选图。
- cache_dir 以稳定 CASE_NAME 为基加 _compute/_reuse 后缀隔离两张静态图；非 MTP 或 index_share_for_mtp_iteration=False 路径保持原单图（self.cached_decode = self.get_cached_graph()）行为不变——全部改动限于 modeling_glm.py cache_compile 块（+84/-3）；ge_graph offload GE-converter 懒加载由类级 _offload_ge_converter_done 保证只注册一次。
