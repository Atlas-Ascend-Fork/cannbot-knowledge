---
type: Runbook
title: Kimi K3 装好一个 SiTU 算子却丢失另一个：两算子须联合打包
description: 针对 950PR/DT 的 SiTU 与 grouped_situ_mx_quant 配套安装，检查同 vendor op_api 整体覆盖，并分别使用独立
  PyTorch golden 验收。
tags:
- task.debugging
- topic.compilation
- topic.mixture_of_experts
status: stable
sources: []
created_at: '2026-10-30T03:17:20Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
---

# Kimi K3 装好一个 SiTU 算子却丢失另一个：两算子须联合打包

## 现象

Kimi K3 的 dense/shared、非量化专家路径需要 `situ_and_mul_sparse`，量化专家路径需要 `grouped_situ_mx_quant`。在同一套昇腾 950PR/DT 环境中分别编译、安装两个包后，后安装的算子可用，先安装的算子却不可用。单独反复重装可能让“丢失的算子”来回切换。

该现象先查 vendor 包的安装边界，再查模型调用。不能只因 `import custom_ops` 成功，就认定两个算子已经共同可用；Python 扩展注册与底层包中的实现是两层依赖。

## 适用场景

- 工程形态：`ops/ascendc` 构建的两个自定义算子、同一 vendor 的 op_api 层、配套 `torch_ops_extension` 和 `torch.ops.custom` 调用。
- 目标平台：950PR/DT；构建目标为 `ascend950`。CANN 环境、二进制算子包与 PyTorch 扩展须成套匹配，本文未完成各版本实机验收。
- 模型中的使用：SiTU 与 grouped SiTU+MXFP8 融合量化分别服务不同分支，应在同一安装环境共存。
- 本卡仅针对整体替换同 vendor op_api 的安装路径；其他 vendor 隔离机制或不同打包器需先验证其安装行为。

## 根因与判别方法

若每次安装会整体替换目标 vendor 的 op_api 层，两个只各含一个算子的安装包不构成增量合并。包 A 安装后有算子 A，随后安装包 B 把这层替换成仅含 B 的内容，A 便不可用。重新编译 Python 扩展不能自动补回被覆盖的底层算子。

按顺序核对：

1. 两个构建产物的 vendor、安装目录、op_api 文件和安装顺序，确认它们是否共享替换范围。
2. 使用的是哪个 CANN 环境、哪个 OPP vendor 环境、哪个 Python 扩展；排除编译时和运行时加载了不同环境。
3. 同一进程中分别调用两个 `torch.ops.custom` 接口，保留真实报错；只查看 namespace 名称不足以验证链接和执行。
4. 若两者本来就都可调用，再进入精度和 dtype 对齐，不要继续把数值问题归因于包覆盖。

## 处理步骤与命令

从源码根目录开始，先设置部署所用 CANN 环境和 `ASCEND_HOME_PATH`。下面是联合构建、安装、编译扩展和测试的一套连续命令；安装会更新指定 OPP 中的自定义包，执行前确认目标环境与要替换的完整包。

```bash
cd ops/ascendc
bash build.sh -n "situ_and_mul_sparse;grouped_situ_mx_quant" -c "ascend950"
cd output
./CANN-custom_ops-*.run --quiet --install-path="${ASCEND_HOME_PATH}/opp"
source "${ASCEND_HOME_PATH}/opp/vendors/customize/bin/set_env.bash"

# 编译并安装 Torch 扩展
cd ../torch_ops_extension
bash build_and_install.sh

# （可选）分别验证两个 SiTU 自定义算子相对原生 PyTorch golden 的精度
cd ../examples
python3 test_situ_custom_ops.py
```

`-n` 中的分号必须处于引号内，它是构建脚本的目标分隔符。若让 Shell 把它解释成两条命令，就没有完成联合构建。检查最终生成的同一个 `.run` 包确实同时包含两个目标，再安装，而不是只把两个独立包放到同一目录。

## 设计决策：安装验收与数学验收分开

联合打包只解决两个实现共存。精度上也需要独立的原生 PyTorch golden，不能把旧两算子链当作唯一 oracle：新融合实现若与旧链位级一致，只能说明两条实现一致，不能排除共同错误。

SiTU 输入在最后一维分成 gate/up 两半。golden 的计算是 `β·tanh(gate/β)·sigmoid(gate)` 与 `α·tanh(up/α)` 相乘；`high_precision=False` 时先把两个分支各自舍入到输入 dtype，再做乘积，不能用始终 FP32 的参考悄悄替换这个语义。以下为完整 golden 函数，只依赖 `torch`，且强制在 CPU 上计算：

```python
def situ_golden(x, beta, alpha, high_precision):
    """SiTU(gate) * bounded_up, using native PyTorch on CPU only.

    high_precision=False rounds each branch to the input dtype before the
    product; True keeps both branches in FP32. Both modes round the output.
    """
    if x.device.type != "cpu":
        raise ValueError("SiTU golden must run on CPU")
    gate, up = x.float().chunk(2, dim=-1)
    gate = beta * torch.tanh(gate / beta) * torch.sigmoid(gate)
    up = alpha * torch.tanh(up / alpha)
    if not high_precision:
        gate = gate.to(x.dtype).float()
        up = up.to(x.dtype).float()
    return (gate * up).to(x.dtype).float()
```

融合算子的输出还含 E4M3 data 与 E8M0 scale，需先反量化后再与同一个 golden 比较。测试实现按每组量化 scale 计算量化舍入/饱和误差预算；预算从 golden 推导，不能用算子输出反推容差，否则错误结果也可能被自己的预算放行。

稀疏输出只比较有效专家行，`valid = min(sum(expert_tokens_list), rows)`；尾部可能未写入，不能拿未写尾行作为精度失败。与此同时，空比较也不能当作 PASS。下面的比较函数把形状、非空、有限性和误差预算同时纳入判定：

```python
def compare(name, actual, golden, budget):
    if actual.shape != golden.shape or golden.numel() == 0:
        raise AssertionError(f"Invalid comparison shapes: {actual.shape}, {golden.shape}")
    error = (actual - golden).abs()
    bad = ~torch.isfinite(actual) | ~torch.isfinite(golden) | (error > budget)
    ok = not bad.any().item()
    rmse = (actual - golden).square().mean().sqrt().item()
    print(f"  [{'PASS' if ok else 'FAIL'}] {name} vs torch golden: "
          f"max_abs={error.max().item():.6g} rmse={rmse:.6g} "
          f"out_of_tolerance={bad.sum().item()}/{golden.numel()}")
    return ok
```

## 验证信号

本轮核对了联合安装命令、两个接口的调用及独立 golden/比较实现；未执行这些命令或 NPU 测试，没有本轮 `ALL PASS` 运行结果。

## 目标验收

目标环境应先确认同一进程可调用两算子，再按测试覆盖 dense、带空专家的 sparse、尾行、全零和边界输入，并覆盖 BF16/FP16 与 high_precision 模式。分别保存 sparse vs golden、fused 反量化 vs golden 的结果以及退出码。任一比较失败必须作为失败处理，不以扩大容差、删掉边界输入或仅检查 fused vs sparse 取代验收。

两算子都通过局部数学验收后，仍需在实际 K3 路由下验收整网输出；namespace 存在、包装层 import、局部算子通过和整网精度是不同层级的证据。

## 坏实践、回退与失效边界

- 分别重装两个包会反复覆盖；应恢复先前已知完整 vendor 包及匹配扩展，不能只恢复一个 `.so`。
- `high_precision=False` 的分支舍入和 E4M3 量化误差应分别解释，不能一并放宽 SiTU 容差。
- package vendor、算子 schema、scale 布局或版本变化后，重新核对安装覆盖范围和接口；本卡不保证任意 MC2/GMM/SiTU 版本互通。
- 一般构建/打包机制继续阅读[自定义算子构建打包排查](ascendc_custom_op_build_packaging_availability.md)。本卡补充 K3 两算子的联合目标与独立数学验收，不扩展该卡的平台范围。
