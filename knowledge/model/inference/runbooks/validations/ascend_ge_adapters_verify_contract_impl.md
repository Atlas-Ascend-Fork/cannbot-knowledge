---
{
  "type": "Runbook",
  "title": "Ascend GE 适配框架 core/verify.py 按契约实现并通过 4 步自验：save_bundle 落盘 bundle.json（具体 shape）+ monkeypatch 探针证实 compare 走 tools/compare.py",
  "description": "在 ascend-ge-adapters 按架构文档 §5.4 契约实现 core/verify.py 的 save_bundle：按 logical 名落盘 inputs/<logical>.bin 与 golden_logits.bin、记录具体 shape（非 io_spec 的 -1）并把 provenance 原样写入 bundle.json。4 步自验（mock）全部通过：bundle 结构、cosine 对比、monkeypatch 探针证实 compute_metrics 被调用（走 tools/compare.py）、.bin 路径对比。",
  "tags": [
    "task.implementation",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# Ascend GE 适配框架 core/verify.py 按契约实现并通过 4 步自验：save_bundle 落盘 bundle.json（具体 shape）+ monkeypatch 探针证实 compare 走 tools/compare.py


## 适用场景

在 ascend-ge-adapters 按架构文档 §5.4 契约实现 core/verify.py 的 save_bundle：按 logical 名落盘 inputs/<logical>.bin 与 golden_logits.bin、记录具体 shape（非 io_spec 的 -1）并把 provenance 原样写入 bundle.json。4 步自验（mock）全部通过：bundle 结构、cosine 对比、monkeypatch 探针证实 compute_metrics 被调用（走 tools/compare.py）、.bin 路径对比。验证层级为 mock 自测（cpu_reference）。

## 触发与观测

触发：契约开发任务（无故障）。探针：读 docs/architecture.md §5.4/§6/§10/§11、core/graph.py IoSpec/IoNode、core/adapter.py、tools/compare.py 的 PrecisionComparator.compute_metrics/compare_and_report/load_file 签名、import 依赖检查。观测：4 步 mock 自测全 PASS；bundle.json 与 §5.4 逐字段对齐（具体 shape 1900/11）。

## 探针与操作

关键探针与修复操作。证据角色覆盖：implementation, validation。

## 机制与判别


> 4 步自验全部通过（无需真实权重的 mock）：test_golden_and_bundle PASS（bundle.json 结构符合 §5.4、具体 shape 1900/11 而非 -1、inputs/*.bin 落盘、logical 名映射正确）；test_compare_tensors PASS（cosine=1.000000 pass_overall=True）；test_compare_via_monkeypatch_probe PASS（compute_metrics called 1 次，证实走了 tools/compare.py）；test_compare_bin_paths PASS（cosine=0.999997）；git status 确认 core/ 下 verify.py 与其余脚手架文件均为未跟踪新增、未修改 compare.py 等既有文件。


```
    def save_bundle(self, dir, inputs, golden, io_spec, provenance):
        """落盘 inputs/golden .bin + bundle.json (schema 见 docs §5.4), 返回 bundle.json 路径。

        每个输入张量 → <dir>/inputs/<logical>.bin (logical 取自 io_spec.inputs[i].logical,
        按位置对应 forward 入参序); golden → <dir>/golden_logits.bin (logical 取自
        io_spec.outputs[0].logical)。记录**具体 shape** (张量真实 shape, 不是 io_spec 的 -1)
        + file 相对路径 (相对 bundle 目录)。provenance 原样写入 (调用方负责塞
        seed/model/soc/dtype/git_commit/版本/时间戳等 — 本模块不编造)。
        """
        inputs_dir = os.path.join(dir, "inputs")
        os.makedirs(inputs_dir, exist_ok=True)

        in_entries = []
        for i, t in enumerate(inputs):
            logical = _logical(io_spec.inputs, i, f"input_{i}")
            rel = os.path.join("inputs", f"{logical}.bin")
            _dump(t, os.path.join(dir, rel))
            in_entries.append({"logical": logical, "shape": _shape(t), "file": rel})

        g_logical = _logical(io_spec.outputs, 0, "logits")
        g_rel = "golden_logits.bin"
        _dump(golden, os.path.join(dir, g_rel))
        g_entry = {"logical": g_logical, "shape": _shape(golden), "file": g_rel}

        bundle = {
            "inputs": in_entries,
            "golden": g_entry,
            "provenance": provenance or {},
        }
        bundle_path = os.path.join(dir, "bundle.json")
        with open(bundle_path, "w") as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
        return bundle_path
```

## 验证信号

GE 适配框架（AIR/ONNX → OM/ACL|GeSession）的验证模块契约实现：bundle 记具体 shape、monkeypatch 探针证实 compare 走 tools/compare.py。


## 适用与失效边界

适用：GE 适配框架（AIR/ONNX → OM/ACL|GeSession）的验证模块契约实现：bundle 记具体 shape、monkeypatch 探针证实 compare 走 tools/compare.py。失效边界：验证为 mock 自测（假 model、小张量、monkeypatch 探针），未接真实权重/真实 backend；两层 shape（io_spec -1 vs bundle 具体）约束下 .bin 加载需 dtype 信息来自 io_spec。
