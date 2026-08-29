# 精选中国节日日历

这是一个给 Apple Calendar（iPhone、iPad、Mac）长期订阅的高信噪比补充日历：精选传统节日、二十四节气、常见国际节日和少量全国性纪念日，不写入国务院放假、调休或补班信息。

中国大陆法定节假日、放假日期与调休请继续使用 Apple 自带的“中国大陆节假日”日历。本项目只补充它覆盖不足的内容。

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

- `festival.ics`：中国常见公历节日、常见国际节日、少量全国性纪念日、默认启用的文化日期，以及传统节日；不含二十四节气本身。
- `lunar.ics`：传统农历节日、清明节和完整二十四节气。
- `lunar-terms.ics`：只含二十四节气，用于与 `festival.ics` 组合且不重复。
- `all.ics`：上述内容的去重合并版。

默认仅启用 520、双11 两个大众文化日期；618、女生节、1024 程序员节、双12 保留在配置中且默认关闭。项目不收录大量“世界 XX 日”、行业宣传周、人物诞忌日或商业营销日。

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
