# Qualisys CAST 下肢标记与补点工作交接

## 1. 任务目标

本任务不是简单地把动态试次补到“每帧 28 个点”，而是要得到一份可以继续用于 Visual3D 的 CAST Lower Body 数据：

- 静态试次的 36 个点身份、左右侧颜色和连线正确；
- 动态试次使用正确的 28 个 tracking marker；
- 每个动态点对应静态试次中同名、同一物理位置的标记；
- TH、SK 四点刚体板的标签顺序正确，连线不交叉、不接错点；
- 内部缺点使用同一刚体板的可靠点做 relational 补点；
- 修复后的轨迹在位置、速度和刚体几何上连续；
- 原始采集文件和用户人工完成的静态文件不能被覆盖。

最重要的原则：**点的位置看起来差不多、每帧点数达到 28，都不能单独证明修复正确。点的身份和 CAST 连线必须同时正确。**

## 2. 数据位置与文件身份

### 2.1 数据目录

```text
C:\Users\Admin\Documents\FOUR_FORCE_Plates\Data\li_wenyan li_2026-09-08_1\2026-09-08\CAST - Lower body_Esp32FlexSensor
```

### 2.2 权威静态试次

用户人工补完并确认的静态文件：

```text
Static LB Anterior - CAST 2.qtm
```

工作输出目录内还有一份副本：

```text
Labeled_Output_v7_Relational\Static LB Anterior - CAST 2_user_completed.qtm
```

静态文件是本受试者的标签身份、颜色、bone topology 和刚体几何基准。CAST PDF 或 AIM 模型只能辅助理解，不能覆盖用户已经确认的静态点位。

### 2.3 重点动态试次

用户重点指出的问题文件：

```text
Labeled_Output_v7_Relational\Gait LB - CAST 6_complete28_relational.qtm
```

用户说明：`CAST 10` 就是 `CAST 6`，只是改了名字。处理时不要把它们当成两个独立采集试次，也不要重复生成两套互相冲突的结果。

### 2.4 已生成的候选文件

```text
Labeled_Output_v7_Relational\Gait LB - CAST 6_complete28_relational_RTH_fixed.qtm
```

这个文件只能视为 **R_TH 候选修复结果**，不能仅凭文件名中的 `fixed` 判定已经可交付。必须重新打开并完成第 11 节的验证，尤其要检查 QTM 显示帧 493 至 523 附近的 R_TH 连线和刚体距离。

### 2.5 中间分析目录

```text
C:\Users\Admin\qtm_mapping_work
```

该目录包含历史分析 JSON、临时 QTM、截图和脚本。它们可以用于追溯，但不是新的 ground truth。重要文件包括：

```text
verify_v7_gait6.json
gait6_v7_relational.json
gait6_qtm_report2.txt
audit_gait6.json
fix_gait6_rth1.py
refine_gait6_rth.py
frame497_rth_fixed.png
```

## 3. CAST 点数与标记集合

### 3.1 静态 36 点

静态 CAST Lower Body 通常是 36 点。除动态 tracking marker 外，还包含用于建立解剖坐标系的 calibration/anatomical markers。不要要求所有静态解剖点都出现在动态试次中。

静态文件的准确 36 点名单应直接从用户完成的静态 QTM 和项目 marker-list XML 读取，不能根据通用 CAST 图凭空补名字。

### 3.2 动态 28 点

本项目动态跟踪集合为：

| 区域 | 标记 | 说明 |
| --- | --- | --- |
| 骨盆 | `L_IAS`, `L_IPS`, `R_IPS`, `R_IAS` | 4 点 |
| 左大腿 | `L_TH1` 至 `L_TH4` | 4 点刚体板 |
| 右大腿 | `R_TH1` 至 `R_TH4` | 4 点刚体板 |
| 左小腿 | `L_SK1` 至 `L_SK4` | 4 点刚体板 |
| 右小腿 | `R_SK1` 至 `R_SK4` | 4 点刚体板 |
| 左足 | `L_FCC`, `L_FM1`, `L_FM2`, `L_FM5` | 4 点 |
| 右足 | `R_FCC`, `R_FM1`, `R_FM2`, `R_FM5` | 4 点 |

动态 label object 有 28 个，不代表每帧都有 28 个有效 sample；必须同时统计逐帧有效点数和每条 trajectory 的 gap range。

## 4. 左右颜色约定

用户特别指出静态文件左右两侧颜色不同。当前项目从用户静态文件得到的 QTM 整数颜色为：

| 身体侧 | 显示色 | QTM 整数值 |
| --- | --- | ---: |
| 左侧 | 青色 | `16763904` |
| 右侧 | 绿色 | `3329330` |

上述整数是 QTM 使用的 `0xbbggrr` 表示。所有动态标签应从静态模板复制对应侧颜色。颜色是很有用的人工检查信号，但颜色正确仍不能代替标签身份和连线检查。

## 5. 用户报告的关键问题

### 5.1 472 帧附近

用户反馈：472 帧补点位置大致合理，但连线错误。这说明当时的问题不是“坐标完全错误”，而是标记身份或 bone endpoint 错误。

处理规则：

1. 先显示 label 和 bones，确认每条线的两个端点名称。
2. 对照静态试次的同一刚体板，检查 TH1-TH4 或 SK1-SK4 的物理顺序。
3. 若坐标合理但线交叉，优先检查 label permutation 和 bone topology。
4. 在身份未修正前，不要继续用这些点作 relational reference。

### 5.2 497 帧附近的 R_TH

用户反馈：从 497 帧开始，`R_TH` 点有问题。后续分析表明问题不能只从肉眼最明显的 497 帧开始处理，应向前查找真正发生身份错误或刚体误差突变的起点。

现有脚本使用的候选修复范围为 API sample `492-522`。若当前 QTM 版本的界面帧号从 1 开始，则对应 QTM 显示帧约为 `493-523`。开始修改前必须在当前安装版本再次验证这个 +1 关系。

历史轨迹报告还显示 R_TH 片段存在身份竞争和重叠：

- 一条候选轨迹在 API sample `401-499` 主要被判为 `R_TH1`，但其中有部分帧更像 `R_TH3`；
- 另一条候选轨迹在 `473-513` 同时出现 `R_TH1` 与 `R_TH3` 竞争；
- 报告记录过 `R_TH1` 的 overlap conflict。

因此，这段不是普通单点 gap。它包含 **轨迹片段冲突、R_TH1/R_TH3 身份歧义和后续 relational 重建**，必须先解决身份再补点。

## 6. 为什么“点补齐了但线是错的”

QTM 的点坐标、trajectory label 和 bone 是三层不同信息：

```text
3D sample 坐标
    ↓ 属于
trajectory / trajectory part
    ↓ 被赋予
marker label（例如 R_TH1）
    ↓ 作为端点参与
bone（CAST 连线）
```

可能出现以下情况：

- 坐标正确，但 `R_TH1` 和 `R_TH3` 名称互换；
- label 正确，但 bone 列表沿用了错误端点；
- 一个 trajectory 在不同 part 中实际属于不同物理点，却被整体赋成一个 label；
- relational 使用了错标 reference，生成的位置平滑但物理身份错误；
- 四点板近似对称，单帧距离排列得分相近，算法选择了错误 permutation。

所以验收顺序应为：**身份 -> 连线 -> 几何 -> 缺点 -> 连续性 -> 点数**，而不是先追求 100% 点数。

## 7. 静态模板应该提取什么

从用户完成的静态试次选取无缺点、无明显抖动的稳定帧，至少记录：

1. 每个 marker 的准确 label。
2. 每个 marker 的左/右颜色。
3. 所有 bone 的准确端点对。
4. 每个四点组的代表性三维位置。
5. TH/SK 每块四点板的 6 条两两距离。
6. 静态自身在稳定区间内的距离波动。

四点板共有 6 条内部距离：

```text
1-2, 1-3, 1-4, 2-3, 2-4, 3-4
```

动态某帧相对静态模板的刚体误差可计算为：

```text
error_ij = dynamic_distance_ij - static_distance_ij
RMS = sqrt(sum(error_ij^2) / 6)
```

本项目可暂用以下筛查尺度：

| RMS | 解释 |
| ---: | --- |
| `<= 3 mm` | 刚体关系较强 |
| `3-5 mm` | 必须结合前后帧和画面复核 |
| `> 5 mm` | 可疑，检查错标、跳点或软组织移动 |

这些数值是筛查起点，不是跨受试者通用的硬阈值。最终阈值应参考该静态试次本身的噪声。

## 8. 动态轨迹身份判定顺序

对每条 dynamic trajectory part，按以下证据顺序判断：

1. 与前一个可信帧的位置和速度连续性。
2. 与后一个可信帧的位置和速度连续性。
3. trajectory part 的开始、结束、split 和 overlap 边界。
4. 与静态刚体板 6 条距离的匹配。
5. 一整段 part 内的稳定投票，而非单帧最优。
6. QTM 中 marker + bone 的视觉检查。

不要只用最近邻。左右腿可能靠近，足部在步态中会交叉，最近的点不一定是同一个物理 marker。

不要只用单帧 permutation。四点板近似对称时，多个排列的距离 RMS 可能相近。若最优和次优得分差很小，应保留为歧义并依赖时序与画面判断。

## 9. Relational 补点策略

### 9.1 单个目标点异常

当同一刚体板另外 3 个点可靠时：

```text
target <- relational(origin, line, plane)
```

例如只有 `R_TH1` 异常，而且 `R_TH2/R_TH3/R_TH4` 在整个范围均已确认可靠：

```text
R_TH1 <- relational(R_TH2, R_TH3, R_TH4)
```

要求：

- target 在修复范围之前和之后有可信锚点；
- 3 个 reference 在整个范围内有效；
- reference 都属于同一个刚体板；
- reference 身份已通过连续性、刚体距离和画面复核。

### 9.2 两个目标点同时异常

若 `R_TH1` 和 `R_TH3` 同时异常，只有 `R_TH2` 和 `R_TH4` 可靠，不能让两个坏点互相做 reference。正确依赖顺序是：

```text
第一步：R_TH3 <- relational(R_TH2, R_TH4)
第二步：重新审计 R_TH3
第三步：R_TH1 <- relational(R_TH2, 修复后的 R_TH3, R_TH4)
第四步：重新审计整个 R_TH 四点板
```

两参考补点必须有可靠的前后 target 锚点。第一步完成后，只有在 `R_TH3` 的位置、速度和刚体关系通过检查后，才能作为第二步的 plane reference。

现有 `refine_gait6_rth.py` 正是这个顺序，候选范围为 API sample `492-522`。但脚本存在不等于最终文件已经通过人工检查。

### 9.3 SK 四点板

`L_SK1-4` 和 `R_SK1-4` 使用完全相同的原则。TH 的 reference 不能用于 SK，左侧不能用于右侧。每块板独立维护刚体参考。

### 9.4 Relational 会覆盖现有 sample

QTM `fill_trajectory(..., "relational", range, settings)` 会覆盖指定范围内的所有 sample，包括原本存在但被判断为错误的 measured sample。因此：

- 先保存独立 backup；
- 明确记录 target、范围和 references；
- 只覆盖已证实错误的范围；
- 修复后另存新文件；
- 不要直接覆盖原始采集或用户静态文件。

## 10. QTM REST 操作要点

默认接口：

```text
http://127.0.0.1:7979/api/scripting/qtm
```

修改前先执行只读查询：

```text
file/get_path
file/is_open
file/is_dirty
gui/timeline/get_measured_range
gui/timeline/get_current_frame
data/object/trajectory/get_trajectory_ids
data/object/trajectory/get_label
data/object/trajectory/get_color
data/object/trajectory/get_parts
data/series/_3d/get_gap_ranges
data/object/bone/get_bone_ids
```

如果 QTM 当前 measurement 有未保存修改，先 `file/save_as` 到新的 backup 路径，再做任何 mutation。

处理 trajectory part 时要注意：

- `split_part(id, sample_index)` 把该 sample 作为 split 前一段的最后一个 sample；
- 每次 split、move 或 swap 后 part index 都可能变化；
- 每次 mutation 后必须重新查询 parts，不能继续使用旧 index；
- 不确定的片段优先保留为 unidentified/discarded 证据，不要直接删除。

## 11. 完整处理流程

### 阶段 A：建立静态 ground truth

1. 打开用户完成的 `Static LB Anterior - CAST 2.qtm`。
2. 确认静态点数是预期的 36。
3. 选稳定帧，检查是否存在缺失或明显错误点。
4. 提取 labels、左右颜色、bone endpoints 和 TH/SK 六边距离。
5. 保存静态模板，但不修改这个静态文件。

### 阶段 B：只读审计动态文件

1. 打开 `Gait LB - CAST 6_complete28_relational.qtm` 或其待查版本。
2. 记录 QTM 当前路径和 dirty 状态。
3. 统计 label 数、empty label、bone 数、unidentified parts。
4. 输出每帧 labeled point histogram 和 total point histogram。
5. 输出每个 marker 的 gap ranges。
6. 对四块 TH/SK 板计算逐帧六边 RMS。
7. 检查 472 帧和 497 帧附近的标签、连线、位移和速度。
8. 标出错标、真实 gap、corrupt sample 和边界 gap，不能混为一类。

### 阶段 C：先修身份与片段

1. 从异常前后的可信帧确认各物理点身份。
2. 找到真实异常起点，不只从肉眼明显帧开始。
3. 必要时 split trajectory part。
4. 只移动已确认的 part 到正确 label。
5. 检查 overlap，保证两个 part 不同时占用同一 label 和 sample。
6. 重新获取 parts 并再次审计。

### 阶段 D：修 bone topology

1. 从用户静态试次或 marker-list XML 读取准确 edge list。
2. 清理错误 bones。
3. 按准确 endpoint names 重建。
4. 在 QTM 中确认线连的是同一块物理刚体板上的预期点。

不要根据距离远近临时发明连线，也不要把四点板连成完全图。CAST 的线是身份检查的一部分，不是装饰。

### 阶段 E：relational 修复

1. 保存新的 backup。
2. 对每个目标范围确认前后锚点。
3. 确认 references 在整个范围可靠。
4. 按依赖顺序先修 reference marker，再修 dependent target。
5. 每一 pass 完成后重新审计，不要一次写多个相互依赖的修复。
6. 输出到新的、带版本号的 QTM 文件。

### 阶段 F：重新打开并验收

1. 关闭或切换当前 measurement。
2. 重新打开保存后的输出文件。
3. 重复完整只读审计。
4. 检查第 12 节所有验收项。
5. 把 QTM 时间线停在用户指出的关键帧，方便用户复核。

## 12. 验收清单

### 12.1 结构

- 动态存在准确的 28 个 tracking labels；
- 没有 required empty label；
- 动态 bone 数与本项目配置一致，历史目标为 21；
- 静态 bone 数与本项目配置一致，历史目标为 25；
- 左侧全部为静态定义的左侧颜色；
- 右侧全部为静态定义的右侧颜色；
- 没有 trajectory part overlap；
- unidentified/discarded parts 已报告并解释。

### 12.2 点数

- 报告逐帧 labeled point histogram；
- 报告逐帧 total point histogram；
- 分开报告内部 gap 与首尾 boundary gap；
- 不允许只报告“有 28 个 labels”或“多数帧 28 点”。

历史 `verify_v7_gait6.json` 对一个中间输出记录过：28 labels、无 empty label、颜色通过、21 bones；但仍有 19 帧只有 27 个 labeled points，并有 1 个 unidentified part。这个结果说明结构检查有进展，但不能证明后续 R_TH 身份和关键帧连线已经正确。

### 12.3 刚体几何

- TH/SK 每块板计算 6 条距离误差；
- 报告 median、95th percentile 和 max RMS；
- 检查修复范围本身以及前后至少 10 帧；
- 对异常最大的边单独检查，不能只看 aggregate RMS；
- 对近似对称板报告最优和次优 permutation 的差距。

### 12.4 轨迹连续性

- 修复起点前一帧到第一修复帧的位置连续；
- 修复末帧到下一可信帧的位置连续；
- 速度没有不合理尖峰；
- 必要时检查加速度；
- 不存在平滑但身份错误的整段轨迹。

### 12.5 QTM 画面

至少人工检查：

- 第一个异常帧；
- 用户报告的 472 帧；
- 用户报告的 497 帧；
- 刚体 RMS 最大帧；
- 修复范围最后一帧；
- 修复后第一个可信帧。

每个关键帧同时打开 marker labels 和 bones，确认 R_TH、R_SK、L_TH、L_SK 的线连接正确的物理板子。

## 13. Visual3D 前的判断

补点不必为了界面显示而强行达到 100%。Visual3D 更关注：

- 静态 calibration markers 完整并正确；
- 静态和动态的 tracking marker 名称一致；
- 分析区间内不存在身份交换；
- 每个刚体节段有足够的非共线有效点；
- 中间 gap 已可靠修复或排除；
- 轨迹没有不合理跳变。

对于 TH/SK 四点板，3 个不共线点已经可以定义 6-DOF 刚体姿态，第 4 点提供冗余。因此首尾少量缺点不一定阻止解算。默认做法是裁剪分析区间，而不是无依据外推首尾数据。

内部缺点、身份交换或错标则必须处理，因为它们会直接破坏节段姿态。**100% 完整但身份错误的数据，比保留少量已知边界缺点更危险。**

## 14. 可复用工具

工具入口：

```text
C:\Users\Admin\QualisysMarkerAutoSetRepair\scripts\qtm_cast_tool.py
```

在 QTM 打开用户静态文件后生成模板：

```powershell
py C:\Users\Admin\QualisysMarkerAutoSetRepair\scripts\qtm_cast_tool.py capture-template `
  --output C:\Users\Admin\qtm_mapping_work\cast-static-template-new.json
```

在 QTM 打开动态文件后只读审计：

```powershell
py C:\Users\Admin\QualisysMarkerAutoSetRepair\scripts\qtm_cast_tool.py audit `
  --template C:\Users\Admin\qtm_mapping_work\cast-static-template-new.json `
  --include-permutations
```

预演 R_TH1 修复，不写数据：

```powershell
py C:\Users\Admin\QualisysMarkerAutoSetRepair\scripts\qtm_cast_tool.py repair `
  --target R_TH1 `
  --start 493 --end 523 `
  --references R_TH2 R_TH3 R_TH4
```

只有确认 target、range、references 和帧号基准后才添加 `--execute`，并且必须提供新的 backup 与 output 路径。

## 15. 明确禁止的做法

- 不覆盖原始 `.qtm`。
- 不覆盖用户人工完成的静态 `.qtm`。
- 不把 CAST PDF 或 AIM 自动识别结果置于用户静态文件之上。
- 不因为点坐标靠近就直接分配 label。
- 不因单帧刚体 RMS 更低就交换整块板的四个标签。
- 不在错标尚未解决时执行 gap fill。
- 不使用另一身体侧或另一节段的 marker 作为 relational reference。
- 不使用本身可疑或缺失的 marker 作为 reference。
- 不为达到 100% 而盲目外推首尾 gap。
- 不把“28 点齐全”写成最终验收结论。
- 不删除无法判断的原始轨迹证据；优先保留为 unidentified/discarded。

## 16. 下一位接手者的优先工作

1. 重新打开用户完成的静态试次，重新导出本次工作的静态模板与 bone edge list。
2. 重新打开 `Gait LB - CAST 6_complete28_relational.qtm`，做一次完全只读的动态审计。
3. 明确 QTM UI frame 与 API sample 是否为 +1，避免 497 帧范围偏移。
4. 从 497 帧向前追溯 R_TH 真正异常起点，重点检查 API `492-522`。
5. 解决 R_TH1/R_TH3 trajectory part overlap 和身份歧义。
6. 若两点同时异常，先用 R_TH2/R_TH4 两参考重建 R_TH3，再用三参考重建 R_TH1。
7. 重建或核对 R_TH bones，检查 472、497 和最大 RMS 帧的连线。
8. 重新打开候选输出并跑完整验收；不通过则生成新的版本，不覆盖旧候选。
9. 对 CAST 5、6/10、8 使用同一静态基准分别审计，不把某一试次的片段边界直接套到另一试次。
10. 最后再判断 Visual3D 分析区间，而不是先追求所有首尾帧 100% 填满。

## 17. 最终交付时必须报告

最终交付说明至少包含：

- 输入静态文件、输入动态文件、backup 和输出文件的完整路径；
- QTM 显示帧与 API sample 的对应关系；
- 哪些是 missing marker，哪些是 wrong identity/corrupt sample；
- 每个修复 target 的准确范围和 references；
- 多目标 relational 的依赖顺序；
- 修复前后刚体 RMS、位置和速度边界误差；
- 28 点逐帧 histogram 与剩余 gap；
- unidentified/discarded parts；
- 左右颜色与 bone topology 的检查结果；
- QTM 人工检查过的关键帧；
- 是否仍有歧义，以及 Visual3D 建议使用的分析区间。

只有上述检查完成，才能把文件描述为“可进入 Visual3D 进一步处理的候选结果”。
