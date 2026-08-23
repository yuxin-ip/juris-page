# -*- coding: utf-8 -*-
"""生成单文件网页：法硕刑法真题 -> 教材页码速查"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r"D:\code\juris_page"
data = json.load(open(base + r"\data\dataset_xingfa_v1.json", encoding="utf-8"))

# 热门罪名（出现次数排序）
from collections import Counter
zc = Counter()
for x in data:
    for p in x["points"]:
        if p["type"] == "zuiming":
            zc[p["name"]] += 1
hot_zuiming = [z for z, _ in zc.most_common(14)]

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>法硕刑法真题 · 教材页码速查</title>
<style>
:root{
  --bg:#f5f6f8; --card:#ffffff; --line:#e5e7eb;
  --text:#1f2937; --muted:#6b7280;
  --brand:#1e40af; --brand-soft:#eef2ff;
  --bs:#0f766e; --jj:#b45309;
}
*{box-sizing:border-box; margin:0; padding:0;}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; background:var(--bg); color:var(--text); line-height:1.6;}
.wrap{max-width:860px; margin:0 auto; padding:20px 16px 60px;}
header{padding:8px 0 18px;}
header h1{font-size:22px; font-weight:700;}
header p{color:var(--muted); font-size:13px; margin-top:4px;}
.controls{position:sticky; top:0; background:var(--bg); padding:10px 0; z-index:5;}
.search{width:100%; padding:11px 14px; font-size:15px; border:1px solid var(--line); border-radius:10px; outline:none; background:#fff;}
.search:focus{border-color:var(--brand); box-shadow:0 0 0 3px var(--brand-soft);}
.row{display:flex; gap:8px; margin-top:10px; flex-wrap:wrap; align-items:center;}
select{padding:8px 10px; border:1px solid var(--line); border-radius:8px; background:#fff; font-size:13px; color:var(--text); outline:none;}
.tags{display:flex; gap:6px; flex-wrap:wrap; margin-top:10px;}
.tagbtn{font-size:12px; padding:4px 10px; border-radius:999px; border:1px solid var(--line); background:#fff; color:var(--muted); cursor:pointer; user-select:none;}
.tagbtn.on{background:var(--brand); border-color:var(--brand); color:#fff;}
.stats{font-size:13px; color:var(--muted); margin:14px 0 10px;}
.card{background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; margin-bottom:12px; box-shadow:0 1px 2px rgba(0,0,0,.03);}
.card-head{display:flex; align-items:center; gap:8px; flex-wrap:wrap;}
.qid{font-weight:700; font-size:15px; color:var(--brand);}
.badge{font-size:11px; padding:2px 8px; border-radius:6px; border:1px solid var(--line); color:var(--muted);}
.badge.ans{border-color:#c7d2fe; background:var(--brand-soft); color:var(--brand); font-weight:600;}
.main-kd{margin-top:8px; font-size:15px;}
.main-kd b{color:var(--brand); font-weight:700;}
.points{display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;}
.point{font-size:12px; border:1px solid var(--line); border-radius:8px; padding:3px 8px; background:#fafafa; display:inline-flex; gap:6px; align-items:center;}
.point .nm{color:var(--text);}
.point .pg{color:var(--muted);}
.point .pg.bs{color:var(--bs); font-weight:600;}
.point .pg.jj{color:var(--jj); font-weight:600;}
.point.main{border-color:#c7d2fe; background:var(--brand-soft);}
.point.main .nm{font-weight:700; color:var(--brand);}
details{margin-top:10px; border-top:1px dashed var(--line); padding-top:8px;}
summary{cursor:pointer; font-size:12px; color:var(--muted); outline:none;}
.analysis{font-size:13px; color:#374151; margin-top:8px; background:#f9fafb; padding:10px 12px; border-radius:8px;}
.empty{text-align:center; color:var(--muted); padding:40px 0; font-size:14px;}
footer{text-align:center; color:#9ca3af; font-size:12px; margin-top:30px;}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>法硕刑法真题 · 教材页码速查</h1>
    <p>选择题 → 考点 → 众合《背诵一本通》《精讲一本通》页码（2010–2026 非法学基础课）</p>
  </header>

  <div class="controls">
    <input class="search" id="q" placeholder="搜索题号 / 考点 / 罪名，如：2024、抢劫罪、2010-25">
    <div class="row">
      <select id="year"><option value="0">全部年份</option></select>
      <select id="type">
        <option value="">全部题型</option>
        <option value="single">单选题</option>
        <option value="multi">多选题</option>
      </select>
      <span style="font-size:12px;color:var(--muted)">热门罪名：</span>
    </div>
    <div class="tags" id="tags"></div>
    <div class="stats" id="stats"></div>
  </div>

  <div id="list"></div>
  <footer>数据来源：法硕历年真题解析 + 众合刑法教材（背诵一本通 / 精讲一本通）</footer>
</div>

<script>
var DATA = __DATA__;
var HOT = __HOT__;

var state = { q:"", year:0, type:"", zui:"" };

function esc(s){ return String(s).replace(/[&<>"]/g, function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }

function pg(v){ return v==null ? "-" : v; }

function render(){
  var list = document.getElementById("list");
  var q = state.q.trim().toLowerCase();
  var rows = DATA.filter(function(x){
    if(state.year && x.year != state.year) return false;
    if(state.type && x.type != state.type) return false;
    if(state.zui){
      var has = x.points.some(function(p){ return p.name === state.zui; });
      if(!has) return false;
    }
    if(q){
      var hay = (x.id + " " + x.kaodian + " " + x.year + " " +
        x.points.map(function(p){return p.name;}).join(" ")).toLowerCase();
      if(hay.indexOf(q) < 0) return false;
    }
    return true;
  });

  document.getElementById("stats").textContent = "共 " + rows.length + " 道题" + (state.zui ? "（罪名：" + state.zui + "）" : "");

  if(!rows.length){ list.innerHTML = '<div class="empty">没有匹配的题目</div>'; return; }

  var html = rows.map(function(x){
    var pts = x.points.map(function(p){
      var cls = "point" + (p.name === x.kaodian ? " main" : "");
      return '<span class="'+cls+'"><span class="nm">'+esc(p.name)+'</span>'+
        '<span class="pg bs">背P.'+pg(p.beisong_page)+'</span>'+
        '<span class="pg jj">精P.'+pg(p.jingjiang_page)+'</span></span>';
    }).join("");
    var typeZh = x.type === "single" ? "单选" : "多选";
    return '<article class="card">'+
      '<div class="card-head"><span class="qid">'+esc(x.id)+'</span>'+
      '<span class="badge">'+typeZh+'</span></div>'+
      '<div class="main-kd">主考点：<b>'+esc(x.kaodian)+'</b></div>'+
      '<div class="points">'+pts+'</div>'+
      '</article>';
  }).join("");
  list.innerHTML = html;
}

function buildYears(){
  var s = document.getElementById("year");
  for(var y=2010; y<=2026; y++){ var o=document.createElement("option"); o.value=y; o.textContent=y+" 年"; s.appendChild(o); }
}
function buildTags(){
  var box = document.getElementById("tags");
  box.innerHTML = HOT.map(function(z){
    return '<span class="tagbtn" data-z="'+esc(z)+'">'+esc(z)+'</span>';
  }).join("");
}
function refreshTags(){
  var btns = document.querySelectorAll(".tagbtn");
  btns.forEach(function(b){ b.classList.toggle("on", b.getAttribute("data-z")===state.zui); });
}

document.getElementById("q").addEventListener("input", function(e){ state.q=e.target.value; render(); });
document.getElementById("year").addEventListener("change", function(e){ state.year=+e.target.value; render(); });
document.getElementById("type").addEventListener("change", function(e){ state.type=e.target.value; render(); });
document.getElementById("tags").addEventListener("click", function(e){
  var b = e.target.closest(".tagbtn"); if(!b) return;
  var z = b.getAttribute("data-z");
  state.zui = (state.zui === z) ? "" : z;
  refreshTags(); render();
});

buildYears();
buildTags();
render();
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace("__HOT__", json.dumps(hot_zuiming, ensure_ascii=False))
out = base + r"\web\index.html"
import os
os.makedirs(base + r"\web", exist_ok=True)
open(out, "w", encoding="utf-8").write(html)
print("已生成", out, "大小", len(html)//1024, "KB")
print("热门罪名:", hot_zuiming)
