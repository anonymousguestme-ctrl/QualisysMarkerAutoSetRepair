---
name: qualisys-cast-gap-repair
description: 处理 Qualisys QTM 的 CAST 下肢 marker 对应、错标、断线、刚性板身份检查和经授权的 relational 补点。适用于静态 36 点、动态 28 点、TH/SK 四点刚性板、左右颜色或连线错误、Visual3D 前的数据质控。不能用于创造原本没有采集到的 marker，也不能把补点结果伪装成 measured 数据。
---

# Qualisys CAST Gap Repair

这是一个**先确认 marker 身份、再决定是否补点**的本地工作流程。目标是得到可以追溯、可重新打开检查、能交给 Visual3D 的 QTM 文件，而不是简单地让屏幕上每一帧看起来有 28 个点。

## 最重要的原则

1. **Measured 优先。** 同一个 marker、同一帧同时存在正确的 `Measured` 和填充结果时，保留正确的 `Measured`。不能为了让曲线更平滑、让每帧显示 28 个点或达到 100% 而覆盖它。
2. **不创造 marker。** 不新增 marker 对象，不复制、镜像、平移、插值或外推一个从未采集到的物理点。静态期望 36 个点、动态期望 28 个点只是检查基准，不是制造缺失点的理由。
3. **身份问题先于缺失问题。** 点出现在错误位置、左右串了、刚性板四点连线错误，属于 label/identity 错误，不是 gap。不能对错误身份的数据直接补点。
4. **连接线必须由正确 label 决定。** 连线错，先修 marker label 或骨拓扑，再谈补点。点的位置大致正确但线连接到另一块板，仍然是错误结果。
5. **Relational 只补已有物理 marker 的缺口。** 只能在用户明确要求补点、目标 marker 曾经被可靠采集、参考 marker 足够可靠时使用。不能用 relational 创造从未出现过的骨性点或整块缺失的刚体板。
6. **原始数据永不覆盖。** 原始 `.qtm`、用户已经完成的静态试验、`.qpr`、PAF 和工程配置均视为受保护文件。任何写入都使用新的、带阶段后缀的输出文件。
7. **“100%”不是唯一验收标准。** 边界缺失可以通过裁剪分析区间处理；一份 100% 完整但 marker 身份错误的文件不能用于 Visual3D。

## 何时使用

使用本 skill 的典型请求包括：

- 把动态 marker 按已确认的静态点对应起来；
- 检查左右颜色、marker 名称和 QTM 连线；
- 检查 `TH1-TH4`、`SK1-SK4` 四点刚性板是否串板或错连；
- 找出 gap、fragment、错标、重复 label 和边界缺失；
- 在得到明确授权后，用 relational 方法修复可靠 marker 的内部缺口；
- 在导出 C3D、导入 Visual3D 之前做最后的结构和刚体几何检查。

如果用户只要求计算 Visual3D 关节角度，应转到 `qualisys-visual3d-joint-angles`；如果 marker 身份还未确认，先完成本 skill，再进入 Visual3D。

## 处理前的安全盘点

### 1. 确认目标和帧号

- 记录完整文件路径、目标 trial、静态参考 trial、动态 trial 顺序。
- 明确用户说的“472 帧”是 QTM 界面显示帧，还是 API 的零基 sample index。QTM 常见关系是 UI frame `n+1` 对应 API sample `n`，必须以当前安装版本和实际文件核对。
- 不根据文件名连续编号猜测用户要处理的 trial。用户确认的顺序优先。

### 2. 建立原始清单

对候选 `.qtm`、`.c3d`、`.qpr`、PAF、设置文件和静态文件记录：绝对路径、文件大小、修改时间、SHA-256，以及是否已在 QTM 中打开或 dirty。

如果 QTM 当前有未保存状态，先用 `file/save_as` 保存到单独的备份；不要直接关闭并丢弃状态。

### 3. 只读优先

先运行结构审计和 marker 统计，不要一上来写入 QTM。先回答：实际有哪些 label；每个 label 有几个 trajectory part；哪些帧是 measured、filled、interpolated 或 relational；哪些点缺失；缺失是内部还是头尾边界；TH/SK 四点的距离关系是否稳定；左右颜色和静态参考是否一致。

推荐使用：

```text
C:\Users\Admin\.codex\skills\qualisys-cast-gap-repair\scripts\qtm_cast_tool.py
```

具体 REST 参数和 frame/sample 规则见 `references/qtm-api.md`；marker 集合见 `references/marker-set.md`；完整操作流程见 `references/workflow.md`。

## CAST 下肢 marker 逻辑

### 静态与动态数量

- 静态 CAST 通常约 36 个点，因为包含骨性标志和校准点。
- 动态 CAST 通常约 28 个点，主要保留刚体追踪和足部 marker。
- 这是配置检查，不是强制补齐目标。实际数量必须服从这次采集真正存在的 marker。

### 刚性板

常见刚体板定义：

- `L_TH1-L_TH4`：左大腿刚体板
- `R_TH1-R_TH4`：右大腿刚体板
- `L_SK1-L_SK4`：左小腿刚体板
- `R_SK1-R_SK4`：右小腿刚体板

四点板的判断不能只看某一帧的空间位置。必须综合静态参考中四点的相对距离、动态相邻帧连续性、trajectory part 边界、左右侧和颜色、QTM 的 bone/line 连接以及刚体模板 RMS 误差。

三点非共线可以定义六自由度姿态，第四点用于冗余检查。不能因为某一帧缺第四点，就把其他点改名或创造新点。

### 颜色和连线

颜色是身份检查的一部分，但颜色本身不能替代轨迹证据。必须核对：左右颜色是否与用户已确认的静态 trial 一致；每条 bone 是否连接到同一侧、同一刚体板的正确 label；是否把 TH 点连到了 SK，或把左侧连到了右侧。点坐标看起来正确但连线错误时，优先怀疑 label/拓扑，而不是位置。

## Measured、缺口和身份错误

### Measured 优先

- 正确的 `Measured` 样本是最高优先级。
- `Relational`、interpolated、pattern fill 都属于合成来源，必须保留 provenance。
- 如果 measured 样本位置明显属于另一个物理点，不能因为它标成 Measured 就盲目保留；但必须有轨迹连续性、静态几何、part 边界和 QTM 线拓扑共同证据后才能改身份。
- 改身份前保存原文件和修改前清单，报告被替换的 label、帧区间和理由。

### 判断是否为 gap

真正的 gap 是：目标物理 marker 身份明确，但某些帧没有有效坐标。以下情况不是普通 gap：点在另一块刚体板上、左右侧互换、四点几何像另一块板、QTM 连线连接错误、轨迹在 part 边界发生身份跳变。先隔离或纠正错误身份，再考虑 relational。

## Relational 补点流程

只有用户明确要求补点时才执行。

### 1. 定义目标

记录目标 marker、精确起止帧、UI frame 还是 API sample、目标区间原有 provenance、参考 marker 和刚体板、预计输出文件名。默认只修复内部缺口；不要为了达到 100% 自动外推开头或结尾，必要时裁剪分析区间并记录。

### 2. 选择参考点

优先使用同一刚体板的三个可靠参考：`origin`、`line`、`plane`。参考点必须优先来自 `Measured`。如果参考点本身也是填充的，先验证它，再把它用于依赖关系；不能静默形成多层合成链。

### 3. 依赖顺序

先修复参考 marker，再修复依赖它们的目标 marker。每一轮之后重新审计：是否覆盖了错误范围；是否覆盖了原有正确 measured；参考点是否全程有效；目标点是否连续；刚体 RMS 是否改善。

### 4. 写入前保护

QTM relational 写入通常会覆盖指定范围样本。写入前必须枚举目标区间已有的 `Measured` 样本；正确 measured 存在时默认中止；只有用户明确授权覆盖错误 measured，且已记录身份错误证据时才允许覆盖；使用新的输出 QTM 路径，不写回原始文件。

### 5. 写入后检查

补点结果必须标记为 relational/filled，不能伪装为 measured。检查补点数量和帧区间、依赖的参考 marker、NaN、端点位置和速度连续性、相对静态模板的刚体距离 RMS，并在 QTM 中查看第一坏帧、最坏帧、第一好帧的显示和连线。

## 刚体板身份判定

对 TH/SK 四点，不能只用一帧最近距离自动排列。优先级是：用户确认的静态身份；前后有效帧连续性；四点相对距离和拓扑；trajectory part 时间边界；左右颜色和 bone 连接；静态模板 RMS。

当四点板接近对称、多个排列距离分数相近时，宁可标记 ambiguous 并请求确认，也不能根据单帧最低距离分数自动换名。

刚体误差是筛查而不是身份裁决：`<=3 mm` 通常较好，`3-5 mm` 需要视觉检查，`>5 mm` 可疑。阈值要结合静态 trial 自身误差和刚体板是否被碰动。

## 必须完成的验证

交付修改后的 QTM 前必须：

1. 对照实际 label 集合和 CAST 配置，列出缺失 label；
2. 对照静态/动态 marker 数和 bone 数；
3. 核对左右颜色与静态约定；
4. 确认没有多个 trajectory part 声明同一 label；
5. 报告每帧有效点数量，并区分内部 gap 与边界 gap；
6. 确认每个 filled frame 的参考点有效；
7. 报告 measured/filled provenance；
8. 确认没有覆盖正确 measured，若覆盖则给出身份错误依据；
9. 比较修复区间及两端与静态模板的刚体距离；
10. 检查修复接缝位置和速度连续性；
11. 在 QTM 中查看第一坏帧、最坏帧、第一好帧并确认正确连线；
12. 重新打开输出 QTM 再做结构审计；
13. 对输出 QTM 计算 SHA-256 并写入 manifest；
14. 若交给 Visual3D，确认动态追踪点身份正确，但不要为凑齐静态解剖点而补点。

## 不应做的事情

- 不要把 `Measured` 全部改成 filled；
- 不要为了“每帧 28 点”推出不存在的点；
- 不要按单帧距离全局重排四点板；
- 不要在身份未确认时先 relational；
- 不要用 `_CGM`、其他模型或其他 trial 的点代替 CAST 点；
- 不要在 QTM 打开文件时覆盖原始文件；
- 不要用宽泛 wildcard 删除原始数据、PAF 或工程文件；
- 不要把输出文件称为 original；
- 不要只因为曲线平滑或点数达到 100% 就宣布修复成功。

## 输出记录

每次处理至少留下 manifest，包含：原始和输出绝对路径及 SHA-256、静态参考、动态 trial 顺序、UI frame/API sample 约定、修改的 label 和帧区间、measured/relational/interpolated 数量、relational 依赖顺序、TH/SK RMS 前后值、颜色和 bone/line 检查、是否覆盖 measured、边界 gap 是否裁剪、未解决歧义以及是否满足 Visual3D 输入条件。

## 本地资源

- [references/marker-set.md](references/marker-set.md)：CAST marker、左右侧、颜色、静态/动态数量和骨拓扑。
- [references/workflow.md](references/workflow.md)：从只读诊断到输出验证的详细流程。
- [references/qtm-api.md](references/qtm-api.md)：QTM REST、frame/sample 和安全写入方法。
- [scripts/qtm_cast_tool.py](scripts/qtm_cast_tool.py)：模板采集、审计和定向 relational 修复脚本。

除非当前任务确实需要，不要一次性加载所有参考文件。先读本入口，再根据任务读取对应 reference。

## 给用户的交付说明

必须明确写出哪些 marker 是原始 measured、哪些是 relational/filled、是否纠正过身份、是否覆盖 measured、是否仍有缺失或边界 gap、输出文件位置、原始文件是否保持不变、是否达到 Visual3D 可用条件，以及仍需用户在 QTM 中确认的画面/颜色/连线问题。“已修复”不能只表示文件能打开或点数变多。
