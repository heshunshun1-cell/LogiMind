# Phase 6 证据说明

Phase 0 是环境与基座试跑；Phase 1 记录数据构建；Phase 2 的基线评测使用旧 Val 200（A/B 各 100）。下面的四方法对比使用扩展后的 Val 1,000（A/B 各 500），两组数字须分别标注数据范围。

可在整理稿根目录运行 `python scripts/verify_results.py`，从已保存预测复算四方法 Val、E1/E2/E3 Val、E1 Test，并检查数据划分与关键哈希。Phase 3 的旧 Val 200 预测及指标保存在 `results/training/`；Phase 2 的原始逐题预测未包含在此整理包，旧基线指标暂由原 Notebook 文字与代码记录支持。

## 四方法统一 Val

Phase 4 保存的 Zero-shot、Few-shot、E1 LoRA 各有 1,000 条逐题预测，均与同一 Val 样本编号对齐；Rule 由原题中的计划时间与实际时间复算，仅适用于 Task B。

| 方法 | Task A 严格 JSON | Task A 字段 | Task B 正确数 |
|---|---:|---:|---:|
| Rule | 不适用 | 不适用 | 500/500 |
| Zero-shot | 1/500 | 7/4000 | 334/500 |
| Few-shot | 500/500 | 3963/4000 | 311/500 |
| E1 LoRA | 500/500 | 4000/4000 | 497/500 |

严格评分直接解析原始回答。Zero-shot 去掉完整 Markdown 代码围栏后，Task A 字段为 3759/4000（仅作辅助分析）。Phase 4 LoRA 预测 SHA-256 为 `02e6e5bbdf487e74903d18f0ba3ba3ad0f0537708cdb9bf650f2e5394369bbe3`，与 Notebook 输出一致。

## E1、E2、E3 的训练配置与结果

E1/E2/E3 的 Task B 四种训练模板各占 25%。E1 在 Test 两种时间顺序模板上均为 500/500。E3 的 Val 错误集中于 `validation_B_2` 是观察结果，模板数量不能证明成因。

Phase 3 训练代码为 E1 手工构造答案标签：提示 token 的标签为 `-100`。E2/E3 以完整对话文本训练，并显式关闭 assistant-only 与 completion-only loss。E1 与 E2/E3 的 loss 计算范围不同，不能将 loss 数值直接比较，也不能将结果差异单独归因于训练规模。原始 Phase 5 报告保留作为历史实验记录；本说明补充其解释边界。

Phase 4 四方法推理设置为确定性生成、最多 384 个新 token。Phase 5 E1/E2/E3 统一 Val 和 E1 最终 Test 使用按任务设置的上限（A 192、B 48）。同一模型的两次评测结果一致，但这不是同一次生成；四方法比较应引用 `results/phase4/` 原始逐题预测。

`results/phase5/final_model_selection.json` 的 `test_status` 保留了选型时“尚未测试”的状态；`results/phase5/E1_final_test_metrics.json` 是后续 Test 结果，不应改写前者。

三个 adapter 的配置分别位于 `results/training/E1_adapter_config.json` 等文件；原始权重不在此整理稿，哈希见 `results/training/adapter_weights_sha256.json`。原始数据快照的哈希已记录，但模型基座 revision 未固定，不能保证不同时间重新下载得到逐字节一致的环境。

## 运行状态

当前 Notebook 保留原始 Colab 路径和原 ZIP 文件名，仓库草稿没有包含原始物流数据 ZIP、基座模型或 adapter 权重。因此可以离线复算已保存的关键指标，但不能仅凭这个整理包从 Phase 1 一键运行到 Phase 5。运行说明与依赖整理属于后续发布步骤。

## 局限

单随机种子；合成且同来源的数据；Task B 只涉及给定时间的延误判断；人工困难样本为探索性压力测试。

## 困难样本归档

按 Phase 4 Notebook 的生成代码恢复了 100 道题目，文件 SHA-256 与原记录一致。逐题预测已归档。Task A 字段 400/400，Task B 正确 45/50，与原 Notebook 输出相符。原推理配置文件尚待核对。
