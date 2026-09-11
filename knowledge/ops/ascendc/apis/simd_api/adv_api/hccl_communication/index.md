# HCCL通信类

- [HCCL Context](hccl_context/index.md)：获取指定Index通信域的context（消息区）地址。
- [HCCL核函数（Kernel）侧接口](hccl_kernel/index.md)：集合通信算子AllGather的任务下发接口，返回该任务的标识handleId给用户。AllGather的功能为：将通信域内所有节点的输入按照rank id重新排序，然后拼接起来，再将结果发送到所有节点的输出。 !
- [HCCL Tiling侧接口](hccl_tiling/index.md)：获取Mc2InitTiling参数和Mc2CcTiling参数。
