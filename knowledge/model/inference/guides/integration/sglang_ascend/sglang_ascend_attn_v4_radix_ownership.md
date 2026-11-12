---
type: Guide
title: SGLang Ascend V4 C128前缀共享：完整页边界与HiCache恢复
description: 说明只有完整C128页组进入radix、节点拆分与引用计数，以及host-only命中加载后刷新请求sidecar的必要性。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/c128_sidecar_component.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_req_to_token_pool.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_allocator.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/registry.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/hybrid_cache/hybrid_pool_assembler.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/memory_pool_host.py
  role: implementation
created_at: '2026-11-08T12:07:57Z'
updated_at: '2026-11-08T12:20:16Z'
platforms: []
aliases:
- C128SidecarComponent
- C128 radix HiCache
---

# SGLang Ascend V4 C128前缀共享：完整页边界与HiCache恢复

## 共享单位

C128 sidecar只把完整物理C128页暴露给unified radix tree，尾部部分页保留request所有。一个可共享边界为G=128*c128_page_size个原始token；插入新长叶时逐个物化完整G边界，避免后续分支只能退回更早的大节点。Eagle缓存长度先减去附加token再向下对齐，返回时按协议加回。

attach克隆页号并retain；node split不把一个旧端点页随意迁到中间新节点，session保护沿路径维护。已有待执行SWARebuild若被C128拆节点，必须同步拆成两个动作，保持full/SWA与sidecar边界一致。

## 命中与回收

普通match允许device或host驻留，device-only要求device value。请求sidecar从命中路径收集device页；host-only命中在load-back commit前没有device页，恢复成功后必须再次收集并刷新sidecar，不能继续使用早先的不完整表。SWA branching候选向下对齐到最近G边界。

device页靠retain/release refcounts，不靠FULL path lock独占；device驱逐只是归还引用。C128是FULL的必需辅助载荷，不增加对外报告的token驱逐数。host值没有refcount，host锁和host_lru另行管理，驱逐后仍有host copy要进入host_lru。

## HiCache传输

备份将每page扩为page*P+arange(P)的独立C128索引，controller单独分配host槽。load-back沿路径汇集host段，commit时将扩展device slot除P并unique恢复物理页号后retain；不能对P份重复page id逐项retain，否则引用数膨胀。commit前rollback由controller释放，commit后由tree eviction释放。

建议检查部分尾页不共享、完整边界分支、host-only恢复、session保护与备份/驱逐竞态后的驻留和计数。完整页对齐可能牺牲短尾命中率，换取稳定所有权；本次未执行缓存/传输测试，本文不替代通用PD/HiCache部署说明。

## 调用依赖补充

注册过程看到req_to_c128_sidecar才额外安装C128 tree slot并绑定C128SidecarComponent，不能只构建sidecar表而遗漏tree组件。Host组装中FULL作为逻辑anchor，C4仍用FULL坐标；NPU C128采用独立device allocator页数×hicache_ratio计算host页数，slot_page_size取native PA_ND的kernel page槽数（如16），不能用FULL页数或全局page_size（如128）代替。该V4组装拒绝--hicache-size，要求--hicache-ratio。

C128 entry绑定独立alloc/free回调与FULL叶host驱逐回调，C128 state本身不注册HiCache；state的PD传输与KV的HiCache驻留协议不同。备份/恢复验收须同时观察Host容量、独立索引和tree引用，不以逻辑FULL命中数代替C128恢复完成。


## Host页与state ring的物理换算

DeepSeekV4PagedHostPool按layer_num×num_host_pages×item_bytes检查Host预算，再按layer_first/page_first/page_first_direct组织字节。NPU传输视图将每层Host页解释为[host_pages,1,native_page_size,1,D]，device视图为[1,device_pages,native_page_size,1,D]。逻辑slot索引先按slot_page_size分组、首项整除得到逻辑page，再展开page*native_page_size+arange(native_page_size)供kernel_ascend的transfer_kv_dim_exchange使用；不能直接把逻辑token索引送入PA_ND搬运。空传输无操作，Host/device索引数量必须相同。

StateHostPool复用SWA传输索引，没有独立alloc/free；所有层的ring_size和state_page_bytes必须一致。SWA索引数量需整除page_size，取page row后展开row*ring_size+arange(ring_size)，Host视图的第三维是ring_size而不是KV native page槽数。state ring行与普通KV page展开不能混用。

两个Host池选择ALLOC_MEMORY_FUNCS时都先把torch.device规范为device.type字符串（或保留字符串）；直接以torch.device对象查字符串键会意外落到cudaHostRegister默认allocator并在NPU失败。预算、allocator、dtype解释和物理索引需成套验收。本次未分配Host内存或执行传输。
