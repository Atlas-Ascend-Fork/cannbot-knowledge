# Cube分组管理（ISASI）

- [CubeResGroupHandle](cube_res_group_handle/index.md)：AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图 !
- [GroupBarrier](group_barrier/index.md)：通知其他等待的AIV，本AIV已经完成其依赖的任务。
- [KfcWorkspace](kfc_workspace/index.md)：用于创建KfcWorkspace对象，Kfc全称为kernel function call，表示核间通信调用。
