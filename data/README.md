# 数据来源与划分

- 原始来源：`yogape/logistics-operations`（合成物流业务数据；原数据卡注明 MIT 许可）。
- 从清洗后的业务记录生成 Task A 信息提取和 Task B 延误判断指令。
- E1／E2／E3 训练指令：1,600／4,000／8,000；固定 Val 1,000；最终 Test 2,000。
- E1 是 E2 的子集，E2 是 E3 的子集；Val 和 Test 与 Train 按业务记录隔离。
- `phase1_dataset_info.json`、`phase4_dataset_info.json` 和 `phase5_training_manifest.json` 记录生成设置、数量和源文件哈希。
- 此处的 `val.jsonl` 与 Phase 5 训练包中的固定 Val 字节一致。`checksums.sha256` 记录本发布副本各文件哈希。
- Phase 4 元数据说明旧 Val 样本保留在扩展 Val 中。E1 的最佳 checkpoint 曾用旧 Val 200 选择，因此扩展 Val 的 E1 成绩并非完全未见过的独立验证；最终 Test 在选定 E1 后报告。

数据来源：https://huggingface.co/datasets/yogape/logistics-operations
