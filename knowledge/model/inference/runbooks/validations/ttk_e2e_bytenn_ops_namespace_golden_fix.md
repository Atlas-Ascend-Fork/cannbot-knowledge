---
{
  "type": "Runbook",
  "title": "TTK e2e 失败根因：bytenn_ops 命名空间映射错误致 API_PARSE_FAIL",
  "description": "vLLM 容器内用 TTK 跑 bytenn_ops 自定义算子 rms_norm_cast 的 e2e 用例报 API_PARSE_FAIL。根因是 TTK 的 torch.ops 命名空间到 Python 包名映射错误。",
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
# TTK e2e 失败根因：bytenn_ops 命名空间映射错误致 API_PARSE_FAIL


## 摘要

vLLM 容器内用 TTK 跑 bytenn_ops 自定义算子 rms_norm_cast 的 e2e 用例报 API_PARSE_FAIL。根因是 TTK 的 torch.ops 命名空间到 Python 包名映射错误。

## 适用场景

TTK（ops-test-kit）在 vLLM 容器内对自定义算子跑 e2e 用例（`python3 -m ttk e2e -i ci/ttk_e2e_rms_norm_cast.csv --plugin .../golden.py --ti=1`），出现 API_PARSE_FAIL 时。适用条件：CSV 的 api_name 是 torch.ops.<namespace>.<op> 形式（框架 API 解析路径）而非 aclnn 前缀。

## 触发与观测

触发一：`NAMESPACE_PACKAGES` 映射的包名与环境实际安装的包名不一致。
观测一：`torch.ops.bytenn_ops` 目录为空、`hasattr(torch.ops.bytenn_ops, 'rms_norm_cast')` 为 False；直接走 `TorchOpsPackageLoader.ensure_registered` 复现 `REGISTRATION FAILED: TorchOpsPackageRegistrationError ... importing installed package 'custom_transformer' failed with ModuleNotFoundError`，`get_api_info => None`，TTK 汇总 fail_reason="API_PARSE_FAIL"。
注意：`ASCEND_CUSTOM_OPP_PATH`/`LD_LIBRARY_PATH` 只暴露 aclnn C 接口，与 torch.ops 的 Python 注册无关——调它们对该错误无效。

## 探针与操作

1. `docker exec <c> python3 -c "import torch; print(hasattr(torch.ops.bytenn_ops, 'rms_norm_cast'))"` 确认命名空间未注册。
2. 走 `TorchOpsPackageLoader.ensure_registered` + `FrameworkApiInfoKeeper().get(...)` 精确复现解析路径并看到 info=None。

## 机制与判别

判别一（API_PARSE_FAIL）：错误发生在签名解析（ensure_registered 强制 import 映射包）而非算子执行；证据链是映射代码（torch_ops_package_loader.py:24-27）、实际安装包名（bytenn_ops-1.5.5+git430b03a）与复现输出三者对齐。

## 适用与失效边界

适用：TTK e2e 对 torch.ops.<namespace>.<op> 形式 API 的解析失败排查。失效边界：本卡止于 API_PARSE_FAIL 的根因定位；后续 golden 阶段问题与修复验证不在本卡覆盖范围。

## 验证信号

### 来源结论a

> API_PARSE_FAIL 的根因：ttk/utilities/torch_ops_package_loader.py 的 NAMESPACE_PACKAGES 把 bytenn_ops 命名空间映射到 custom_transformer 包，而该环境实际安装的包名就是 bytenn_ops（dist-info: bytenn_ops-1.5.5+git430b03a.torch2.10.0.cann90）；解析时强制 import custom_transformer 抛 TorchOpsPackageRegistrationError（ModuleNotFoundError），FrameworkApiInfoKeeper 置 info=None，testcase_e2e.py:416-419 据此设 fail_reason="API_PARSE_FAIL"。复现：TorchOpsPackageLoader.ensure_registered 直接打印 REGISTRATION FAILED，且 hasattr(torch.ops.bytenn_ops, 'rms_norm_cast') 为 False。ASCEND_CUSTOM_OPP_PATH/LD_LIBRARY_PATH 只暴露 aclnn C 接口（libcust_opapi.so），与 torch.ops 的 Python 注册无关，对该错误没有影响。


## 补充机制片段

### 机制片段

```
NAMESPACE_PACKAGES = {
    "cann_ops_transformer": "cann_ops_transformer",
    "bytenn_ops": "custom_transformer",   # ← 期望 import custom_transformer
}

```
