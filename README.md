# 法硕刑法真题教材页码速查

这是一个可直接部署到 GitHub Pages 的静态网页，收录 2010—2026 年法学、非法学刑法客观题，按题目关联众合 2027《背诵一本通》《精讲一本通》的纸质书印刷页。

## 当前口径

- 法学 250 道、非法学 425 道，共 675 道。
- 2025、2026 年两类试卷均已收录。
- 一道题允许关联多个罪名或刑法总则考点。
- 不提供教材 PDF、真题题面或第三方解析全文。

## 生成与检查

```powershell
python scripts/build_final_site.py
python scripts/validate_final_dataset.py
```

部署入口是仓库根目录的 `index.html`；在 GitHub Pages 中选择 **Deploy from a branch → main / root** 即可。`web/index.html` 是同内容的本地预览副本。

## 微信小程序

`miniprogram/` 是不依赖后端的原生微信小程序版本，保留搜索、三项筛选、双类别试卷与教材印刷页码展示。

```powershell
python scripts/build_final_site.py
python scripts/build_miniprogram_data.py
python scripts/validate_miniprogram.py
```

然后以 `miniprogram/` 为目录导入微信开发者工具，并在 `miniprogram/project.config.json` 中把 `appid` 替换为你的小程序 AppID。发布前请在真机预览中检查搜索、筛选和长列表。

主要文件：

- `data/site_dataset.json`：网页使用的双类别数据集。
- `data/topics.json`：合并并核验后的考点—教材页码索引。
- `data/page_audit.json`：两套页码索引的差异与逐项取舍。
- `data/questions.source.json`、`data/topics.source.json`：生成用源数据。
