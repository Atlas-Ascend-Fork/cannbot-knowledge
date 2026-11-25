---
{
  "type": "Runbook",
  "title": "K31/K3 BF16 MLA Prolog 更换入口后旧位置参数错绑 quant_scale_kv",
  "description": "在 cann-recipes-infer 类推理仓中，把普通（未配置 DSA 量化）Kimi K3/K31 的 BF16 MLA Prolog 从旧入口 `mla_prolog_bf16` 迁移到新统一入口 `mla_prolog`（或量化入口 `quant_mla_prolog` 同族接口）时的接口契约核对。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-20T14:17:05Z",
  "platforms": []
}
---

# K31/K3 BF16 MLA Prolog 更换入口后旧位置参数错绑 quant_scale_kv

## 适用场景

在 cann-recipes-infer 类推理仓中，把普通（未配置 DSA 量化）Kimi K3/K31 的 BF16 MLA Prolog 从旧入口 `mla_prolog_bf16` 迁移到新统一入口 `mla_prolog`（或量化入口 `quant_mla_prolog` 同族接口）时的接口契约核对。本规则来自 K31 适配 PR #1（master 4447f2f → head 58d6b32，14 个变更文件）的检视回合（source 0 seq 677/678）。

## 触发与观测

- 触发：PR 将 `KimiDSAAttention` 内 Prolog 导入从旧 BF16 专用入口换成 `ops.mla_prolog`，但调用处仍按旧签名把 epsilon 作为第 10 个位置参数传入（source 0 seq 618、678）。
- 探针（可执行）：不改 NPU 实现，用 AST 提取新入口 `mla_prolog` 的公开签名并 `inspect.signature(...).bind(*args)` 复算第 10 个位置参数的实际绑定；再用 `torch.library` 注册 `optional_tensor(Tensor x, Tensor? quant_scale_kv=None)` 的最小 schema，把绑定结果喂给 dispatcher 观察类型拒绝（source 0 seq 569/571）。
- 原始观测（CPU 接口检查，tool_observed）：

```
Plain MLA actual 10th argument binding: {'quant_scale_kv': 1e-06, 'norm_eps': 1e-05, 'cache_mode': 0, 'rope_mode': 1}
Dispatcher optional Tensor rejects old epsilon: pr1_contract_review::optional_tensor() Expected a value of type 'Optional[Tensor]' for argument 'quant_scale_kv' but instead found type 'float'.
```

（source 0 seq 571/572，脚本 exit_code 0）

## 探针与操作

探针脚本 `verify_contracts.py` 的关键结构（source 0 seq 569）：

1. `ast.parse` 读取仓内 `mla_prolog.py`，取 `mla_prolog` 函数定义，函数体替换为 `return locals()` 后 `exec`，避免 import NPU 实现；
2. 构造 `[object()]*9 + [1e-6]` 作为旧调用形态的 10 个位置参数，`inspect.signature(ns['mla_prolog']).bind(*args)` 后打印 `quant_scale_kv/norm_eps/cache_mode/rope_mode` 四个关键字的实际取值；
3. `torch.library.Library('pr1_contract_review','DEF')` 定义 `optional_tensor(Tensor x, Tensor? quant_scale_kv=None) -> Tensor`，传入绑定的 `quant_scale_kv`，捕获 RuntimeError 首行。

## 机制与判别

- 分支机制（源码 diff，tool_observed，source 0 seq 622/623）：量化路径导入 `ops.quant_mla_prolog.quant_mla_prolog_op`；BF16 路径导入 `ops.mla_prolog.mla_prolog`。BF16 调用处第 10 个位置参数为 `self.q_a_layernorm.variance_epsilon`（=1e-6），而新签名该位是 `quant_scale_kv: Optional[Tensor]`，`norm_eps` 已移到第 11 位（默认 1e-5）。
- 判别点：错误不是“参数名拼错”一类显式报错，而是位置参数静默错绑——若调用方恰好不触发 dispatcher 类型检查（例如走 Python 回退路径），epsilon 会以 float 进入 scale 语义位，属于数值语义级风险；本例由 Optional[Tensor] schema 检查显式拒绝（source 0 seq 571/678）。
- 范围判别（agent_narrative，基于源码核对，source 0 seq 678）：影响未配置 DSA、走 BF16 MLA 的普通 K3；CP 开关不影响触发。

## 验证信号

- tool_observed（source 0 seq 571/572）：绑定 dump 与 dispatcher 拒绝输出逐字如上；脚本 exit_code 0。
- agent_narrative（source 0 seq 618/677/678）：接口迁移不完整的确认与最终检视报告；权重方向（旧 `[K,O]` vs 新 `[O,K]`）、`RopeMode.NONE`、`CacheMode.PA_NZ` 未一并适配，仅把 epsilon 改成关键字参数不够。
- 验证层级：CPU/接口检查（AST + signature bind + dispatcher schema），未执行 NPU 整网验证（source 0 seq 678 明示）。

## 适用与失效边界

- 仅证明该 PR 快照（58d6b32）上的签名契约错位与 dispatcher 行为；不证明修复方案的正确性（本会话未实施修复）。
- 探针方法（AST 提取签名 + bind + 最小 schema dispatcher）可复用于同类“入口替换后旧调用未迁移”的核对，不依赖 NPU 环境。
- 新入口后续若再改签名，本结论的参数序号失效，需按同法重算。

## 附：断言存档

- K31 PR 将 BF16 MLA Prolog 入口从 mla_prolog_bf16 换成 mla_prolog 后，调用处仍把 epsilon 作为第 10 个位置参数传入；新签名第 10 参数是 quant_scale_kv: Optional[Tensor]，实际绑定 {'quant_scale_kv': 1e-06, 'norm_eps': 1e-05, 'cache_mode': 0, 'rope_mode': 1}，dispatcher 拒绝 float 进 Tensor 位
