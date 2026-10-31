# Notify 管理 API

CANN Runtime Notify 与 CntNotify（计数型通知）管理接口：创建、记录、等待/重置、跨进程共享与白名单。

- [aclrtCreateNotify](aclrt_create_notify.md)：创建 Notify，支持 Host/Device 使用 flag。
- [aclrtDestroyNotify](aclrt_destroy_notify.md)：销毁 Notify。
- [aclrtRecordNotify](aclrt_record_notify.md)：在指定 Stream 上记录 Notify。异步接口。
- [aclrtWaitAndResetNotify](aclrt_wait_and_reset_notify.md)：阻塞 Stream 直到 Notify 完成并复位。异步接口。
- [aclrtGetNotifyId](aclrt_get_notify_id.md)：获取指定 Notify 的 ID。
- [aclrtNotifyBatchReset](aclrt_notify_batch_reset.md)：批量复位 Notify。
- [aclrtNotifyGetExportKey](aclrt_notify_get_export_key.md)：将 Notify 设为 IPC Notify 并导出共享名称 key。
- [aclrtNotifyImportByKey](aclrt_notify_import_by_key.md)：按 key 在本进程导入 IPC Notify。
- [aclrtNotifySetImportPid](aclrt_notify_set_import_pid.md)：设置共享 Notify 的进程白名单。
- [aclrtNotifySetImportPidInterServer](aclrt_notify_set_import_pid_inter_server.md)：设置共享 Notify 的进程白名单（A3 超节点场景）。
- [aclrtCntNotifyCreate](aclrt_cnt_notify_create.md)：创建利用计数值实现任务间同步的 CntNotify，计数范围为 1 至 UINT32_MAX；普通 Notify 仅支持计数值 1，仅 Ascend 950PR/950DT 支持 CntNotify。
- [aclrtCntNotifyDestroy](aclrt_cnt_notify_destroy.md)：销毁 CntNotify。
- [aclrtCntNotifyRecord](aclrt_cnt_notify_record.md)：在指定 Stream 上记录 CntNotify。异步接口。
- [aclrtCntNotifyWaitWithTimeout](aclrt_cnt_notify_wait_with_timeout.md)：阻塞 Stream 直到 CntNotify 完成。异步接口。
- [aclrtCntNotifyReset](aclrt_cnt_notify_reset.md)：将 CntNotify 计数值复位为 0。异步接口。
- [aclrtCntNotifyGetId](aclrt_cnt_notify_get_id.md)：获取 CntNotify 的 ID。
