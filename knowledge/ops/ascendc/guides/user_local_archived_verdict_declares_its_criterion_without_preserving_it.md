---
type: Guide
title: "要把归档的精度判定用在今天的候选上之前先问两件：判据字节还在吗？那次实际映射的是哪个库？"
description: "触发物=你打算复用一份归档 precision_report 的判定。两条必查：(1) bindings 里 comparator/profile/reference_worker 的 sha 只是【声明】——实测 2_GroupedMatmul 归档 5 份报告都声明同一组三件，而对该目录全部 84 个文件逐件 content-hash 后三件一个都不在 ⇒ 判定不可复算、精度只能记 UNBOUND_NOT_JUDGED；按 sha 去 hash，不要按文件名去 ls。(2) runtime_evidence.mapped_libraries[].sha256 是那次【实际映射】的库——归档 PASS 映射的是 25b2bead，而当前候选 DSO 是 f4565a84 ⇒ 不同构建，不能借那次 PASS；这比报告的candidate_digest 更直接，两者是不同的量。判据模块丢了但【查了什么】仍在逐例 metrics 里（eco-open-source / required_matched_ratio 0.9 / atol 1e-3 / rtol 1.220703125e-4 / max_abs_error_limit 0.01 / 四项 checks）⇒ 不要猜判据；且 eco 与 6e5 不能互换。拿到三件＋公共签名只关闭判据接线，当前候选的 P 仍须在原判据下实测。边界：extension_access 里的 cpython-312-x86_64 是【路径名】，不证明被映射库的 ELF 架构，没读 ELF 头不得断言。多次运行归档（harness2..6，passed 44/45/49/48/50，candidate_digest 互不相同，hardware_verified 仅末次 true，而 first_attempt_is_verdict 五份都有）⇒ 哪一次是行判定从字节判不出来，标未决交 schema 所有者。附带：wrapper 可能故意跳过 *.cpython-*.so（whl 打包的空 pybind 壳，注册不了算子），只加载无 tag 的 fat 库 ⇒ 目录里有 .so 不等于算子已注册。"
tags: [task.debugging, task.testing, topic.precision, topic.compilation]
status: draft
sources: []
created_at: "2026-10-27T06:07:44Z"
updated_at: "2026-10-27T06:09:00Z"
platforms: ["950"]
---

# 要把归档的精度判定用在今天的候选上之前先问两件：判据字节还在吗？那次实际映射的是哪个库？

> **来源说明（2026-10-31）**：本卡结论来自车队私有实测/推理，暂无可公开复核的原始出处；按社区评审口径以 draft 收录，待补可复核来源后回升。
> **来源与状态**：本卡结论全部来自本队**第一方实测**（catalog 52 / `2_GroupedMatmul`，A5/arch35），无可公开复核的外部出处 ⇒ `status: draft` 且 `sources: []`。卡内引用的该行性能结果已由 56 行基线表独立核对（`device_event` 全 50 几何平均 0.2691141087、绑定门 0.8 ⇒ F FAIL；候选 DSO `f4565a84c11b19267c21a5432cf12543a75226884cba91c1706c975d9eb57a41`；P 仍 `UNBOUND_NOT_JUDGED`，`precision_cases_measured=0`）。黑盒复现未做、本轮未做优化，二者单列保留。

## 当场自问（动作）

1. 报告的 `bindings` 里 `comparator_sha256` / `profile_sha256` / `reference_worker_sha256`
   是**声明**还是**字节**？—— 按这三个 sha 对归档目录做 content-hash，别看文件名。
2. `runtime_evidence.mapped_libraries[].sha256` 是多少？它与**今天**的候选 DSO 相同吗？
3. 归档里有几次运行？每次的 `candidate_digest` 相同吗？

## 机制一：声明 ≠ 保存，于是判定不可复算

`precision_report.json` 的 `bindings` 会逐一声明判据三件套的 sha256。**这只是声明。**
实测（2_GroupedMatmul / A5 port_light 归档，5 份 harness 报告）：三件套的 sha 在
**每一份**报告里都一致声明，而对该归档目录**全部 84 个文件**逐件 content-hash 后，
**三件一个都不在**；在的只有报告自己。
⇒ 后果：**判定无法复算，精度无法重新绑定**。这不是 FAIL 也不是 PASS，是
`UNBOUND_NOT_JUDGED`。
⇒ 判据：`missing_*_sha256` 这类字段要当成**取件清单**，不是"已归档"的证明。
按 sha 去 hash，而不是按路径/文件名去 `ls`。

## 机制二：判据模块丢了，但"查了什么"还在

模块字节没了，它**产出的口径**仍留在逐例 `metrics` 里，可直接读出来：

```
standard eco-open-source   kind floating   required_matched_ratio 0.9
atol 0.001   rtol 0.0001220703125
small_value_threshold 6.103515625e-05
eco: atol 1.52587890625e-05  rtol 0.0009765625  max_abs_error_limit 0.01
checks: max_error_cap / required_matched_ratio / MERE / nonfinite
```

⇒ **不要猜判据**；它在 metrics 里。但注意这是 **eco** 家族：eco 与 6e5 比较器 keying
的侧不同、且不共享 MARE 判据 ⇒ 字节到手后**不能互相替换**。
⇒ 同时记清边界：拿到三件＋公共调用签名只**关闭判据接线**；
**当前候选的 P 仍需在原判据下实测**（设备工作），不是 CPU 能完成的。

## 机制三：用 mapped_libraries 判"这个判定属于谁"，而不是信 status

`runtime_evidence.mapped_libraries[]` 记的是那次运行里**实际被映射**的库及其 sha256。
实测：归档 PASS 那次映射的是 `25b2bead…`，而当前候选 DSO 是 `f4565a84…` ⇒ **不同的构建**
⇒ **不能把那次 PASS 借给今天的候选**。这一条本身就足以下结论。
⇒ 这比报告里的 `candidate_digest` 更直接：两者是不同的量，别互相替代。

⚠️ **边界（我踩过）**：同一段里的 `extension_access` 路径名含 `cpython-312-x86_64`，
**路径名不证明被映射库的 ELF 架构** —— 没读 ELF 头就不能断言架构，尤其那份库在无权访问的主机上。
mapped sha 不同已足够，不需要也不应再加一条未核的架构主张。
相关但不同机制：`ol_244` 用 `*.cpython-3XX-*.so` 标签判**构建/运行期解释器错配**的失败签名；
本卡说的是**归档证据的归属**，两者别混。

## 机制四：多次运行的归档，"哪一次是行判定"可能无法从字节确定

实测该归档有 harness2..6 五次，`passed_cases` 44 / 45 / 49 / 48 / 50，status 仅最后一次 PASS，
且**五次的 `candidate_digest` 互不相同**（是迭代序列，不是同一候选复测）；
`hardware_verified` 仅最后一次为 true。
而 `first_attempt_is_verdict: true` **五份都有** ⇒ 它到底指"本次运行内无重试"还是
"五次里第一次才是行判定"，**从这些字节判不出来**，而这会改变归档判定是哪一个 status。
⇒ 处置：**标为未决、交 schema 所有者**，不要自己挑一个 status 当行判定。

## 附带一条独立事实：扩展 .so 存在 ≠ 算子已注册

该行候选 wrapper 的 `_load_extension` **故意跳过 `*.cpython-*.so`**，其自述理由是 whl 打包产出的
那个是**空 pybind 壳、注册不了任何算子**，先加载它会让 `torch.ops.npu.<op>` 保持未注册；
它只加载**无 tag 的 fat 库**。
⇒ 判据：选 DSO 时按 wrapper 实际加载的那一类选；"目录里有个 `_<op>_ext*.so`"不构成可用候选。
⇒ 注意与 `ol_244` 的用法相反方向：那张卡里 cpython tag 指示的是**可执行扩展的错配**，
这里 cpython tag 指示的是**空壳**。同一命名在两条路径上含义不同，按实际打包路径判。

## 完整摘要（本卡讲的就是身份，所以这里给 64 位全值，不给前缀）

正文里的 8 位缩写只为可读；**核对一律用下表**。截断的 SHA-256 前缀不得写进身份字段——
32 个十六进制字符正好是 MD5 长度，日后会被当 MD5 读。

| 对象 | sha256 |
|---|---|
| 归档 PASS 那次**实际映射**的扩展 | `25b2bead13730f9a21d21ca7c7f92d6ddf800b333f55b879feec36a54d117d67` |
| 当前候选 DSO | `f4565a84c11b19267c21a5432cf12543a75226884cba91c1706c975d9eb57a41` |
| 声明但未保存：comparator | `403aa3426425de8a39ecda767c3ad6ad20c0e0a9cb20458ca97e855293002b15` |
| 声明但未保存：profile | `78ba3dc9198f5fa7b44abe39928cef8cd17e53644953fb654e1ca03c14044c5c` |
| 声明但未保存：reference worker | `3651a6efdd6fbb89517fdadb0c3d027e0b2edd5266761c62c5dbdaf59b4d405a` |
| 唯一在归档里的那一份（harness6 报告） | `4ad808ac2dab8bae6efe944de66651968200015e3f4d2fc9828ca79a4bab0d09` |

## 作用域

- 实测来源：catalog 52 = `2_GroupedMatmul`，A5/arch35，候选 DSO `f4565a84…`，
  归档 `0928_950pr_port_light_cjm/2_GroupedMatmul/runs_evidence/harness{2..6}`。
- 本卡只讲**归档证据的可复算性与归属**；不含任何性能结论。该行 F 另有独立结果
  （全 50 device_event GM `0.269114109` < 0.8，FAIL），与本卡无关。
- 未做：黑盒复现；本轮未做优化也不声称。

## 相关卡（相邻、机制不同）

- [Unsupported soc version 是 torch_npu / cpython 构建错配](../runbooks/compilation/ol_244_unsupported_soc_version_build_mismatch.md) —— 正文机制三里提到的那张。那张用 `*.cpython-3XX-*.so` 标签判**可执行扩展的构建/解释器错配失败签名**；本卡的 cpython 标签指的是 whl 打包的**空 pybind 壳**。**同一命名在两条路径上含义相反**，按实际打包路径判，别互换。
- [load-binding 写成自由文本不标记它伴随的那个数](../runbooks/validations/load_binding_needs_explicit_eligibility_field.md) —— 同属「收据里的绑定不足以支撑它旁边那个数」这一族,但机制不同：那张讲收据**缺少显式 eligibility 字段**；本卡讲判据字节**声明了却没保存**,以及用 `mapped_libraries[].sha256` 判归属。两者可互为参照,不重复。
