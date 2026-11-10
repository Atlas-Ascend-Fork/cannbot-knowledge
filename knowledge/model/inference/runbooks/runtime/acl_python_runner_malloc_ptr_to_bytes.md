---
{
  "type": "Runbook",
  "title": "ACL Python 绑定 OM runner 签名探针：malloc 元组返回与 ptr_to_bytes 设备指针段错误定位",
  "description": "CANN 9.3.0 的 ACL Python 绑定（acl.so）多数调用返回 (值, ret) 元组且参数个数固定（rt.malloc 必须两参）；util.ptr_to_bytes 直接读设备指针会段错误且缓冲 stdout 丢失。用 stderr 无缓冲逐行打点可把崩溃点定位到 ptr_to_bytes，再用 malloc_host+memcpy(dev→host) 取回数据；get_output_dims 返回 (dict, ret)。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "a3"
  ]
}
---

# ACL Python 绑定 OM runner 签名探针：malloc 元组返回与 ptr_to_bytes 设备指针段错误定位

## 适用场景

- 平台/版本：Ascend910_9362（ACL 逻辑卡 0）、CANN 9.3.0 的 ACL Python 绑定（`$ASCEND_HOME_PATH/python/site-packages/acl.so`）、Python 3.11.4（aarch64）。
- 场景：自研 ACL Python OM 推理 runner——`mdl.load_from_file → create_desc/get_desc → create_dataset → create_data_buffer → add_dataset_buffer → execute → 输出取回`。
- 缺失信息：本轨迹未核对 ACL Python 官方文档；以下签名与约束全部来自同机实测探针，未见文档佐证。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

- 触发 1（事件 429/430）：`dev_ptr, ret = acl.rt.malloc(size)` → `TypeError: acl.rt.malloc args parse failed`。
- 触发 2（事件 443/447）：按 `(ptr, ret)` 解包后，`add_dataset_buffer` 处 `_check` 失败：`RuntimeError: ACL call failed: add_dataset_buffer -> ret (187651020291920, 0)`——该调用返回值是 `(id, 0)` 二元组而非 ret 整数。
- 触发 3（事件 453/454）：探针进程 `Segmentation fault`，且重定向到文件的 stdout 全部丢失（缓冲未刷出）。
- 观测（事件 436/437、475/476）：`acl.rt.malloc(1024, 0)` → `(20619064328192, 0)`；`acl.mdl.get_output_dims(desc, 0)` → `({'name': '/Add:0:4', 'dimCount': 2, 'dims': [2, 2]}, 0)`。

## 探针与操作

崩溃定位探针（事件 460，`print(..., file=sys.stderr, flush=True)` 无缓冲逐行打点）：

```
cat > ${LOCAL_PATH_1} <<'EOF'
import sys, acl
def log(*a): print(*a, file=sys.stderr, flush=True)
acl.init(); acl.rt.set_device(0)
ds = acl.mdl.create_dataset()
p, r = acl.rt.malloc(64, 0); log("malloc ok", r)
buf = acl.create_data_buffer(p, 64); log("create_data_buffer ok", type(buf))
res = acl.mdl.add_dataset_buffer(ds, buf); log("add_dataset_buffer ->", res)
log("num_buffers:", acl.mdl.get_dataset_num_buffers(ds))
b2 = acl.mdl.get_dataset_buffer(ds, 0); log("get_dataset_buffer ->", type(b2))
addr = acl.get_data_buffer_addr(b2); log("addr ->", addr)
sz = acl.get_data_buffer_size(b2); log("size ->", sz)
hb = acl.util.ptr_to_bytes(addr, sz); log("ptr_to_bytes len:", len(hb))
ptr2 = acl.util.bytes_to_ptr(hb); log("bytes_to_ptr ->", ptr2)
r2 = acl.rt.memcpy(addr, sz, ptr2, sz, 2); log("memcpy dev->host-copyback:", r2)
acl.rt.free(p); log("freed")
acl.destroy_data_buffer(buf); log("destroy_data_buffer ok")
acl.mdl.destroy_dataset(ds); log("destroy_dataset ok")
acl.rt.reset_device(0); acl.finalize(); log("done")
EOF
python3 ${LOCAL_PATH_1} 2>&1 >/dev/null | grep -vE "^\[INFO\]|ATRACE|^\[W" | head -20
```

结果（事件 461）：打点止于 `size -> 64`，`ptr_to_bytes` 行及之后全部缺失——崩溃点即 `hb = acl.util.ptr_to_bytes(addr, sz)`，其中 `addr` 是设备指针。

正确内存流探针（事件 464）：

```
cat > ${LOCAL_PATH_2} <<'EOF'
import sys, acl
def log(*a): print(*a, file=sys.stderr, flush=True)
acl.init(); acl.rt.set_device(0)
ctx, r = acl.rt.create_context(0); log("ctx", r)
ds = acl.mdl.create_dataset()
p, r = acl.rt.malloc(64, 0)
buf = acl.create_data_buffer(p, 64)
_, r = acl.mdl.add_dataset_buffer(ds, buf); log("add", r)
b2 = acl.mdl.get_dataset_buffer(ds, 0)
addr = acl.get_data_buffer_addr(b2); sz = acl.get_data_buffer_size(b2)
# write known bytes host->dev
payload = bytes(range(64))
hptr = acl.util.bytes_to_ptr(payload)
r = acl.rt.memcpy(addr, sz, hptr, 64, 1); log("memcpy h->d", r)
# alloc host mem and copy dev->host
hp, r = acl.rt.malloc_host(64); log("malloc_host", r, type(hp))
r = acl.rt.memcpy(hp, 64, addr, sz, 2); log("memcpy d->h", r)
data = acl.util.ptr_to_bytes(hp, 64); log("ptr_to_bytes len", len(data), "first:", list(data[:8]))
acl.rt.free_host(hp); log("free_host ok")
acl.rt.free(p); acl.destroy_data_buffer(buf); acl.mdl.destroy_dataset(ds)
acl.rt.destroy_context(ctx); acl.rt.reset_device(0); acl.finalize(); log("done")
EOF
python3 ${LOCAL_PATH_2} 2>&1 >/dev/null | grep -vE "^\[INFO\]|ATRACE|^\[W" | head -15
```

结果（事件 465）：`ctx 0 / add 0 / memcpy h->d 0 / malloc_host 0 / memcpy d->h 0 / ptr_to_bytes len 64 first: [0, 1, 2, 3, 4, 5, 6, 7] / free_host ok / done`——全程无崩溃，数据逐字节一致。

形状提取探针（事件 475）：`get_output_dims` 返回 `(dict, ret)`；另有失败对照（事件 471/472）：把返回值直接当 dict 用产生 `output_00.bin: 4 values do not match shape []`。

ACL Python 绑定的返回约定：acl.rt.malloc 必须带 (size, policy) 两参并返回 (ptr, ret)，单参调用直接 TypeError: acl.rt.malloc args parse failed；acl.mdl.add_dataset_buffer 返回 (id, ret) 二元组；acl.mdl.get_output_dims 返回 (dims_dict, ret)，维度在返回 dict 的 "dims" 键。

acl.util.ptr_to_bytes 只能用于主机指针：直接读设备指针会在该调用处段错误，进程崩溃且重定向到文件的 stdout 全部丢失；用 print(..., file=sys.stderr, flush=True) 逐行打点可把崩溃点定位到 ptr_to_bytes 行——其前的 malloc、create_data_buffer、add_dataset_buffer、get_data_buffer_addr、get_data_buffer_size 打点全部正常输出。

设备数据取回的正确链路：rt.create_context → rt.memcpy(host→dev, kind=1) → rt.malloc_host + rt.memcpy(dev→host, kind=2) → util.ptr_to_bytes(主机指针)；实测 64 字节 host→dev→host 往返逐字节一致（first: [0, 1, 2, 3, 4, 5, 6, 7]）。

## 机制与判别

- 判别 1（段错误根因）：崩溃由 `ptr_to_bytes` 读设备指针引起，而非 dataset/buffer API——打点顺序证明此前所有 buffer 调用成功（事件 461）；同一 `ptr_to_bytes` 对 `malloc_host` 主机指针正常返回（事件 465）。指针类别（host/device）是唯一判别变量。
- 判别 2（返回约定）：ACL Python 绑定把 `(输出值, ret)` 打包成元组返回，调用方必须解包再判 ret；把元组整体当 ret 会把成功误判为失败（事件 447 的 `ret (187651020291920, 0)`）。
- 判别 3（崩溃信息保全）：段错误会吞掉缓冲 stdout，`file=sys.stderr, flush=True` 的无缓冲打点是保留崩溃前观测的可用手段（事件 454 → 461 的对照）。
- 收敛验证（事件 468/483/490）：按上述签名重写的 runner（`_check` 兼容元组 ret、malloc 双参、host 中转取回、`get_output_dims` 解元组取 dict）经 `run_om.py` 在 NPU 上跑通 baseline/optimized 两个 OM 并产出可比输出（max abs diff = 0.0）——上述签名结论在真实推理路径上复用有效。

## 验证信号

全部为单次会话内单次探针观测，Ascend910_9362 / CANN 9.3.0 / Python 3.11.4：

- 事件 437：`malloc(size, policy) -> (ptr, 0)`；单参形式 TypeError（事件 430）。
- 事件 447：`add_dataset_buffer -> (187651020291920, 0)`（元组返回的直接证据）。
- 事件 454/461：段错误 + 无缓冲打点定位崩溃点在 ptr_to_bytes。
- 事件 465：64 字节 host→dev→host 往返逐字节一致（first: [0, 1, 2, 3, 4, 5, 6, 7]）。
- 事件 476：`get_output_dims -> ({'name': '/Add:0:4', 'dimCount': 2, 'dims': [2, 2]}, 0)`。
- 事件 483/490：终版 runner 跑通两个 OM，输出可比（max abs diff = 0.0）。

## 适用与失效边界

- 覆盖面：仅本轨迹实际探测的子集——`rt.malloc/malloc_host/free/free_host/memcpy/create_context/destroy_context`、`mdl.create_dataset/destroy_dataset/create_desc/get_desc/load_from_file/unload/get_num_inputs/get_num_outputs/get_input_size_by_index/get_output_size_by_index/get_output_name_by_index/get_output_dims/get_output_data_type`、模块级 `create_data_buffer/get_data_buffer_addr/get_data_buffer_size`、`mdl.add_dataset_buffer/get_dataset_buffer/get_dataset_num_buffers`、`util.ptr_to_bytes/bytes_to_ptr`。
- 未验证：`mdl.execute/execute_async` 的返回形态（runner 内使用但未单独探针签名）、流/事件、其余 dtype 映射完备性。
- "ptr_to_bytes 禁止设备指针"来自一次崩溃定位 + 一次主机指针对照，无官方文档佐证；若要写进产品代码建议以 host 中转为唯一路径。
- 版本边界：结论绑定 CANN 9.3.0 的 acl.so；后续版本若调整绑定返回约定需重跑探针（事件 436/460/464/475 的探针可直接复用）。
