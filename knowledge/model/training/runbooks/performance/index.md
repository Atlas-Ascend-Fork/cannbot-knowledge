# 模型训练性能优化

- [torch._foreach_copy_ 的 fast/slow path 判别与 host 派发收益边界](foreach_copy_fast_slow_path_dispatch.md)：ATen/CUDA foreach copy 的形状限制是 self[i]/src[i] 逐对匹配，不要求列表内所有参数同形；异形 FSDP 参数本身不能判定 slow path。CPU/device offload 因设备不同不满足所读 CUDA fast path 的同设备条件；已进入 slow path 时才有逐对 copy_ 调用，实际 host 收益和 DMA 数需运行测量。
