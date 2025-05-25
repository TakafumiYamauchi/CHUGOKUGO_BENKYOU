import pandas as pd

# CSV を読み込み
df = pd.read_csv('all_sentences_with_ruby.csv', dtype=str)

# ---- ここから並び替えロジックを修正 ----
# 元のCSVはデータベースで既に「レベル / グループ / 単元」順に並んでいる。
# ただし念のため、同じキーで再ソートしておく。
# これにより make_audio_player.py と完全に同じ並びになる。

df = df.sort_values(['レベル', 'グループ', '単元'], key=lambda col: col.astype(int))

# レベル一覧を取得（レベルセレクト用）
levels = sorted(df['レベル'].dropna().unique(), key=lambda x: int(x))

# ---- ここまで ----

# HTML ヘッダー部
html_head = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>HSK 例文集</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    ruby { ruby-position: over; }
    rt { font-size: 0.6em; color: gray; }
    .entry { margin-bottom: 1.5em; border-bottom: 1px solid #ddd; padding-bottom: 1em; }
    .controls { 
      margin-bottom: 1em; 
      position: sticky; 
      top: 0; 
      background: #fff; 
      padding: 10px 0; 
      z-index: 100; 
      box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    .controls select, .controls input { margin-right: 8px; }
    .meaning { font-weight: bold; margin: 0.5em 0; }
    .meta-info { font-size: 0.9em; color: #666; }
    .sentence { font-size: 1.3em; line-height: 1.8; margin: 0.8em 0; }
    .translation { color: #555; margin: 0.5em 0; }
    h2 { font-size: 1.2em; margin: 0.5em 0; }
    .jump-controls { margin: 10px 0; padding: 10px; background: #f0f0f0; border-radius: 5px; }
    .jump-controls label { font-weight: bold; margin-right: 10px; }
    .jump-controls input[type="number"] { width: 80px; padding: 5px; margin: 0 5px; }
    .jump-controls button { padding: 5px 15px; margin: 0 5px; cursor: pointer; }
  </style>
  <script>
    function filterEntries() {
      var kw = document.getElementById('kw').value.toLowerCase();
      document.querySelectorAll('.entry').forEach(function(e){
        var text = e.textContent.toLowerCase();
        var ok = true;
        if (kw && text.indexOf(kw) < 0) ok = false;
        e.style.display = ok ? 'block' : 'none';
      });
    }
    
    function jumpToAppNumber() {
      var lvl = document.getElementById('jumpLevel').value;
      var num = document.getElementById('appNumberInput').value;
      if (!lvl || !num) {
        alert('レベルと番号を入力してください');
        return;
      }
      var target = document.getElementById('entry-' + lvl + '-' + num);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        target.style.backgroundColor = '#ffffcc';
        setTimeout(function(){ target.style.backgroundColor=''; }, 2000);
      } else {
        alert('指定されたエントリが見つかりません');
      }
    }
    
    window.addEventListener('DOMContentLoaded', function(){
      document.getElementById('kw').oninput = filterEntries;
    });
  </script>
</head>
<body>
  <h1>HSK 例文集（アプリ表示順）</h1>
  <div class="controls">
    <input type="text" id="kw" placeholder="キーワード検索（フィルタリング）">
    <label>アプリ順番号ジャンプ:</label>
    <select id="jumpLevel">
      <option value="">レベル</option>
"""

# レベル選択肢を挿入
for lv in levels:
    html_head += f'\n      <option value="{lv}">Lv.{lv}</option>'

html_head += """
    </select>
    <input type="number" id="appNumberInput" min="1" placeholder="番号" style="width:90px">
    <button onclick="jumpToAppNumber()">ジャンプ</button>
  </div>
  <div id="entries">
"""

# 各エントリを書き出し（アプリの表示順序で）
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_head)
    
    # アプリ内の通し番号（レベル毎）と全体通し番号を追加
    global_index = 1
    app_number = 1
    current_level = None
    
    for _, row in df.iterrows():
        lvl     = row['レベル']
        ut      = row['単元']
        word    = row['単語(中文)']
        pin     = row['ピンイン']
        meaning = row['訳(日本語)']
        html_ruby       = row['例文(ルビHTML)']
        sentence_trans  = row['例文訳']
        group_num = row['グループ']
        
        if current_level != lvl:
            app_number = 1
            current_level = lvl
        
        f.write(f'''
    <div class="entry" id="entry-{lvl}-{app_number}" data-level="{lvl}" data-unit="{ut}">
      <h2>Lv.{lvl} - アプリ順#{app_number}：{word} （{pin}）</h2>
      <p class="meta-info">元No.{ut} / グループ{group_num}</p>
      <p class="meaning">訳：{meaning}</p>
      <p class="sentence">{html_ruby}</p>
      <p class="translation">{sentence_trans}</p>
    </div>''')
        app_number += 1
        global_index += 1
        
    f.write("""
  </div>
</body>
</html>""")

print("→ index.html を生成しました（アプリ表示順）。")
print(f"→ 総エントリ数: {len(df)}") 