# 故障处置

- [运行故障](runtime/index.md)：共 20 张知识卡（本批新增：训练侧运行/环境/启动故障的轨迹沉淀，如 Mooncake 共享段默认值、custom_op Optional-in-tuple 注册、容器 EBUSY 分层定位、HiF8 训练启动器 CPU 预检等）。

- [模型训练编译与构建排障](compilation/index.md)：共 3 张知识卡（如 inductor_npu_ext 放开 sigmoid_backward decompose 白名单并双环境同步验证、inductor 图输出身份决定 realize 时机：`sigmoid_1` 不在 return 里时 RMSNorm 链算两份（--check 结构性假阴性根因））。
- [模型训练性能优化](performance/index.md)：ATen/CUDA foreach copy 的形状限制是 self[i]/src[i] 逐对匹配，不要求列表内所有参数同形；异形 FSDP 参数本身不能判定 slow path。CPU/device offload 因设备不同不满足所读 CUDA fast path 的同设备条件；已进入 slow path 时才有逐对 copy_ 调用，实际 host 收益和 DMA 数需运行测量。
- [模型训练精度排障](precision/index.md)：CANN 0923 的 torchtitan-npu 双跑中，摘掉 aten.sigmoid 白名单的 golden 梯度有限，原白名单 check 的 mul_934 出现 NaN；可按 FX 名找到其 producer。sum_30 两侧签名均有限，sigmoid_1 仅 check 侧有限、golden 签名缺失，不能称为双侧通过。需使用新缓存并核对 logger、FX 名和采集覆盖，缺失签名不得按 nan=0 处理。
- [模型训练验证方法](validations/index.md)：共 6 张知识卡（如 rollout dump 的采样 token surprisal 分桶：均值下降、百分比舍入与判读边界、sigtrace CULPRIT 误报判读：首条 nan_count 行、同配置噪声底与 logger 门控）。
