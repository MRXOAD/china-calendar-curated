# 精选中国节日日历

这是一个给 Apple Calendar（iPhone、iPad、Mac）长期订阅的高信噪比补充日历：精选非法定传统节日、二十四节气、常见国际节日和少量全国性纪念日，不写入国务院放假、调休或补班信息。

中国大陆法定节假日、放假日期与调休请继续使用 Apple 自带的“中国大陆节假日”日历。本项目只补充它覆盖不足的内容。默认明确排除元旦、春节、除夕、清明节、端午节、中秋节、国庆节，避免同名法定节日重复；“清明”仅保留为二十四节气。

## 订阅

部署 GitHub Pages 后，将下面的 `<用户名>` 与 `<仓库名>` 替换为实际值：

- `https://<用户名>.github.io/<仓库名>/festival.ics`
- `https://<用户名>.github.io/<仓库名>/lunar.ics`
- `https://<用户名>.github.io/<仓库名>/lunar-terms.ics`
- `https://<用户名>.github.io/<仓库名>/all.ics`

在 Apple Calendar 中选择“添加日历” → “添加订阅日历”，粘贴任一 URL。事件均为全天、透明事件，不含提醒。

推荐组合：

1. **简洁**：Apple 自带“中国大陆节假日” + `festival.ics`。
2. **完整、分成两条订阅**：Apple 自带“中国大陆节假日” + `festival.ics` + `lunar-terms.ics`。
3. **一个订阅解决**：Apple 自带“中国大陆节假日” + `all.ics`。

`festival.ics` 与 `lunar.ics` 都按各自用途收录传统节日；因此不要同时订阅这两条，否则传统节日会在两个订阅日历中各出现一次。需要 `lunar.ics` 的完整农历视图时单独订阅；需要组合视图请使用不会重复的 `all.ics`，或使用 `festival.ics + lunar-terms.ics`。同样，不要把 `all.ics` 与任何其他本项目订阅源同时添加。

## 内容边界

- `festival.ics`：中国常见公历节日、常见国际节日、少量全国性纪念日、默认启用的文化日期，以及非国家法定传统节日；不含二十四节气本身。
- `lunar.ics`：非国家法定传统农历节日和完整二十四节气。
- `lunar-terms.ics`：只含二十四节气，用于与 `festival.ics` 组合且不重复。
- `all.ics`：上述内容的去重合并版。

默认仅启用 520、双11 两个大众文化日期；618、女生节、1024 程序员节、双12 保留在配置中且默认关闭。项目不收录大量“世界 XX 日”、行业宣传周、人物诞忌日或商业营销日。

这里的“完整”指配置中已启用的 34 类节日、纪念日与 24 个节气完整生成，不是全部中国节日大全。母亲节采用五月第二个星期日，父亲节采用六月第三个星期日，感恩节采用美国的十一月第四个星期四；小年分别列出腊月二十三、二十四两种常见日期，不代表所有地区习俗。

纪念日只从其首次举办年份开始生成，设立依据记录在 `data/anniversaries.yaml` 的 `source` 字段中，不把后来设立的纪念日回填到 2000 年。文化日期仅表示按当前收录口径推算的月日，不表示当年的民俗或商业活动已经存在。

农历和节气按北京时间（UTC+8）计算。2026-11-01 与[香港天文台 2000–2100 年对照表](https://www.hko.gov.hk/tc/gts/time/conversion.htm)核对时，2,424 条节气全部一致；1,111 条传统节日中，2057 年重阳节存在一天差异：当前算法为 10 月 7 日，天文台表为 10 月 6 日。天文台已说明 2057 年 9 月新月接近午夜，远期预测可能导致一天差别；本项目保留算法结果，后续随权威历表更新复核。这一差异不影响当前年份。

## 本地生成

要求 Python 3.12+。

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
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
