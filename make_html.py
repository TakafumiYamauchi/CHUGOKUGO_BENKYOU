import pandas as pd

# CSV を読み込み
df = pd.read_csv('all_sentences_with_ruby.csv', dtype=str)

# ---- ここから並び替えロジックを修正 ----
# 元のCSVはデータベースで既に「レベル / グループ / 単元」順に並んでいる。
# ただし念のため、同じキーで再ソートしておく。
# これにより make_audio_player.py と完全に同じ並びになる。

df = df.sort_values(['レベル', 'グループ', '単元'], key=lambda col: col.astype(int))

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
    .controls { margin-bottom: 1em; }
    .controls select, .controls input { margin-right: 8px; }
    .meaning { font-weight: bold; margin: 0.5em 0; }
    .meta-info { font-size: 0.9em; color: #666; }
  </style>
  <script>
    function filterEntries() {
      var kw = document.getElementById('kw').value.toLowerCase();
      var lvl = document.getElementById('level').value;
      var unit = document.getElementById('unit').value;
      document.querySelectorAll('.entry').forEach(function(e){
        var text = e.textContent.toLowerCase();
        var ok = true;
        if (kw && text.indexOf(kw) < 0) ok = false;
        if (lvl && e.getAttribute('data-level') !== lvl) ok = false;
        if (unit && e.getAttribute('data-unit') !== unit) ok = false;
        e.style.display = ok ? 'block' : 'none';
      });
    }
    window.addEventListener('DOMContentLoaded', function(){
      document.querySelectorAll('.controls select, .controls input')
              .forEach(function(el){ el.oninput = filterEntries; });
    });
  </script>
</head>
<body>
  <h1>HSK 例文集（アプリ表示順）</h1>
  <div class="controls">
    <input type="text" id="kw" placeholder="キーワード検索">
    <select id="level">
      <option value="">全Lv.</option>"""
# Lv. の選択肢
levels = sorted(df['レベル'].dropna().unique(), key=lambda x: int(x))
for lv in levels:
    html_head += f'\n      <option value="{lv}">Lv.{lv}</option>'
html_head += """
    </select>
    <select id="unit">
      <option value="">全No.</option>"""
# No. の選択肢（元の単元番号）
units = sorted(df['単元'].dropna().unique(), key=lambda x: int(x))
for ut in units:
    html_head += f'\n      <option value="{ut}">No.{ut}</option>'
html_head += """
    </select>
  </div>
  <div id="entries">
"""

# 各エントリを書き出し（アプリの表示順序で）
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_head)
    
    # アプリ内の通し番号を追加
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
        
        # レベルが変わったら番号をリセット
        if current_level != lvl:
            app_number = 1
            current_level = lvl
        
        # グループ番号を計算
        unit_int = int(ut)
        group_num = ((unit_int - 1) % 71) + 1
        
        f.write(f'''
    <div class="entry" data-level="{lvl}" data-unit="{ut}">
      <h2>Lv.{lvl} - アプリ順#{app_number}：{word} （{pin}）</h2>
      <p class="meta-info">元No.{ut} / グループ{group_num}</p>
      <p class="meaning">訳：{meaning}</p>
      <p class="sentence">{html_ruby}</p>
      <p class="translation">{sentence_trans}</p>
    </div>''')
        app_number += 1
        
    f.write("""
  </div>
</body>
</html>""")

print("→ index.html を生成しました（アプリ表示順）。")
print(f"→ 総エントリ数: {len(df)}") 