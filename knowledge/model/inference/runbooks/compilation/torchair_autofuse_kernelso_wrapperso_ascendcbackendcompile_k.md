---
{
  "type": "Runbook",
  "title": "按算子收集 torchair AutoFuse 融合算子的 kernel.so/wrapper.so（扩展 AscendcBackend.compile_kernel 落盘钩子）",
  "description": "AutoFuse 融合算子编译产物默认只落在 $TORCHINDUCTOR_CACHE_DIR/ascendc/host_<soc>/<autofused_xxx_md5>/<tiling_hash>/ 下按 hash 组织，无按算子收集开关。在模型侧既有 fxrt AscendcBackend.compile_kernel patch 上扩展：编译前落源码（原有），编译后从返回 launcher 的 _compiled（NpuInductorKernel）取 lib_kernel/lib_wrapper 拷入 FX_DUMP_DIR、与源码同名配对，不改 inductor_npu_ext。实测单次运行收集 28 个融合算子共 56 个 .so，模型正常跑完无 Traceback；autofuse_adapter.so 列为可选 artifact。",
  "tags": [
    "task.implementation",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "agnostic"
  ]
}
---
# 按算子收集 torchair AutoFuse 融合算子的 kernel.so/wrapper.so（扩展 AscendcBackend.compile_kernel 落盘钩子）

## 适用场景

- 路径：torch.compile + inductor + inductor_npu_ext（torchair AutoFuse）+ `FX_WRAPPER=1`（inductor → fx_wrapper → fxrt），模型侧 `fxrt_fx_wrapper.py` 已有 patch `AscendcBackend.compile_kernel` 落 kernel 源码的钩子。
- 框架：torch 2.13.0+cpu、torch_npu 2.13.0+gitea585a8（torch_npu.fxrt 提供 `fxrt.ascendc_fx_wrapper.AscendcBackend`）、inductor-npu-ext 0.0.1（torchair AutoFuse，`NpuInductorKernel` 于 `inductor_npu_ext/compiler/_kernel.py:48`）、CANN 9.2.0（autofuse）。
- 硬件：Atlas 910B3、aarch64。目标：把每个融合算子的编译产物按算子收集到指定目录（收集融合算子 .so 做后续分析/交付）。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

- 需求（事件 474）：把 torchair AutoFuse 融合生成的算子 .so 保存到指定文件。
- 现状（事件 480，客观）：.so 固定落在 inductor 缓存 `${LOCAL_PATH_1}/<autofused_xxx_md5>/<tiling_hash>/{kernel.so, wrapper.so, asc_kernel.py}`（launch_compile.sh 已设 `TORCHINDUCTOR_CACHE_DIR=${LOCAL_PATH_2}`），没有单独控制 .so 落盘位置的开关；改该变量只能整体换缓存位置、且按 tiling hash 组织，不是干净的按算子收集。

## 探针与操作

方式 1（零代码）：改 `launch_compile.sh` 的 `TORCHINDUCTOR_CACHE_DIR`。缺点：整个 inductor 缓存都在里面、按 hash 组织。不满足"按算子收集"需求。

方式 2（本次实现，推荐）：扩展模型侧既有 patch。启用条件：`FX_WRAPPER=1` 且 `FX_DUMP_DIR` 非空（launch_compile.sh 默认 `FX_DUMP_DIR=../profiling/fx_capture`）。

改动一（事件 528）：`_make_dumping_compile_kernel` 在 fxrt 的 `compile_kernel` 前后各插一手——编译前落 kernel 源码（原有能力），编译后从返回 launcher 拷 .so：

```python
def _make_dumping_compile_kernel(original):
    """fxrt compile_kernel 前后各插一手：编译前落 kernel 源码，编译后拷 .so。

    编译逻辑仍归 fxrt/inductor_npu_ext。编译完成后 launcher._compiled 是
    NpuInductorKernel，其 lib_kernel/lib_wrapper 即 autofuse 产物路径，
    此时 kernel.so/wrapper.so 已就绪（compile_kernel 内部等完了编译 future）。
    """

    def compile_kernel(self, converter, defn_line):
        src_path = None
        if _dump_dir:
            from torch._inductor.codegen.wrapper import PythonWrapperCodegen

            code = PythonWrapperCodegen._format_kernel_definition(
                defn_line.kernel_name,
                defn_line.kernel_body,
                metadata=defn_line.metadata,
            )
            src_path = _dump_kernel(
                defn_line.kernel_name,
                "\n".join([converter.prologue, code]),
                defn_line.metadata,
            )
        launcher = original(self, converter, defn_line)
        if src_path:
            _dump_kernel_so(launcher, defn_line.kernel_name, src_path)
        return launcher

    return compile_kernel
```

改动二（事件 531）：`_dump_kernel` 改为返回路径，并新增 `_dump_kernel_so` 拷贝函数：

```python
def _dump_kernel_so(launcher, name: str, src_path: str) -> None:
    """把 AutoFuse 融合算子的编译产物拷到落盘目录，与源码同名配对。

    * kernel.so   设备侧融合 kernel（autofuse jit_compile 产物）
    * wrapper.so  host 侧 wrapper（加载 kernel.so、解析 tiling/launch）
    * autofuse_adapter.so  存在才拷（FX Converter runtime v2 需要的适配层）

    兼容缓存命中：lib_* 路径来自 NpuInductorKernel，命中时同样有效。
    """
    compiled = getattr(launcher, "_compiled", None)
    base = src_path[:-3] if src_path.endswith(".py") else src_path
    artifacts = [
        ("kernel.so", getattr(compiled, "lib_kernel", None)),
        ("wrapper.so", getattr(compiled, "lib_wrapper", None)),
        ("autofuse_adapter.so", None),
    ]
    for tag, src in artifacts:
        if tag == "autofuse_adapter.so":
            wrapper = getattr(compiled, "lib_wrapper", None)
            src = os.path.join(os.path.dirname(wrapper), tag) if wrapper else None
        if not src or not os.path.exists(src):
            logger.warning(f"[fxrt_fx] kernel artifact not found: {tag} ({src})")
            continue
        dst = f"{base}_{tag}"
        try:
            shutil.copy2(src, dst)
            logger.info(f"[fxrt_fx] saved {tag} of '{name}' -> {dst}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[fxrt_fx] failed to save {tag} of '{name}': {e}")
```

配套：`import shutil`（事件 534）；产物命名形如 `kernel_00000_autofused_add_where_4bbf..._kernel.so` / `..._wrapper.so`，与源码 `kernel_00000_....py` 同名配对。

## 机制与判别

- 结论：在模型侧既有 `AscendcBackend.compile_kernel` patch 上扩展：编译前落 kernel 源码（原有能力），编译后从返回 launcher 的 `_compiled`（NpuInductorKernel）取 `lib_kernel`/`lib_wrapper` 拷入 `FX_DUMP_DIR`、与源码同名配对，不改 inductor_npu_ext 即可按算子收集 AutoFuse 的 kernel.so/wrapper.so。
  - 机制：`compile_kernel` 返回 `_AscendcKernelLauncher`，其 `_compiled` 是 `NpuInductorKernel`（`inductor_npu_ext/compiler/_kernel.py:48`，事件 522），构造时 `self.lib_wrapper = wrapper; self.lib_kernel = kernel` 即 autofuse 产物路径；`compile_kernel` 内部等完编译 future，返回时 .so 已就绪；缓存命中时路径同样有效。
- 结论：实测单次运行收集 28 个融合算子共 56 个 .so（每算子 kernel.so + wrapper.so），模型正常跑完无 Traceback；日志行因双 logger handler 成对重复，56 条 adapter 缺失 warning 对应 28 个算子。
  - 计数口径：run 日志每条 INFO/WARNING 出现两次（事件 547/551/555 均可见成对重复），故 56 条 `kernel artifact not found: autofuse_adapter` warning = 28 个算子 × 2 次重复；56 个 .so = 28 算子 × (kernel.so + wrapper.so)，两口径互相印证。
- 结论：`autofuse_adapter.so` 在该 default 路径不生成（生成条件见 [autofuse_adapter.so 未生成的根因判别：requires_autofuse_adapter 标志探针（已装 wheel 落后于源码）](autofuse_adapterso_requires_autofuse_adapter_wheel.md)），收集钩子将其列为可选 artifact：缺失时静默跳过、存在时才拷贝；该静默化改动通过语法检查但未端到端复跑。
  - 事件 558 在 `autofuse_adapter.so` 分支加 `optional = True`（仅 kernel.so/wrapper.so 缺失才 warning），事件 562 仅 `python -m py_compile` 通过，未再跑模型验证，静默效果未实测。

## 验证信号

（平台：Atlas 910B3 + CANN 9.2.0；证据等级：会话内单次 run（run4）观测）

- 事件 547：`[fxrt_fx] saved kernel.so of 'autofused_add_where_4bbf199b1aa7b13c8a656f558fba0932' -> ../profiling/fx_capture/kernel_00000_autofused_add_where_4bbf199b1aa7b13c8a656f558fba0932_kernel.so` 日志与 `ls` 文件成对出现（kernel.so/wrapper.so 均在）。
- 事件 551：`ls ../profiling/fx_capture/*.so | wc -l` → 56；`grep -c Traceback` → 0；进程正常退出、`finished!`。
- 事件 555：`grep -c "kernel artifact not found: autofuse_adapter"` → 56；`kernel_00000_autofused_add_where_4bbf...` 三件齐全（.py 1282769B、_kernel.so 1103672B、_wrapper.so 85368B）。
- 事件 562：静默化改动后 `python -m py_compile fxrt_fx_wrapper.py` → `syntax OK`（仅语法级验证）。

## 适用与失效边界

- 仅 `FX_WRAPPER=1` 且 `FX_DUMP_DIR` 非空时生效；`--compile_backend=fxrt`/`torchair`（绕开 inductor host codegen）不适用。
- 依赖 torch_npu.fxrt 的 `fxrt.ascendc_fx_wrapper.AscendcBackend` 存在（无此子包的 torch_npu 在 `_patch_autofuse_backend()` 处抛 RuntimeError）。
- 覆盖 kernel.so/wrapper.so；`autofuse_adapter.so` 仅在 FX Converter runtime v2 路径（`requires_autofuse_adapter` 为真）生成时才会被额外拷贝。
- 收集计数为单次 run 观测；多 batch/多 graph/动态 shape 下编译算子数可能不同，未验证稳定性。
- 拷贝发生在 `compile_kernel` 返回处，若后续 tiling 变体在缓存目录中新增子产物（其他 tiling_hash 目录），不会自动同步收集。
