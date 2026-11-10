---
type: Runbook
title: "vllm-ascend PR #14374（Omni-EPLB）eplb_warmup 末尾无条件调用 reset_log2phy：非 omni 动态 EPLB 预期 AttributeError 的静态源码诊断"
description: "vllm-ascend 集成上游 PR #14374（Support Omni-EPLB，观察时 open 未合并）后，NPUModelRunner.eplb_warmup() 末尾新增无条件 self.eplb_updator.reset_log2phy()，而该方法仅定义于 OmniEplbUpdator 子类（omni_eplb_updator.py:33），基类 EplbUpdator 未定义且 PR 对 eplb_updator.py 仅新增空行；eplb_updator 实例类型由 enable_omni_eplb 在初始化时二选一，因此 dynamic_eplb=True 且 enable_omni_eplb=False 的非 omni 动态 EPLB 首次 warmup 预期抛 AttributeError。证据为 Windows 开发机上的 git grep/diff/show 与文件读取静态观测（源码级 tool_observed），未在 torch/NPU 环境运行时复现；本轨迹按忠实移植原则保留该上游缺陷原样并推送。"
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
status: draft
sources: []
created_at: '2026-10-29T16:39:00Z'
updated_at: "2026-11-04T09:23:45Z"
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
      model_features:
        all_of: [moe]
---

# vllm-ascend PR #14374（Omni-EPLB）eplb_warmup 末尾无条件调用 reset_log2phy：非 omni 动态 EPLB 预期 AttributeError 的静态源码诊断

## 适用场景

- 适用框架与代码线：vllm-ascend（vLLM 的昇腾 NPU 硬件插件，v1 worker 代码线）集成上游 vllm-project/vllm-ascend PR #14374 "Support Omni-EPLB"（CConory fork 的 eplb 分支，7 提交、13 文件 +156/-31，base rfc/vllm_cann；本轨迹观察时状态 open、未合并）或其等价改动。
- 涉及组件：EPLB（MoE 专家并行负载均衡）warmup 路径 vllm_ascend/worker/model_runner_v1.py 的 NPUModelRunner.eplb_warmup、EPLB updator 类族 vllm_ascend/eplb/eplb_updator.py 与新增文件 vllm_ascend/eplb/omni_eplb_updator.py，以及 EplbConfig 配置。
- PR #14374 为 EplbConfig 新增 enable_omni_eplb、omni_config_file、convert_weight_to_list 三个配置项。

```text
+        "enable_omni_eplb": False,
+        "omni_config_file": None,
+        "convert_weight_to_list": False
```

- 本轨迹证据等级：Windows 开发机上的静态源码观测（git grep/git diff/git show 与文件读取；Python 3.14.7，无 torch，无 NPU 参与运行）；硬件型号未知，未运行时复现。保持 draft、平台未知。

## 触发与观测

- 触发条件（预期）：引入 PR #14374 改动后，配置 dynamic_eplb=True 且 enable_omni_eplb=False（非 omni 的动态 EPLB），服务启动首次进入 EPLB warmup，执行到 eplb_warmup() 末尾的 self.eplb_updator.reset_log2phy()。
- PR #14374 在 vllm_ascend/worker/model_runner_v1.py 的 eplb_warmup() 末尾、enable_omni_eplb 分支之外、dynamic_eplb 守卫之内新增无条件调用 self.eplb_updator.reset_log2phy()。
- 本轨迹实际观测到的是源码静态事实（未运行到该代码路径）：cherry-pick 落地后在目标分支执行 git grep，得到定义与调用位置（原文行摘录）：

```text
HEAD:vllm_ascend/eplb/omni_eplb_updator.py:33:    def reset_log2phy(self):
HEAD:vllm_ascend/worker/model_runner_v1.py:3815:            self.eplb_updator.reset_log2phy()
HEAD:vllm_ascend/eplb/omni_eplb_updator.py:10:class OmniEplbUpdator(EplbUpdator):
```

## 探针与操作

在含 PR #14374 改动的工作区执行以下探针（本轨迹实际执行的命令原文）：

```text
git grep -n "def reset_log2phy" HEAD -- vllm_ascend/
git grep -n "reset_log2phy" HEAD -- vllm_ascend/worker/
```

再读取 model_runner_v1.py 的 eplb_warmup 上下文核对调用位置（工具行号原样保留）：

```text
3812:                 except Exception as e:
3813:                     logger.error("[eplb/omni] OmniPlanner stage 2 failed: %s", e)
3814:                     raise
3815:             self.eplb_updator.reset_log2phy()
3816:
3817:     def update_eplb_heat_collection_status(self, num_tokens_padded: int):
```

对照 PR 净 diff（3da28f94..pr-14374）中该调用的引入位置：

```diff
@@ -3738,10 +3747,28 @@ class NPUModelRunner(GPUModelRunner):
         if self.dynamic_eplb and not self.is_eplb_warmuped:
             self.is_eplb_warmuped = True
             self.eplb_adaptor = VllmEplbAdaptor(model=self.model)
-            self.eplb_loader.set_adator(self.eplb_adaptor)
+            if self.eplb_loader is not None:
+                self.eplb_loader.set_adator(self.eplb_adaptor)
             self.eplb_updator.set_adaptor(self.eplb_adaptor)
             self.eplb_updator.warm_up_eplb()

+            # Trigger OmniPlanner stage 2 when num_moe_layers is now known
+            eplb_config = self.ascend_config.eplb_config
+            if eplb_config.enable_omni_eplb:
+                try:
+                    from omni_placement.omni_planner import OmniPlanner
+                    from vllm_ascend.eplb.adaptor.vllm_adaptor import VllmEplbAdaptor as _VllmEplbAdaptor
+                    num_moe_layers = len(_VllmEplbAdaptor._registered_moe_layers)
+                    omni_planner = OmniPlanner()  # get singleton
+                    omni_planner.init_dynamic_components(num_moe_layers)
+                    omni_planner.init_dram_weights(self.eplb_adaptor.param_dict, 0, param_dict_type="vllm_ascend")
+                    omni_planner.start_dynamic_optimize_expert_load_balance()
+                    logger.info("[eplb/omni] OmniPlanner stage 2 initialized, num_moe_layers=%s", num_moe_layers)
+                except Exception as e:
+                    logger.error("[eplb/omni] OmniPlanner stage 2 failed: %s", e)
+                    raise
+            self.eplb_updator.reset_log2phy()
+
     def update_eplb_heat_collection_status(self, num_tokens_padded: int):
```

## 机制与判别

- reset_log2phy 仅定义于 OmniEplbUpdator 子类（omni_eplb_updator.py:33；类声明 class OmniEplbUpdator(EplbUpdator) 位于同文件第 10 行）；基类 EplbUpdator 未定义该方法，PR 对 eplb_updator.py 的唯一改动是新增一个空行。子类中的定义（git show 原文）：

```text
    def reset_log2phy(self):
        for local_idx, layer in enumerate(self.adaptor.moe_layers):
            layer.log2phy = OmniPlanner().get_log2phy(local_idx)
        logger.info("[eplb/omni] OmniEplbUpdator re-register log2phy completed, rank=%s", self.rank_id)
```

- 基类文件在 PR 中的完整改动（git diff 原文，仅一个空行）：

```diff
diff --git a/vllm_ascend/eplb/eplb_updator.py b/vllm_ascend/eplb/eplb_updator.py
index a9a8da60..851bc624 100644
--- a/vllm_ascend/eplb/eplb_updator.py
+++ b/vllm_ascend/eplb/eplb_updator.py
@@ -76,6 +76,7 @@ class EplbUpdator:

         logger.info("[eplb/updator] Launched EPLB subprocess, pid=%s", self.process.pid)

+
     def update_iteration(self):
         self.cur_iterations += 1
         if self.cur_iterations == (
```

- eplb_updator 的实例类型由 enable_omni_eplb 决定：True 时为 OmniEplbUpdator，False 时为基类 EplbUpdator；因此 dynamic_eplb=True 且 enable_omni_eplb=False 的非 omni 动态 EPLB 首次执行 eplb_warmup 时，将对该基类实例调用仅子类定义的 reset_log2phy，预期抛出 AttributeError——此为静态源码推断，本轨迹未在 torch/NPU 环境运行时复现。初始化分支（PR 净 diff）：

```diff
@@ -505,21 +505,30 @@ class NPUModelRunner(GPUModelRunner):

         eplb_config = self.ascend_config.eplb_config
         self.dynamic_eplb = eplb_config.dynamic_eplb
-        self.eplb_enable = self.dynamic_eplb or (eplb_config.expert_map_path is not None)
+        self.eplb_enable = self.dynamic_eplb or (eplb_config.expert_map_path is not None) or eplb_config.enable_omni_eplb
         if self.dynamic_eplb:
             self.is_eplb_warmuped = False
             self.policy_type = eplb_config.eplb_policy_type
-            self.eplb_loader = D2DExpertWeightLoader()
-            self.manager = Manager()
-            self.shared_dict = self.manager.dict({"expert_map": None, "moe_load": None, "expert_maps": None})
-            self.eplb_process = EplbProcess(
-                shared_dict=self.shared_dict,
-                policy_type=self.policy_type,
-                enable_d2d=True,
-                tp_size=self.parallel_config.tensor_parallel_size,
-            )
-            self.process = self.eplb_process._launch_process()
-            self.eplb_updator = EplbUpdator(eplb_config, self.eplb_loader, self.eplb_process, self.process)
+            if eplb_config.enable_omni_eplb:
+                self.eplb_loader = None
+                self.manager = None
+                self.shared_dict = None
+                self.eplb_process = None
+                self.process = None
+                from vllm_ascend.eplb.omni_eplb_updator import OmniEplbUpdator
+                self.eplb_updator = OmniEplbUpdator(eplb_config)
+            else:
+                self.eplb_loader = D2DExpertWeightLoader()
+                self.manager = Manager()
+                self.shared_dict = self.manager.dict({"expert_map": None, "moe_load": None, "expert_maps": None})
+                self.eplb_process = EplbProcess(
+                    shared_dict=self.shared_dict,
+                    policy_type=self.policy_type,
+                    enable_d2d=True,
+                    tp_size=self.parallel_config.tensor_parallel_size,
+                )
+                self.process = self.eplb_process._launch_process()
+                self.eplb_updator = EplbUpdator(eplb_config, self.eplb_loader, self.eplb_process, self.process)
```

- 可区分分支：enable_omni_eplb=True 时 eplb_updator 为 OmniEplbUpdator，reset_log2phy 存在，不触发；dynamic_eplb=False（含仅配置静态 expert_map_path 的 EPLB）时 eplb_warmup 的 dynamic_eplb 守卫短路，不会执行到该调用；仅 dynamic_eplb=True 且 enable_omni_eplb=False 组合预期触发 AttributeError。
- 该调用为 PR 上游原始缺陷：PR 净 diff（3da28f94..pr-14374）原样包含该行，本轨迹的 cherry-pick 未改写该区域，按忠实移植原则保留原样；omni_eplb_updator.py 顶层导入的 omni_placement 为外部依赖，model_runner_v1.py 中的 OmniPlanner 导入位于 enable_omni_eplb 分支内（惰性），不影响非 omni 路径的导入链。

## 验证信号

以下均为本轨迹内真实观测到的信号（平台：Windows 静态源码分析，无 torch/NPU；证据等级：tool_observed、源码级；单条轨迹单次观测）：

- git grep 返回 reset_log2phy 定义唯一位于 HEAD:vllm_ascend/eplb/omni_eplb_updator.py:33，调用唯一位于 HEAD:vllm_ascend/worker/model_runner_v1.py:3815，OmniEplbUpdator(EplbUpdator) 类声明位于同文件第 10 行。
- 文件读取返回 eplb_warmup 实际代码：reset_log2phy() 位于 3815 行、enable_omni_eplb try/except 块（3802-3814 行）之外、dynamic_eplb 守卫之内。
- git show 返回 omni_eplb_updator.py 全文（reset_log2phy 定义）与 eplb_updator.py 的净 diff（仅新增空行）。
- 未观测到的信号（如实声明）：AttributeError 的运行时堆栈、NPU 设备侧行为——本轨迹无 torch/NPU，无法产生；上述触发判定为静态推断。

## 适用与失效边界

- 语义边界：仅针对含 PR #14374 改动（或其等价移植）的 vllm-ascend 代码线；上游若已修复（把调用移入 omni 分支、给基类补 no-op、或加守卫）则本页失效，采用前应先核对上游最新状态（本轨迹观察时 PR 尚未合并）。
- 配置边界：触发组合收敛为 dynamic_eplb=True 且 enable_omni_eplb=False；静态 EPLB（dynamic_eplb=False）与 enable_omni_eplb=True 路径不受此缺陷影响。
- 证据边界：全部为静态源码证据，AttributeError 为预期推断而非运行时观测；在 torch/NPU 环境实际运行复现前，不能宣称"已复现"，verified 保持空。
- 平台边界：本轨迹在 Windows 开发机完成，未涉任何 NPU 硬件；芯片型号未知，不推断平台适用性。
- 处置建议（未执行，属后续工作）：若需在非 omni 动态 EPLB 下使用该代码线，应在 eplb_warmup 中为 reset_log2phy 调用增加 enable_omni_eplb 守卫（或等价修复），并回归 dynamic_eplb=True 且 enable_omni_eplb=False 的启动链路。
