---
type: Runbook
title: 昇腾多模态模型 bringup 的结构失配：框架侧 config 扫描盲区与 OOT 算子秩契约违背
description: >-
  vLLM-Ascend 多模态模型 bringup 有两类共性结构失配。一是 MoE 判定只扫描 hf_config
  顶层，会漏掉 text_config 中的 num_experts，导致 moe_comm_method 未初始化并在 FusedMoE
  调用 prepare 时崩溃；应在模型加载前递归扫描嵌套配置中的 expert 键。二是替换上游
  MMEncoderAttention 的 OOT 算子无条件返回四维 b,s,h,d，而三维 query 的调用方期望
  b,s,(h*d)，最终使 aclnnAddmm 报参数错误；应根据输入秩折叠输出。通用边界是：模型属性判定
  必须穿透嵌套配置，OOT 替换必须保持原算子的输入输出秩和布局契约。
tags:
- task.debugging
- topic.attention
- topic.mixture_of_experts
- topic.graph_execution
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/3897
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/issues/5297
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 昇腾多模态模型 bringup 的结构失配：框架侧 config 扫描盲区与 OOT 算子秩契约违背

## 适用场景

在昇腾 NPU 上用 vLLM-Ascend（vLLM 昇腾后端）起**多模态模型**（VL / Omni / 视觉编码器类）时，会撞上两类**结构失配**——框架/算子按纯文本或某个固定张量布局的假设写死，遇到多模态模型的**嵌套 config 结构**或**非固定秩的调用形状**就失配崩溃。它们各自独立、症状不同，但都属于同一类根因：**通用框架/OOT 算子对结构做了过强假设，多模态模型的结构与该假设不符**。本页汇两个具体失败签名，起同类多模态模型时逐一核对：

1. **config 结构盲区**：框架用「扫 hf_config 找某类键」来判定模型属性（如是否 MoE），但只扫**顶层**；多模态模型把语言塔配置塞进 `text_config` 子字典，标记键在嵌套层，被漏检 → 该模型的 NPU 侧优化路径（MoE 通信方法）从未初始化 → 后续崩 `AttributeError`。
2. **OOT 算子秩契约违背**：昇腾 out-of-tree（OOT）自定义算子替换上游算子后，无条件把输出 rearrange 成固定秩（4D）；当上游视觉编码器以另一种秩（3D）调用时，输出秩/布局与下游线性层期望不符 → 下游 `o_proj` 落到 CANN `aclnnAddmm` 报参数错误。

两类症状（`AttributeError: 'NoneType'` 于 FusedMoE、`aclnnAddmm error code 161002`）见下各自子节。

## 信号 1：MoE 判定只扫顶层 config，嵌套 `text_config` 的 MoE 键被漏检

**信号（现象）**：起 VL / Omni 型多模态 MoE 模型（观测实例 Qwen3-VL-30B-A3B-Instruct、Qwen3-Omni-30B-A3B）时，在 `_dummy_run` → `profile_run`（KV cache 预探测）阶段就崩，栈落在 FusedMoE：

```
File "vllm_ascend/ops/fused_moe/fused_moe.py", line 335, in forward_impl
  hidden_states, router_logits, mc2_mask, context_metadata = forward_context.moe_comm_method.prepare(
AttributeError: 'NoneType' object has no attribute 'prepare'
```

典型启动命令（触发处境）：`vllm serve Qwen3-VL-30B-A3B-Instruct --tensor-parallel-size 4 --enable-expert-parallel --enforce-eager`（TP=4 + EP，昇腾）。

**触发条件**：多模态 MoE 模型的 hf_config 把语言塔配置放进 `text_config` 子字典，MoE 相关键（`num_experts` 等）**不在顶层**；而纯文本 MoE（如 Qwen3-30B-A3B）的这些键在顶层。框架据顶层扫描判 MoE，于是多模态 MoE 被误判为非 MoE。

**根因**：`moe_comm_method` 为 `None`，是因为模型被判为非 MoE、NPU 侧 MoE 通信方法从未建立，后续 FusedMoE 层拿到 `None`。旧的判定只遍历 config 的顶层键：

```python
config = vllm_config.model_config.hf_config
_IS_MOE_MODEL = any('experts' in key.lower() for key in config.to_dict())
```

`config.to_dict()` 只列**顶层**键，VL/Omni 模型顶层没有 `experts` 类键（它们在 `text_config` 里）。**关键约束**（属耐久设计事实）：MoE 判定在**模型加载之前**就被调用（例如 platform 初始化更新 ACLGraph 配置阶段），因此**不能**靠「模型里是否含 `FusedMoE` 模块」来判 MoE，只能从 config dict 判——这决定了修法必须仍走 config、只是要能穿透嵌套。

**修法**：把顶层扫描换成**递归遍历嵌套 config dict**，任意层键名含子串 `"expert"` 即判为 MoE：

```python
def is_moe_model(vllm_config: VllmConfig):
    global _IS_MOE_MODEL
    if _IS_MOE_MODEL is None:
        model_configs = vllm_config.model_config.hf_config.to_dict()
        _IS_MOE_MODEL = _is_contain_expert(model_configs)
    return _IS_MOE_MODEL

def _is_contain_expert(config: Any):
    if isinstance(config, dict):
        for k, v in config.items():
            if "expert" in str(k):
                return True
            if _is_contain_expert(v):
                return True
    return False
```

设计权衡（可迁移）：**不精确匹配 `num_experts` 键**——并非所有 MoE 模型都用该键名，也可能是 `xxx_expert_xxx`，故用子串 `"expert"` 递归匹配以覆盖不同命名；也**不按模型架构名（VL/Omni）走特定分支**，而是不看架构、纯递归找嵌套 expert 键，这样对未来新增的嵌套-config 多模态 MoE 也成立。

## 信号 2：OOT 编码器注意力算子未保持输出与输入同秩，下游 `o_proj` 报 `aclnnAddmm 161002`

**信号（现象）**：起多模态视觉编码器（观测实例 Tencent-Hunyuan/HunyuanOCR，e2e 用例 `pytest -sv tests/e2e/singlecard/test_vlm.py::test_multimodal_vl[hunyuan-vl]`）时，在 `profile_run` 的 `embed_multimodal` 阶段（KV cache 预探测）崩，栈落在视觉编码器 self-attn 之后的 `o_proj`：

```
hunyuan_vision.py:250  output, _ = self.o_proj(out)
  -> vllm/model_executor/layers/linear.py:1406 forward -> quant_method.apply
  -> layers/linear.py:240 dispatch_unquantized_gemm -> default_unquantized_gemm
  -> layers/utils.py:106 torch.nn.functional.linear(x, weight, bias)
RuntimeError: addmm: NPU function error: call aclnnAddmm failed, error code is 161002
[ERROR] ... ERR00100 PTA call acl api failed.  AclNN_Parameter_Err
```

**触发条件**：视觉编码器的 attention 由昇腾 OOT 算子承担——`AscendMMEncoderAttention` 经 `CustomOp.register_oot(name="MMEncoderAttention")` 注册，替换 vLLM 上游 `vllm.attention.layers.mm_encoder_attention.MMEncoderAttention`（故 traceback 全在 vllm 侧 `hunyuan_vision.py`，实际执行的是昇腾 OOT 算子）；而该编码器以 **3D（非 4D）query** 调用该 attention。

**根因**：OOT 算子内部一律先把 q/k/v 折叠成 3D `(b*s, head, head_dim)` 交给 `torch_npu._npu_flash_attention_unpad` 计算，输出 `context_layer` 也是折叠布局；但收尾**只有一条** `-> b s h d` 路径，无条件返回固定 **4D**。HunyuanOCR 视觉编码器以 3D 调用，其后的 `o_proj`（RowParallelLinear）weight 是按合并隐藏维 `(h*d)` 组织的 `b s (h d)`；收到 4D 输出后 `aclnnAddmm` 形状对不上，报 `161002 / AclNN_Parameter_Err`——**是上游 attention 算子返回秩不对，不是 `o_proj` 自身的错**。

**修法**：让算子**保持输出与输入同秩/同布局**。入口记住输入是否为 4D，收尾按秩分支折叠：

```python
is_reshaped = query.dim() == 4
...
if is_reshaped:                       # 输入本就是 4D [b, s, h, d]
    context_layer = einops.rearrange(context_layer,
                                     "(b s) h d -> b s h d", b=bsz).contiguous()
else:                                 # 输入是 3D（rank-collapsed）
    context_layer = einops.rearrange(context_layer,
                                     "(b s) h d -> b s (h d)", b=bsz).contiguous()
```

可迁移的核心事实：**OOT 自定义算子替换上游算子时，其输出必须保持调用方传入的张量秩/布局**（输入 4D 则输出 4D，输入 3D 则把最后两维折叠回 `(h d)`），否则下游线性层（RowParallelLinear → `aclnnAddmm`）报 161002 参数错误。任何以 3D query 调用昇腾编码器 attention OOT 算子的视觉编码器 bring-up 都可能对号入座。

## 通用启示

这两个签名共享一条可迁移的 bring-up 纪律：**通用框架/OOT 算子对多模态模型的结构（config 布局、张量秩）不要写死单一假设**——

- 判模型属性时**递归穿透嵌套 config**，别只扫顶层，也别绑架构名；
- OOT 算子替换上游算子时**保持输出与调用方输入同秩/同布局**，别无条件 rearrange 成固定秩。

多模态模型（VL/Omni/视觉编码器）恰是最容易暴露这两处假设的 workload，因为它们把语言塔塞进嵌套 config、且各编码器以不同秩调用 attention。

## 参考实现及其约束

- 参考实现：vllm-ascend（vLLM 昇腾后端）。信号 1 的判定在 `vllm_ascend/utils.py` 的 `is_moe_model` / `_is_contain_expert`；信号 2 的算子在 `vllm_ascend/ops/mm_encoder_attention.py` 的 `AscendMMEncoderAttention.forward_oot`（`utils.py` 中经 `register_oot("MMEncoderAttention")` 注册为上游 `MMEncoderAttention` 的昇腾 OOT 替换算子）。
- 这些是该参考实现的具体绑定（`text_config` 键名、`"expert"` 子串匹配、`query.dim()==4` 分支、HunyuanOCR / Qwen3-VL/Omni 模型名），**不是技术本身的限制**。可迁移的是两条结构纪律本身，具体触发实例限于 source 覆盖（VL/Omni 型把 MoE 键嵌进 `text_config` 的多模态 MoE、以 3D query 调用编码器 attention 的 HunyuanOCR 视觉编码器），不外推到其它框架或其它 config 布局。
- 两处均为 correctness 型修复，source 未给修复前后的性能/精度数字，仅「原本崩、修后能起」的定性结果（信号 1 有 CI 精度测试通过佐证）。

## 相关经验

- 同类多模态编码器 packed 全注意力里，两个可互换昇腾融合算子的 `seq_len` 语义（原始长度 vs. cumsum）不同、误用也会导致输出错位——同源于「OOT 算子契约细节被上层误当同义」，见 [mm-encoder-packed-attention-seqlen-semantics](mm_encoder_packed_attention_seqlen_semantics.md)。
- CUDA 原生 vLLM 多模态模型移植 vllm-ascend 时的三处固定后端不兼容点（MoE 算子 / 视觉 flash_attn / 引擎图）见 [vllm-cuda-multimodal-npu-bringup](vllm_cuda_multimodal_npu_bringup.md)。
- 多模态模型 bringup 的启动/运行时环境类坑见 [multimodal-launch-and-runtime-env-pitfalls](multimodal_launch_and_runtime_env_pitfalls.md)。

## 相关静态页

- [Expert Parallel](../../concepts/parallelism/expert_parallel.md)——信号 1 的漏检直接导致 EP/MoE 通信方法（`moe_comm_method`）未初始化、FusedMoE 崩溃；判 MoE 是启用 EP 优化路径的前置门。
- [FIA / npu_fused_infer_attention_score](../../concepts/kernels/fused_infer_attention_score.md)——信号 2 的编码器 attention OOT 算子属昇腾融合注意力算子族，其输出秩/布局契约与 FIA 同类，须与下游线性层的张量布局对齐。

## Evidence

- 信号 1（diff 事实，merge commit `40c7db65599534e92a6f17cbacf2dc784bcc20b7`，`vllm_ascend/utils.py`）：`is_moe_model` 递归化为 `_is_contain_expert` 遍历嵌套 config dict；根因由维护者兼作者 PR 描述确认（顶层扫描漏检 VL/Omni 的 `text_config` 嵌套 MoE 键、判定在模型加载前被调不能用 FusedMoE 模块判），崩点与调用链由一手 traceback 佐证。
- 信号 2（diff 事实，merge commit `58adf7c8ac239d10fa1b9851c3d38af8930a17f3`，`vllm_ascend/ops/mm_encoder_attention.py:96,138-145`；OOT 注册见 `vllm_ascend/utils.py:697`）：入口 `is_reshaped = query.dim() == 4` + 收尾按秩分支折叠，与报错栈（`o_proj -> aclnnAddmm 161002`）对得上；维护者 PR body 明确修复目标为「保持 `AscendMMEncoderAttention` 输出形状与输入一致」。
- 溯源下探：[vllm-ascend-pr-3897-mm-bugfix-add-moe-verification-for-multi-modal-models](https://github.com/vllm-project/vllm-ascend/pull/3897)、[vllm-ascend-issue-5297-bug-tencent-hunyuan-hunyuanocr-model-execute-failed-with-linear-op-input](https://github.com/vllm-project/vllm-ascend/issues/5297)