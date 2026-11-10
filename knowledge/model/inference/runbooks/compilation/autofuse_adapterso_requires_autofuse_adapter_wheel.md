---
{
  "type": "Runbook",
  "title": "autofuse_adapter.so 未生成的根因判别：requires_autofuse_adapter 标志探针（已装 wheel 落后于源码）",
  "description": "torchair AutoFuse 常规路径下只产出 kernel.so/wrapper.so，autofuse_adapter.so 仅在 inductor_npu_ext 读到 V.graph.wrapper_code.requires_autofuse_adapter=True 时才编译（npu.py:1142），且仅 fx_converter（GE Convert runtime v2）路径需要它——default 变体走 fxrt 自有运行时直接 dlopen wrapper.so。判定探针：对源码树与已装 site-packages 的 fx_wrapper.py 分别 grep requires_autofuse_adapter 再 diff；本例输出 1d0（源码树 :318 有 True、wheel 无），加文件时间戳证实已装 torch_npu wheel 落后于源码，adapter 永不生成与模型跑通同时成立。根因（wheel 未更新）在本轨迹内未修复。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "agnostic"
  ]
}
---

# autofuse_adapter.so 未生成的根因判别：requires_autofuse_adapter 标志探针（已装 wheel 落后于源码）

## 适用场景

- 路径：torch.compile + inductor + inductor_npu_ext（torchair AutoFuse）+ `FX_WRAPPER=1`（inductor → fx_wrapper → fxrt，`FXRT_BACKEND_VARIANT` 控制执行者变体）。
- 框架：torch_npu 2.13.0+gitea585a8（torch_npu.fxrt 子包）、inductor-npu-ext 0.0.1、fx_converter 0.1.dev0+164734d、CANN 9.2.0；Atlas 910B3。
- 症状面：AutoFuse 融合算子只产出 kernel.so/wrapper.so，没有 autofuse_adapter.so，而 fx_converter（GE Convert runtime v2）按设计"必须用到这个库"——两者表面矛盾，需判别模型究竟走了哪条运行时、adapter 为何没生成。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${TORCH_NPU_ROOT}` 为torch-npu 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

- 触发（事件 555，客观）：收集钩子单次 run 报 56 条 `[WARNING] [fxrt_fx] kernel artifact not found: autofuse_adapter.so (${LOCAL_PATH_1})`；用户质疑（事件 564）模型是否压根没走 fx_converter。
- 运行侧观测（事件 463，客观）：run 日志含 `[fxrt] 使用 fxrt.fx_backend.backend 作为 torch.compile 后端`——即 `load_fxrt_backend()` 以 `FXRT_BACKEND_VARIANT=default` 加载了 `fxrt.fx_backend`，不是 fx_converter。

## 探针与操作

探针 1（adapter 生成开关，事件 577，inductor_npu_ext `npu.py:1142` 附近静态读取）：

```python
        # Generate adapter source only when the FXRT wrapper requests the C ABI.
        export_adapter = bool(getattr(getattr(V.graph, "wrapper_code", None), "requires_autofuse_adapter", False))
        artifacts["export_adapter"] = str(export_adapter)
```

探针 2（谁该设置该标志，事件 615/618，源码树 grep + sed）：torch-npu 源码树 `fxrt/fxrt/python/fxrt/fx_wrapper.py:318` 有 `requires_autofuse_adapter = True`（挂在 `class FxrtFxWrapper(WrapperFxCodegen)` 上）；同一事件对已装 site-packages 的 grep 只命中 `315:class FxrtFxWrapper(WrapperFxCodegen):`、无标志行。

探针 3（源码树 vs 已装 wheel 判定探针，事件 629）：

```bash
diff <(grep -n "requires_autofuse_adapter" ${TORCH_NPU_ROOT}/pytorch/fxrt/fxrt/python/fxrt/fx_wrapper.py) <(grep -n "requires_autofuse_adapter" ${TORCH_NPU_ROOT}/fxrt/fx_wrapper.py) 2>/dev/null; echo "diff-exit=$?"

# 输出（事件 629）：
# 1d0
# < 318:    requires_autofuse_adapter = True
# diff-exit=1
# stat 输出：源码树 fx_wrapper.py 2026-10-17 10:58:56，已装 wheel 2026-10-16 14:42:26
```

源码树 FxrtFxWrapper（事件 618 原文）：

```python
class FxrtFxWrapper(WrapperFxCodegen):
    """WrapperFxCodegen that sends the host FX graph to the configured backend."""

    requires_autofuse_adapter = True
```

## 机制与判别

- 结论：autofuse_adapter.so 的生成开关在 inductor_npu_ext npu.py:1142：`export_adapter = bool(getattr(getattr(V.graph, "wrapper_code", None), "requires_autofuse_adapter", False))`，仅当 wrapper codegen（FxrtFxWrapper）带 `requires_autofuse_adapter = True` 时才编译 adapter。
- 结论：模型实际走 FXRT_BACKEND_VARIANT=default → `fxrt.fx_backend.backend` 的 fxrt 自有运行时：autofused HOP 经 compiled_kernel_mutation → _AscendcKernelLauncher → NpuInductorKernel → `cdll.LoadLibrary(self.lib_wrapper)` 直接 dlopen，仅需 kernel.so + wrapper.so、不需要 adapter——adapter 缺失与模型跑通同时成立。
  - 分支 A（成立，default 变体）：`_AscendcKernelLauncher`（事件 508）包 `NpuInductorKernel`，其 `load()` 即 `self.dl = cdll.LoadLibrary(self.lib_wrapper)`（事件 522），kernel.so 由 wrapper 内部加载，链路不引用 adapter。
  - 分支 B（本次未触发，converter 变体）：fx_converter（GE Convert runtime v2）经 `fxrt_converter_metadata()` 把 `adapter_path` 挂到 IR `compiled_kernel_mutation` 节点属性（`torch_npu/fxrt/compiled_kernel_adapter.py:154`，事件 604），GE 侧通过 C-ABI adapter 下发融合 kernel——此路径必须 adapter 存在。
- 结论：判定探针：对源码树与已装 site-packages 的 fx_wrapper.py 分别 `grep -n requires_autofuse_adapter` 再 diff，输出 `1d0 < 318:    requires_autofuse_adapter = True`（源码树 10-17 10:58 更新、已装 wheel 10-16 14:42 构建），判定已装 torch_npu wheel 落后于源码、缺少该标志、export_adapter 恒为 False，adapter 永不生成。
  - 即："装的新代码支持 converter 但没装"——源码树 10-17 早上刚更新加上标志，已装 wheel 是 10-16 构建的旧版本；跑通的是不需要 adapter 的 default 路径，两个表面矛盾的事实同时成立。
- 未验证推断（假设，非结论）：用当前源码树重装 torch_npu + `export FXRT_BACKEND_VARIANT=converter` 后 adapter 应生成且 Convert 可消费；旧环境 log.txt 显示 converter 变体曾因 `PadV3 no binary` 失败（GE 算子覆盖问题，事件 227），新 CANN 是否修复需实测。根因（wheel 未更新）在本轨迹内未修复。

## 验证信号

（平台：Atlas 910B3 + CANN 9.2.0 + torch_npu 2.13.0+gitea585a8；证据等级：静态代码读取 + 单次 run 日志 + 单次 grep/stat/diff 探针）

- 事件 555：56 条 `kernel artifact not found: autofuse_adapter.so` warning（单次 run，adapter 确实不在产物目录）。
- 事件 577：npu.py:1142 `export_adapter = bool(getattr(getattr(V.graph, "wrapper_code", None), "requires_autofuse_adapter", False))` 开关代码（静态读取）。
- 事件 615：源码树 `fx_wrapper.py:318:    requires_autofuse_adapter = True`（grep 命中）。
- 事件 618：源码树 FxrtFxWrapper 类定义带标志；已装 site-packages 同名类无该行（grep 仅命中 315 行类定义）。
- 事件 629：stat 时间戳（源码树 10-17 10:58 vs wheel 10-16 14:42）+ diff 输出 `1d0 / < 318:    requires_autofuse_adapter = True / diff-exit=1`。
- 事件 463：run 日志 `[fxrt] 使用 fxrt.fx_backend.backend 作为 torch.compile 后端`（default 变体实际生效）。

## 适用与失效边界

- 探针适用于"torch_npu 源码树与安装 wheel 可能版本漂移"导致的 fxrt 行为差异判定（本例：源码树随后被同步更新过，事件 588 时 fxrt 目录一度消失又恢复）。
- 判定基于单机单次 grep/stat/diff；源码树是滚动同步的副本，结论只对当时快照成立。
- 分支 B（converter 变体 adapter 消费链）在本轨迹未实测；"adapter_path 指向不存在文件时 Convert 必失败"来自代码阅读（`fxrt_converter_metadata()` 对 lib_kernel/lib_wrapper 缺失即抛 RuntimeError，事件 508），未运行验证。
- 若 wheel 已含标志而 adapter 仍缺，需另查 `V.graph.wrapper_code` 是否真是 FxrtFxWrapper 实例（例如 codegen 被 `inductor_npu_ext` 后注册的整条 DeviceCodegen 替换冲掉的场景，见事件 92/109 的 `fx_wrapper_codegen` 重置机制）。
- 本判定不涉及性能结论；adapter 生成与否对 default 路径性能无影响（该路径不加载 adapter）。
