---
{
  "type": "Runbook",
  "title": "XdgOmniMoE 架构名与 vLLM/vllm-ascend 注册表不一致致服务无法启动：批量对齐 10 处注册键（不改模型目录）",
  "description": "dots-note 服务启动报 Model architectures ['XdgOmniMoEForCausalLM'] are not supported。按用户要求改框架侧不改模型目录，用 base64 打包脚本在容器内批量替换 vLLM 4 文件 7 处 + vllm-ascend 2 文件 3 处共 10 处架构名字符串（只改注册键与比较串、不改类名）；10 处全部 OK，grep 复核 XdgOmniMoE 各引用就位。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# XdgOmniMoE 架构名与 vLLM/vllm-ascend 注册表不一致致服务无法启动：批量对齐 10 处注册键（不改模型目录）


## 摘要

dots-note 服务启动报 Model architectures ['XdgOmniMoEForCausalLM'] are not supported。按用户要求改框架侧不改模型目录，用 base64 打包脚本在容器内批量替换 vLLM 4 文件 7 处 + vllm-ascend 2 文件 3 处共 10 处架构名字符串（只改注册键与比较串、不改类名）；10 处全部 OK，grep 复核 XdgOmniMoE 各引用就位。

## 适用场景

模型 config.json 的 architectures 名与 vLLM/vllm-ascend 注册表（含 MTP/spec-decode 补丁的架构匹配）不一致导致服务无法启动、且不允许改模型目录（权重/配置只读）的场景。dots-note/XdgOmniMoE 类私有模型接入（发布名与框架注册名不一致）均可套用。

## 触发与观测

触发：start_vllm_server.sh 启动即失败。
观测：`Model architectures ['XdgOmniMoEForCausalLM'] are not supported for now. Supported architectures: ... 'XdgMoEForCausalLM', 'XdgMoEVLForCausalLM' ...`。注意 MTP 推测解码补丁（patch_speculative_config.py:127）与 VL 变体注册也检查同一组名字，只改一处不够。

## 探针与操作

1. 全引用点搜索：grep 模型目录自定义文件名（configuration_xdgmoe.py/modeling_xdgmoe.py）、vllm 与 vllm-ascend 两侧的注册键与比较串（registry/speculative/llm_base_proposer/xdg_moe_vl/patch_speculative_config）。
2. 批量替换：写 Python 脚本定义 (file, [(old,new)...]) 清单（幂等：count==0 报 WARNING、count>1 只换第一处并提示），base64 编码经 docker exec 执行规避多层引号转义。
3. 复核：grep 新架构名逐文件确认 10 处就位；类名（XdgMoEForCausalLM 等）保持不动（仍作为 registry 的 value）。

## 机制与判别

机制：vLLM 架构解析按注册键字符串匹配；MTP/spec-decode 路径在 config/speculative.py 与 vllm-ascend patch_speculative_config.py 里还有第二组架构名比较，VL wrapper（xdg_moe_vl.py:1422）内部初始化语言模型时也用该名——三处必须同步改。
判别：若服务能起但多模态 400（"not a multimodal model"），说明注册的是非 VL 变体、需按部署需求选择 ForCausalLM 或 VLForCausalLM 键名。

## 适用与失效边界

- 本修复改的是容器内 vllm/vllm-ascend 源码（6 文件 10 处字符串），升级/重装框架会丢失，长期应改模型侧 config 或上游注册表。
- 验证范围：10 处替换全部 OK、grep 复核 XdgOmniMoE 各引用就位（源码级）；运行期端到端行为不在本卡验证范围。
- 轨迹后段（FIA 精度 dump/golden 对比）为另一主题，本候选不覆盖；该部分在轨迹尾部未完成。

## 验证信号

### 来源结论b

> 修复（用户约束：不改模型文件目录，改 vllm 和 vllm-ascend 与模型 arch 名一致）：写 fix_arch.py（base64 编码经 docker exec 执行避免多层引号转义），批量替换 6 个文件 10 处——vLLM 侧 registry.py:102/103/636 三个注册键、config/speculative.py:515（MTP 架构匹配）与 :530（MTP architectures 覆盖值）、v1/spec_decode/llm_base_proposer.py:1235（VL 模型名匹配）、model_executor/models/xdg_moe_vl.py:1422（VL 内部初始化语言模型的架构名）；vllm-ascend 侧 patch/platform/patch_speculative_config.py:127/137 与 spec_decode/llm_base_proposer.py:307。只改架构名字符串（注册键和比较逻辑），不改任何 Python 类名（XdgMoEForCausalLM 等类定义保持原样仍作为 value 被 registry 引用）。10 处全部 OK，grep 复核 XdgOmniMoE 各引用就位。


## 补充机制片段

### 机制片段

```
import sys

changes = [
    ("/vllm-workspace/vllm/vllm/model_executor/models/registry.py", [
        ('"XdgMoEForCausalLM":', '"XdgOmniMoEForCausalLM":'),
        ('"XdgMoEVLForCausalLM":', '"XdgOmniMoEVLForCausalLM":'),
        ('"XdgMoEMTPModel":', '"XdgOmniMoEMTPModel":'),
    ]),
    ("/vllm-workspace/vllm/vllm/config/speculative.py", [
        ('("XdgMoEForCausalLM", "XdgMoEVLForCausalLM")', '("XdgOmniMoEForCausalLM", "XdgOmniMoEVLForCausalLM")'),
        ('"architectures": ["XdgMoEMTPModel"]', '"architectures": ["XdgOmniMoEMTPModel"]'),
    ]),
    ("/vllm-workspace/vllm/vllm/v1/spec_decode/llm_base_proposer.py", [
        ('"XdgMoEVLForCausalLM",', '"XdgOmniMoEVLForCausalLM",'),
    ]),
    ("/vllm-workspace/vllm/vllm/model_executor/models/xdg_moe_vl.py", [
        ('architectures=["XdgMoEForCausalLM"]', 'architectures=["XdgOmniMoEForCausalLM"]'),
    ]),
    ("/vllm-workspace/vllm-ascend/vllm_ascend/patch/platform/patch_speculative_config.py", [
        ('("XdgMoEForCausalLM", "XdgMoEVLForCausalLM")', '("XdgOmniMoEForCausalLM", "XdgOmniMoEVLForCausalLM")'),
        ('"architectures": ["XdgMoEMTPModel"]', '"architectures": ["XdgOmniMoEMTPModel"]'),
    ]),
    ("/vllm-workspace/vllm-ascend/vllm_ascend/spec_decode/llm_base_proposer.py", [
        ('"XdgMoEVLForCausalLM",', '"XdgOmniMoEVLForCausalLM",'),
    ]),
]

errors = 0
for filepath, replacements in changes:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"ERROR: File not found: {filepath}")
        errors += 1
        continue

    for old, new in replacements:
        count = content.count(old)
        if count == 0:
            print(f"WARNING: '{old}' not found in {filepath}")
            errors += 1
        elif count > 1:
            print(f"WARNING: '{old}' found {count} times in {filepath}, replacing first only")
        content = content.replace(old, new, 1)
        print(f"OK: {filepath}: {old[:40]}... -> replaced")

    with open(filepath, 'w') as f:
        f.write(content)

if errors:
    print(f"\nCompleted with {errors} errors/warnings")
    sys.exit(1)
else:
    print("\nAll changes applied successfully!")

```
