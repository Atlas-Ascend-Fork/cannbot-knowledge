---
{
  "type": "Runbook",
  "title": "GLM-5.2 DSA offload DsaInstall AscendC 算子 decode 阶段 MTE 越界崩溃（与 GE ref-mapping / MTP 无关）",
  "description": "模型/框架：GLM-5.2（W8A8C16 量化，11 层裁剪权重复现环境），cann-recipes-infer + duyubo 提供的全新 DSA offload 算子组（dsa_plan / dsa_serve / dsa_install，AscendC 自定义算子）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# GLM-5.2 DSA offload DsaInstall AscendC 算子 decode 阶段 MTE 越界崩溃（与 GE ref-mapping / MTP 无关）

## 适用场景

- 平台范围依据：source 0 seq 1、source 0 seq 500的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/框架：GLM-5.2（W8A8C16 量化，11 层裁剪权重复现环境），cann-recipes-infer + duyubo 提供的全新 DSA offload 算子组（dsa_plan / dsa_serve / dsa_install，AscendC 自定义算子）。
- 硬件/环境：A3 dies 0—7（world_size=8），ge_graph 图模式，offload + DSA 共享池路由；CANN cann-9.1.0-beta.1。
- 目标：按 runbook 构建并验证 DSA offload 算子组接入，消除 MlaProlog in-place staging 快照。

## 触发与观测

- run7（GE patch 开、next_n=3）：decode 阶段崩溃，rank0 device plog 逐字记录：
  "[ERROR] RUNTIME(455409,python3):…[device_error_core_proc.cc:657]…there is an exception of aivec error, core id is 43, error code = 0x800000, … mte error info: 0x120302caed …"
  "The extend info: errcode:(0x800000, 0x4000, 0) errorStr: The DDR address of the MTE instruction is out of range.CCU instruction address check error."
  "[ERROR] GE(455409,python3):…ErrorTrackingCallback: ErrorNo: 4294967295(failed)Error happened, origin_op_name [DsaInstall_6], op_name [DsaInstall_6], task_id 20, stream_id 294."（source 0 seq 520）
- run8（GE patch 开、next_n=0）：主模型 decode warmup 后 synchronize 崩溃，rank0 507057 SUSPECT REMOTE ERROR（真错在对端 rank，详细 dump 进 device plog）→ 崩溃非 MTP 专属（source 0 seq 523 progress 记录）。
- run9（GE patch revert、next_n=0）：同样 507057 模式崩溃，0 成功；device plog(544596) 确认 origin_op_name [DsaInstall_3] + 同样的 "DDR address of the MTE instruction is out of range"（source 0 seq 571/579）。

## 探针与操作

- 静态核对算子原型（决定性排除）：DsaInstall inputs `[0:install_records, 1:selection_kv_cache, 2:selection_k_rope, 3:selection_kv_block_table, 4:pool_kv_cache, 5:pool_k_rope, 6:pool_ids, 7:id_to_slot, 8:lru_counter]`，outputs `[0:pool_kv_cache, 1:pool_k_rope, 2:pool_ids, 3:id_to_slot, 4:lru_counter]`；GE patch 映射 out0→in4, 1→5, 2→6, 3→7, 4→8，即每个 output 别名同名 pool input——语义正确。DsaServe outputs（selection_kv_cache, selection_k_rope）→ inputs 5,6 同名——正确（source 0 seq 514/516/523）。
- A/B 诊断：`patch_ge_graph_pass_dsa_ref_mapping.py --revert` 后重跑 next_n=0（run9），再重新 apply 恢复 runbook 状态（sha 745ea84…→a0974ae…→745ea84…）（source 0 seq 525/572/573）。
- plog 提取命令（复用）：`grep -aE "DsaInstall|out of range|MTE|aivec|0x800000" $PLOG | head -25`；跨 rank 扫 `EZ9999|EE9999|aivec|DsaInstall|507011`。

## 机制与判别

- 结论：DsaInstall AscendC kernel 在 decode 阶段做设备侧越界访问（MTE DDR address out of range，aivec 0x800000），是算子作者的 kernel bug；与 GE ref-mapping（静态验证正确）和 MTP 无关——四种组合（patch on/off × next_n 3/0）全部复现（source 0 seq 571/579/611）。
- 集成层已验证至 decode 前：vendor build/install（DSA + GatherSelection 共存）、torch.ops.custom.dsa_*、GE ref-mapping、模型加载、ge_graph 编译、prefill + warmup decode、入图 DSA 路由生效（非 legacy gather fallback）（source 0 seq 611）。
- 未验证推断：越界是否由 output==input in-place 别名触发（A/B 已排除 GE patch 层面的映射错误，但 kernel 内部对 in-place 的处理未审计）。
- 附带真修复（回退时被撤掉）："custom_op_loader.py 的双重 TORCH_LIBRARY 守卫是真 bug 修复，未来重跑需重新应用（candidate 的 offload_backend 选路未抑制 legacy gather 加载器）"（source 0 seq 611）。

## 验证信号

- tool_observed（NPU 设备日志，三次独立运行）：run7 DsaInstall_6、run9 DsaInstall_3 均 MTE 越界；run8 507057 对端错误；八 rank 全部 0 成功、无 token 输出。
- source_observed（静态）：两个算子 def 的输入/输出与 GE patch 映射一致。
- 用户侧停止：retry-cap governance 触发阶段回退，阻塞点上报主流程（source 0 seq 611）。

## 适用与失效边界

- 适用于：GLM-5.2 + duyubo DSA offload 算子组在 ge_graph/decode 的接入排查；出现 507011/EZ9999 + "DDR address of the MTE instruction is out of range" + origin_op_name [DsaInstall_N] 时优先判 kernel 越界，不要先怀疑集成层。
- 失效边界：本环境为 11 层裁剪权重复现；真实权重/其他 quant 配置未测。507057 SUSPECT REMOTE 只是对端症状，须查对端 rank plog。
- 停止/回退条件：需算子作者修复 kernel 越界后再验证；重跑前须重新应用 custom_op_loader.py 双重 TORCH_LIBRARY 守卫（source 0 seq 611）。

## 附：断言存档

- GLM-5.2 DSA offload 的 DsaInstall AscendC 算子在 decode 阶段做设备侧越界访问：device plog 记录 aivec error 0x800000、"The DDR address of the MTE instruction is out of range"、origin_op_name [DsaInstall_6]（run7）。
- A/B 判别：GE ref-mapping patch 静态验证正确（每个 output 别名同名 pool input；DsaServe out0→in5/1→in6）；revert patch 后（run9）仍崩且 plog 确认 DsaInstall_3 同样 MTE 越界；next_n=0（run8）也崩——崩溃与 GE patch 和 MTP 均无关，为算子作者 kernel bug。

```text
[ERROR] GE(455409,python3):2026-07-02-15:24:26.663.264 [error_tracking.cc:177]456133 ErrorTrackingCallback: ErrorNo: 4294967295(failed)Error happened, origin_op_name [DsaInstall_6], op_name [DsaInstall_6], task_id 20, stream_id 294.
```

```text
Decisive static check: DsaInstall's op prototype has inputs `[0:install_records, 1:selection_kv_cache, 2:selection_k_rope, 3:selection_kv_block_table, 4:pool_kv_cache, 5:pool_k_rope, 6:pool_ids, 7:id_to_slot, 8:lru_counter]` and outputs `[0:pool_kv_cache, 1:pool_k_rope, 2:pool_ids, 3:id_to_slot, 4:lru_counter]`. The GE patch maps output 0→4, 1→5, 2→6, 3→7, 4→8 — i.e., **each output aliases the identically-named pool input. The ref-mapping is semantically correct.**
```

```text
Conclusive: run9 (no patch, next_n=0) faulted on **DsaInstall_3** with the same "DDR address of the MTE instruction is out of range" as run7's DsaInstall_6 (with patch, next_n=3). The DsaInstall MTE out-of-range reproduces across all combinations (patch on/off, MTP on/off).
```
