# 精选中国节日日历

这是一个给 Apple Calendar（iPhone、iPad、Mac）长期订阅的补充日历。推荐使用 `all.ics`，显示名称为“中华节日补充日历”：只保留 Apple“中国大陆节假日”尚未覆盖的精选节日与纪念日，不写入放假、调休或补班安排。

Apple 自带日历实际还包含二十四节气、元宵、七夕、重阳；历史版本也收录过妇女节、青年节、儿童节。`all.ics` 按已记录和当次官方源确认的节日类别在全部年份中排除，识别“七夕／七夕节”和“（休）／（班）”等名称差异，不因 Apple 当前年份窗口较短而重新补入。

## 订阅

部署 GitHub Pages 后，将下面的 `<用户名>` 与 `<仓库名>` 替换为实际值：

- `https://<用户名>.github.io/<仓库名>/festival.ics`
- `https://<用户名>.github.io/<仓库名>/lunar.ics`
- `https://<用户名>.github.io/<仓库名>/lunar-terms.ics`
- `https://<用户名>.github.io/<仓库名>/all.ics`

在 Apple Calendar 中选择“添加日历” → “添加订阅日历”，粘贴任一 URL。事件均为全天、透明事件，不含提醒。

推荐组合只有一套：**Apple 自带“中国大陆节假日” + `all.ics`**。原订阅地址保持不变，无需重新订阅，刷新后会移除重复事件。

另外三条源保留给不使用 Apple 自带日历的人独立选择；它们会与 Apple 重复，不要与上述推荐组合叠加。`festival.ics + lunar-terms.ics` 可形成一套独立的完整精选日历；`festival.ics` 与 `lunar.ics` 之间也有传统节日重叠。

## 内容边界

- `all.ics`：与 Apple 官方源去重后的补充版，推荐长期订阅。
- `festival.ics`：独立版，34 类精选节日、纪念日，不含二十四节气。
- `lunar.ics`：独立版，11 类传统农历节日和完整二十四节气。
- `lunar-terms.ics`：独立版，只含二十四节气。

发布前先下载并解析 [Apple 官方中国大陆节假日源](https://calendars.icloud.com/holidays/cn_zh.ics)，更新 `data/apple_covered.json`。读取或解析失败时停止发布，保留上次有效的在线版本；不把失败当成 Apple 没有收录。ICS 解析使用锁定版本的 `icalendar`，以正确识别 Apple 的语言参数和折行。

默认仅启用 520、双11 两个大众文化日期；618、女生节、1024 程序员节、双12 保留在配置中且默认关闭。项目不收录大量“世界 XX 日”、行业宣传周、人物诞忌日或商业营销日。

这里的“完整”指当前收录口径下完整生成，不是全部中国节日大全。2026-11-01 对照 Apple 官方源后，`all.ics` 保留 28 类、2,722 条补充事件，覆盖 2000–2100 年；24 个节气以及元宵、七夕、重阳、妇女节、青年节、儿童节由 Apple 提供。母亲节采用五月第二个星期日，父亲节采用六月第三个星期日，感恩节采用美国的十一月第四个星期四；小年分别列出腊月二十三、二十四两种常见日期，不代表所有地区习俗。

纪念日只从其首次举办年份开始生成，设立依据记录在 `data/anniversaries.yaml` 的 `source` 字段中，不把后来设立的纪念日回填到 2000 年。文化日期仅表示按当前收录口径推算的月日，不表示当年的民俗或商业活动已经存在。

独立版的农历和节气按北京时间（UTC+8）计算。2026-11-01 与[香港天文台 2000–2100 年对照表](https://www.hko.gov.hk/tc/gts/time/conversion.htm)核对时，2,424 条节气全部一致；1,111 条传统节日中，2057 年重阳节存在一天差异：当前算法为 10 月 7 日，天文台表为 10 月 6 日。天文台已说明 2057 年 9 月新月接近午夜，远期预测可能导致一天差别。推荐的 `all.ics` 已排除重阳节，这条远期差异仅留在独立版中。

## 本地生成

要求 Python 3.12+。

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python apple_reference.py
.venv/bin/python generate.py
.venv/bin/python -m unittest discover -s tests -v
```

默认生成 2000–2100 年。可临时改范围而不修改配置：

```bash
python generate.py --start-year 2020 --end-year 2050
```

YAML 位于 `data/`；新增或关闭固定日期、按星期规则的日期、农历日期或纪念日均不需要改 Python。农历转换、闰月处理、除夕和节气由 [`lunar_python`](https://pypi.org/project/lunar_python/) 计算。它是 MIT 许可项目，当前锁定版本为 1.4.8；UID 按“节日 slug + 公历完整日期”稳定生成，避免腊八等可能在同一公历年一月和十二月各出现一次时发生冲突。项目测试对农历、节气、星期规则、UID 与 ICS 基本结构做回归检查。

## 发布到 GitHub Pages

1. 在 GitHub 新建空仓库并推送本目录内容到 `main`。
2. 打开仓库 **Settings → Pages**，将 Source 选为 **GitHub Actions**。
3. 推送 `main`、手动运行 workflow，或每月自动任务都会运行测试、生成 `dist/` 并发布 Pages。

订阅 URL 只有在 GitHub Pages 首次部署完成后才会生效。工作流仅发布 `dist/` 下的 ICS 文件。

## 防止定时任务因不活跃而停用

GitHub 会在公共仓库连续 60 天没有活动时停用定时工作流，成功构建和 Pages 部署不能代替仓库提交。`keepalive.yml` 每周一 03:43 UTC 独立检查一次；最近提交满 30 天时，才通过仓库自带的 `GITHUB_TOKEN` 写入一个空提交。它不修改任何文件、不生成日历，也不部署 Pages；该令牌的推送不会触发新的工作流运行。

只有独立保活任务使用本仓库的 `contents: write`，原发布工作流仍为 `contents: read`，不新增个人访问令牌或外部主机。保活推送失败会让任务失败，不强制覆盖主分支。主分支若以后开启禁止直接推送的保护规则，应同步调整此保活方式。

原月度发布时刻仍为每月 1 日 02:17 UTC，四个订阅文件名和地址保持不变。可在 Actions 中手动运行 **Keep calendar publishing active** 检查保活；近期已有提交时，它会正常结束且不产生新提交。
