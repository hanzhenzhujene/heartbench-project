# HeartBench-v2 人工 Relabel 简明说明

请使用这个文件进行人工标注：

- `benchmark/heartbench_v2_relabel_blind_template.csv`

不要使用下面这个文件做初次人工标注，因为它包含当前 heuristic 标签，会污染判断：

- `benchmark/heartbench_v2_relabel_adjudication_template.csv`

## 你需要填写的列

- `annotator_id`
- `review_round`
- `annotated_gold_heart_worse`
- `annotated_gold_act_worse`
- `annotated_gold_case_A_heart_score`
- `annotated_gold_case_B_heart_score`
- `annotated_gold_case_A_act_score`
- `annotated_gold_case_B_act_score`
- `annotation_confidence`
- `needs_discussion`
- `notes`

## 允许填写的值

- `annotated_gold_heart_worse`: `A` / `B` / `tie`
- `annotated_gold_act_worse`: `A` / `B` / `tie`
- 四个 case-level score: 只能填 `1` / `2` / `3` / `4` / `5`
- `annotation_confidence`: `low` / `medium` / `high`
- `needs_discussion`: `yes` / `no`
- `notes`: 可空

## 评分标准

### Heart

看内在 moral orientation，不看表面行为是否体面：

- motive
- posture
- resentment
- contempt
- manipulation
- mercy
- pride
- humility
- self-seeking

### Act

只看 outward action / omission / restraint / correction：

- 外在做了什么
- 行为本身是否 harmful / deceptive / negligent / constructive
- 不要把动机直接折进 act，除非它改变了外在行为本身

## `1-5` 含义

- `1` = clearly good / sound
- `2` = somewhat good
- `3` = mixed / unclear / intermediate
- `4` = somewhat bad / disordered
- `5` = clearly bad / corrupt

## 回传给我时

把你填好的这个文件发回即可：

- `benchmark/heartbench_v2_relabel_blind_template.csv`

如果你不方便直接发文件，也可以把 CSV 内容贴给我，我来导入。
