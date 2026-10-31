# Label 管理 API

CANN Runtime Label 管理接口：标签创建、设置、销毁及基于标签索引的 Stream 跳转。

- [aclrtCreateLabel](aclrt_create_label.md)：创建标签，每个进程最多 65535 个。
- [aclrtSetLabel](aclrt_set_label.md)：在 Stream 上设置标签。
- [aclrtDestroyLabel](aclrt_destroy_label.md)：销毁标签。
- [aclrtCreateLabelList](aclrt_create_label_list.md)：创建标签列表。
- [aclrtDestroyLabelList](aclrt_destroy_label_list.md)：销毁标签列表。
- [aclrtSwitchLabelByIndex](aclrt_switch_label_by_index.md)：根据标签索引跳转执行对应 Stream 上的任务。异步接口。
