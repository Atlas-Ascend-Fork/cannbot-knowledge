---
type: Optimization
title: 昇腾部署镜像的组件版本对齐（torch_npu / 驱动 HDK / CANN 包）与过渡态规避
description: 昇腾部署镜像的组件版本对齐（torch_npu / 驱动 HDK / CANN 包）与过渡态规避。cann-recipes-infer 的昇腾部署镜像把 torch_npu、驱动/HDK、CANN 包的版本成套 pin 死。不要把其中任一组件当作可自由升级的旋钮：单独换一个而与镜像不匹配，会在 bringup 期直接失败。做部署/调优时，先把组件版本对齐到目标 recipe/镜像 pin 的版本，再动优化。下面是三条已踩过的对齐关系与过渡态规避。
tags:
- task.optimization
- topic.model_architecture
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/24
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/140
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/101
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/249
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/169
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/65
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# 昇腾部署镜像的组件版本对齐（torch_npu / 驱动 HDK / CANN 包）与过渡态规避

## 条件 → 优先尝试什么

cann-recipes-infer 的昇腾部署镜像把 torch_npu、驱动/HDK、CANN 包的版本**成套 pin 死**。不要把其中任一组件当作可自由升级的旋钮：单独换一个而与镜像不匹配，会在 bringup 期直接失败。做部署/调优时，先把组件版本对齐到目标 recipe/镜像 pin 的版本，再动优化。下面是三条已踩过的对齐关系与过渡态规避。

## 规则一：torch_npu 主次版本 = 镜像内嵌 PyTorch 版本

镜像名内嵌 `cannX.Y_ptA.B.C_..._aarch_image` 形式的版本标签，`ptA.B.C` 是随附的 PyTorch 基线。

- **torch_npu 的主次版本须等于镜像 `ptA.B.C` 的 `A.B`**：torch_npu 2.5.x 对 PyTorch 2.5.x、2.6.x 对 2.6.x。读镜像名的 `ptX.Y.Z` 即知该装哪版 torch_npu。
- 反例：PyTorch 2.5.1 基线镜像上想单独把 torch_npu 换成 2.6.0 → 踩版本不匹配（维护者确认不能改用 2.6.0）。要用更高 torch_npu，须整体换到内嵌对应 `ptX.Y.Z` 的镜像，而非在原镜像里单换 torch_npu。
- 该规则绑定"镜像内嵌 PyTorch 版本"这条对齐关系，随镜像基线演进而移动，不是对某一 torch_npu 版本的绝对禁用。

## 规则二：算子已上 PTA 但镜像 CANN 包过旧 → 用自定义算子 run 包过渡

某前置融合算子（本例 [npu_mla_prolog_v3](../../../concepts/kernels/mla_prolog.md)）虽已进入 PTA/torch_npu 内置，但线上部署镜像的 CANN 包版本落后于内置该算子的版本（本例镜像 CANN 包为 9/30 版本，早于内置 `npu_mla_prolog_v3` 的版本）。

- **不要阻塞等镜像升级 CANN 包**：编译该融合算子生成**自定义算子 run 包** → 打进镜像的"自定义算子 run 包路径" → 建模代码统一经 `torch.ops.custom.<op>` 调用它（本例 `torch.ops.custom.npu_mla_prolog_v3`）。
- 这解释了 review 中常见的困惑："算子不是上 PTA 了吗，为何还用 custom？"——因为部署镜像的 CANN 包过旧、旧镜像上直接调内置版会缺算子。
- 证据覆盖 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md) / [kimi-k2-thinking](../../../concepts/models/kimi_k2_thinking.md) 同族建模路径（C8 伪量化的 MLA-prolog），机制对"PTA 已内置但部署镜像 CANN 包过旧"的任意融合算子过渡态可迁移。
- **边界 / rollback**：这是版本过渡态的规避、非永久设计。一旦部署镜像升级到已内置该算子的 CANN 版本，切回 torch_npu 内置算子即可。

## 规则三：驱动/HDK + CANN 包低于 PyPTO 要求 → PyPTO 算子加载崩，不是抢卡

[PyPTO](../../../concepts/frameworks/pypto.md) 融合算子 `SparseAttentionPto`（即 [DeepseekIndexerAttention](../../../concepts/kernels/deepseek_indexer_attention.md)，DeepSeek-V3.2-Exp 稀疏注意力算子）在 [TorchAir](../../../concepts/frameworks/torchair.md) 图模式加载时若容器内驱动/CANN 过旧，图 compile 成功、`LoadGraph` 阶段崩：

```
RuntimeError: E19999: Inner Error!
  Assert ((ArgsFormatUtils::GetTileFwkHiddenInputs(op_desc_, *davinci_model_, context_addrs)) == ge::SUCCESS) failed
  [Assemble][Addresses] failed, op = SparseAttentionPto.
  Load graph failed, error code:1343225857 ...
```

- **误判排除**：报错像 device 冲突（维护者与报告人最初都怀疑抢卡），但报告人实测"卡都没在用、换卡后仍报同一错"——排除 device 抢卡。
- **根因**：`SparseAttentionPto` 是 [DSA](../../../concepts/modules/dsa.md) 的 TileFwk 运行态算子，图加载时 GE 需向驱动/runtime 取该算子的"TileFwk 隐藏输入"（`GetTileFwkHiddenInputs`）来组装地址；驱动/CANN 未提供对应 TileFwk 运行态 ABI（版本过低）时组装即失败。PyPTO FAQ 同类问题的设备侧签名是 `DynTileFwkKernelServer... func is nullptr`。
- **修法**：把驱动与镜像对齐到 `ops/pypto/README.md` 指定版本。DSV3.2-Exp PyPTO 场景 pin：Atlas A3 系列 / 镜像 `cann8.3.rc1.alpha003_pt2.6.0_dsv3.2_pypto_aarch_image:v0.1` / 驱动 `Ascend HDK 25.2.0`（`npu-smi info` 须显示 25.2.0）。
- **注意版本随 PyPTO 前移**：DSV3.2-Exp 镜像期驱动下限 25.2.0、CANN 8.5.0；当前 pypto master 已要求 `Ascend HDK 25.5.0 及以上`（低于支持版本的 HDK 不在验证范围，运行异常算子可能致 NPU 状态异常、AIC 超时、需重启设备）。引用时以目标 recipe/镜像 pin 的版本为准。

## 规则四：算子可用性受 CANN 版本 + PTA(torch_npu) 构建双重独立门控——post 号高 ≠ 有算子

新近合入的算子能不能调到，取决于两道**相互独立**的门（本例 [Gated Delta Net](../../../concepts/kernels/recurrent_gated_delta_rule.md) 的 chunk 变体 `npu_chunk_gated_delta_rule`，[GDN](../../../concepts/modules/gated_deltanet.md) / 线性注意力）：

- **CANN 版本门**：`chunk_gated_delta_rule` 仅 CANN 9.1.0 支持（近期合入，9.0 / 8.5 不含）。算子由 CANN `ops-transformer` 仓 `attention/chunk_gated_delta_rule` 提供（同族另有 `recurrent` 变体；chunk 走 prefill 并行、recurrent 走 decode 增量，语义不同、不能互换顶替）。
- **PTA(torch_npu) 构建门**：PTA 各版本对新算子的 wire-up 节奏有别——即便 CANN 已装 9.1.0，`torch_npu 2.8.0.post4` 仍**不暴露**该算子，报 `AttributeError: module 'torch_npu' has no attribute 'npu_chunk_gated_delta_rule'. Did you mean: 'npu_recurrent_gated_delta_rule'?`；实测暴露它的是 torch 2.7.1 一支。

排查动作：① 确认 CANN ≥ 算子最低版本（不是「装了最新 CANN 就有」）；② 选**暴露该算子的 PTA 构建**、**不盲目上最高 `torch_npu.post` 号**（post 号高不代表 wire 了新算子）；③ 以算子所在 CANN 仓（`ops-transformer`）的提交 / README 作可用性与硬件支持面的权威，而非 recipe README；④ 「recurrent 变体在 ≠ chunk 变体在」——两算子各自独立随版本上线，别因同族的一个在就假设另一个在。这与规则二互补：规则二是「算子已上 PTA、但镜像 CANN 包过旧」，本规则是「CANN 够了、但 PTA 构建没 wire」。

## 规则五：PyPTO 算子编译期须在仓方镜像内——TileFwk 头/库不随普通 CANN toolkit 发布

[PyPTO](../../../concepts/frameworks/pypto.md) 融合算子（[LightningIndexer](../../../concepts/kernels/lightning_indexer.md) / [LightningIndexerProlog](../../../concepts/kernels/indexer_prolog.md) / [DeepseekIndexerAttention](../../../concepts/kernels/deepseek_indexer_attention.md)）的 kernel 直接写在 TileFwk 框架（`namespace npu::tile_fwk`）之上，编译期强依赖只随特定镜像发布的头/库。在**裸 CANN toolkit（含 nnal）**里 `bash ./build.sh` 会断在头文件缺失：

```
fatal error: tilefwk/tilefwk_op.h: No such file or directory
  （及 tilefwk/{tilefwk.h,tensor.h,symbolic_scalar.h,config.h}、register/op_ct_impl_registry.h）
```

- **根因**：`ops/pypto/CMakeLists.txt` 的 `tile_fwk_impl` 目标从 `${ASCEND_HOME_PATH}/include` 找 TileFwk 头、从 `${ASCEND_HOME_PATH}/lib64` 链接 `tile_fwk_interface` / `tile_fwk_operator`——普通 CANN toolkit / nnal 的 `ASCEND_HOME_PATH` 下没有这套 TileFwk 头与库。
- **修法**：pypto 当前**只支持在仓方钉定的 Docker 镜像内编译运行**（该镜像已把 TileFwk 装进 `ASCEND_HOME_PATH`），README 的编译全流程（`docker load` → `docker run` → 容器内 `source setenv.bash` → `bash ./build.sh`）都在容器内。不要在裸 toolkit（哪怕更新的 8.5.0）自建编译——pypto 的编译前置是「用这个特定镜像」而非「任意更新版本 toolkit」。
- 与规则三互补：规则三是 pypto 算子**运行 / 加载期**因驱动 / CANN 过旧取不到 TileFwk 运行态 ABI（E19999）；本规则是**编译期**因裸 toolkit 缺 TileFwk 头 / 库。两处都指向「pypto 紧耦合仓方镜像里的 TileFwk」。

## 规则六：torch 2.5.1+ 在 NPU 环境自动导入 torch_npu——跑纯 torch 脚本前须先 source CANN 环境

即使脚本只 `import torch`、逻辑只做 CPU 侧处理（如权重转换），在 NPU 环境下 torch **2.5.1 及以后**会自动把 torch_npu 一并导入；torch_npu 的导入依赖 CANN 运行环境，**运行前未 `source` CANN/NPU 环境变量则导入失败、脚本起不来**（脚本不显式 `import torch_npu` 也绕不过这次自动导入）。修法：跑权重转换 / 任意 torch 脚本**前先 `source` CANN 环境变量**（set_env）。这是系于 torch/torch_npu 2.5.1+ 栈的持久前置步骤、非某版本一次性 bug。

## 相关经验
- [昇腾 bringup 初始化/HCCL 报错的根因常在环境/驱动/平台层，顶层 ACL/HC](../../../runbooks/runtime/bringup_error_root_cause_env_driver_platform.md)

## Evidence

- **规则一 · 维护者确认**：该镜像须用 torch_npu 2.5.1、不能改 2.6.0；"torch_npu 主次须匹配镜像 PyTorch"由该确认 + 镜像名 `ptX.Y.Z` 约定推出，范围限本仓部署镜像。
  - 溯源下探：[cann-recipes-infer-issue-24-question-torch-npu](https://gitcode.com/cann/cann-recipes-infer/issues/24)
- **规则二 · 代码事实**（clone `@7037e39a9d95`）：合并 diff 确认建模路径调用 `torch.ops.custom.npu_mla_prolog_v3`。**维护者确认**："为何用自定义算子 + 打进镜像自定义算子路径"来自 review 答复。
  - 溯源下探：[cann-recipes-infer-pr-140-refactor-delete-unused-key-states-parameter](https://gitcode.com/cann/cann-recipes-infer/merge_requests/140)
- **规则三 · 代码事实**（clone `cann-recipes-infer@e00ab79` / `pypto@c1344f41`）：`ops/pypto/README.md` 环境要求 + `pypto` `faq.md`「CANN包不兼容」/ `prepare_environment.md` 两处一手佐证"驱动/CANN 版本不足 → TileFwk 算子加载/组装失败"；宿主报错节点/TileFwk 符号/算子归属/版本要求四路互对。**报告人实测**：device 抢卡假设被报告人换卡复测反驳。细粒度 ABI 机制为据符号 + PyPTO 文档的推断。
  - 溯源下探：[cann-recipes-infer-issue-101-question](https://gitcode.com/cann/cann-recipes-infer/issues/101)
- **规则四 · 维护者确认 + 源码事实**（`ops-transformer@master`：`attention/chunk_gated_delta_rule` dir sha `b498ca2`、`recurrent_gated_delta_rule` dir sha `4bd9028` 两目录并存，chunk README 记 A3/A2 √、950/旧 Atlas ×、chunk=prefill 并行版、BF16/ND）：维护者确认「chunk 仅 CANN 9.1.0 支持、近期合入、见 ops-transformer 提交记录」；PTA「2.7.1 可用 / 2.8.0.post4 不暴露」为 issue 讨论 + PTA release note 披露、未独立复测。观测于 Qwen3.5 类 GDN / 线性注意力模型 bringup（`AttributeError` 逐字取自源）。
  - 溯源下探：[cann-recipes-infer-issue-249-question](https://gitcode.com/cann/cann-recipes-infer/issues/249)
- **规则五 · 代码事实 + 维护者确认**（clone `@239c0c1`）：pypto kernel/host 源码 `#include "tilefwk/*.h"` + proto `#include "register/op_ct_impl_registry.h"` 与报障堆栈行号一一对上；`ops/pypto/CMakeLists.txt` 的 `tile_fwk_impl` include `${ASCEND_HOME_PATH}/include`、link `tile_fwk_interface`/`tile_fwk_operator`；README 钉镜像 `cann8.3.rc1.alpha003_pt2.6.0_dsv3.2_pypto_aarch_image:v0.1` + 驱动 25.2.0 + Atlas A3。维护者确认「当前只支持通过镜像运行」。
  - 溯源下探：[cann-recipes-infer-issue-169-bug-report-cann-recipes-infer-ops-pypto](https://gitcode.com/cann/cann-recipes-infer/issues/169)
- **规则六 · 维护者确认**：转换脚本头注「`import torch_npu  # torch_npu 2.5.1 及以后版本可以不用`」；维护者确认 torch 2.5.1+ 在 NPU 环境自动导入 torch_npu、修法为转权重前先 source 环境变量（纯环境行为、无代码 diff）；torch 2.5 树外 backend autoload 机制为背景推断、不并入事实面。
  - 溯源下探：[cann-recipes-infer-issue-65-bug-report-torch-torch-npu-torch-npu-source](https://gitcode.com/cann/cann-recipes-infer/issues/65)

<!-- cannbot:related:start -->
## 相关

- [昇腾 bringup 初始化/HCCL 报错的根因常在环境/驱动/平台层，顶层 ACL/HCCL 码是泛化包装](../../../runbooks/runtime/bringup_error_root_cause_env_driver_platform.md)（`related`）：“先把组件版本对齐到目标 recipe/镜像 pin 的版本，再动优化”与“先怀疑环境/驱动/平台不匹配，别急着改模型或并行代码”共同给出从版本对齐到环境根因排查的 bringup 顺序。
- [自带（vendored）自定义算子与 CANN 库同名算子冲突：torch_npu.npu_* 解析走偏 / 接口漂移](../../../runbooks/runtime/vendored_custom_op_vs_cann_samename_op_conflict.md)（`related`）：“因为部署镜像的 CANN 包过旧、旧镜像上直接调内置版会缺算子”与“调用解析到了「错的那一份」”分别覆盖内置算子缺失和同名实现解析错误，属于升级镜像后的同一算子来源排查链。
- [量化权重格式 / dtype 组合的可用性受 SoC 平台与 CANN 算子包版本双重约束（非量化配置 bug）](../../../runbooks/precision/quant_format_dtype_platform_cann_version_gating.md)（`related`）：“CANN 算子包版本缺口 → 升版本”把一类 dtype 报错归因到版本；“不要把其中任一组件当作可自由升级的旋钮”要求升级时保持 torch_npu、驱动和 CANN 的镜像配套。
<!-- cannbot:related:end -->
