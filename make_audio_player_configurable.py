#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import pandas as pd
import os

# ========================================
# 設定パラメータ（重要度順）
# ========================================

# 1. テキストサイズ設定（モバイル視認性のため最重要）
CHINESE_WORD_SIZE = "36px"      # 中国語単語のサイズ（デフォルト: 32px → 36px）
CHINESE_PINYIN_SIZE = "26px"    # ピンインのサイズ（デフォルト: 22px → 26px）
JAPANESE_MEANING_SIZE = "22px"  # 日本語訳のサイズ（デフォルト: 20px → 22px）
CHINESE_SENTENCE_SIZE = "24px"  # 例文(中国語)のサイズ（デフォルト: 18px → 20px）
JAPANESE_SENTENCE_SIZE = "20px" # 例文訳(日本語)のサイズ（デフォルト: 16px → 18px）

# 2. 再生設定のデフォルト値
DEFAULT_CHINESE_SPEED = "0.6"   # 中国語のデフォルト再生速度
DEFAULT_JAPANESE_SPEED = "1.6"  # 日本語のデフォルト再生速度
DEFAULT_REPEAT_COUNT = "5"      # 例文のデフォルト繰り返し回数
AUDIO_INTERVAL_MS = 20          # 音声再生間のインターバル（ミリ秒）
SENTENCE_REPEAT_INTERVAL_MS = 20  # 例文リピート間のインターバル（ミリ秒）

# 3. ボタンとコントロールのサイズ
BUTTON_PADDING = "12px 16px"    # ボタンの内側余白
BUTTON_FONT_SIZE = "15px"       # ボタンの文字サイズ
MAIN_BUTTON_PADDING = "15px"    # メインボタン（再生等）の内側余白
MAIN_BUTTON_FONT_SIZE = "17px"  # メインボタンの文字サイズ

# 4. 色設定
PRIMARY_COLOR = "#007AFF"       # メインカラー（iOS風ブルー）
SUCCESS_COLOR = "#34C759"       # 成功/再生ボタンの色
WARNING_COLOR = "#FF9500"       # 警告/一時停止ボタンの色
DANGER_COLOR = "#FF3B30"        # 危険/停止ボタンの色
BACKGROUND_COLOR = "#f5f5f5"    # 背景色
CARD_BACKGROUND = "#fff"        # カードの背景色

# 5. レイアウト設定
MOBILE_MAX_WIDTH = "600px"      # モバイル表示の最大幅
CARD_BORDER_RADIUS = "12px"     # カードの角丸
CARD_PADDING = "15px"           # カードの内側余白
SECTION_MARGIN = "15px"         # セクション間のマージン

# 6. アニメーション設定
TRANSITION_DURATION = "0.0s"    # トランジション時間
PULSE_DURATION = "1.5s"         # 再生中のパルスアニメーション時間

# 7. 範囲指定再生の設定
RANGE_BACKGROUND_COLOR = "#FFF3E0"  # 範囲指定セクションの背景色
RANGE_BORDER_COLOR = "#FFB74D"      # 範囲指定セクションの枠線色
RANGE_DEFAULT_REPEAT = "3"          # 範囲指定のデフォルト繰り返し回数

# 8. 検索結果表示設定
SEARCH_RESULT_MAX_HEIGHT = "300px"  # 検索結果の最大高さ
SEARCH_RESULT_DISPLAY_COUNT = 10    # 検索結果の表示件数

# 9. スライダー設定
SLIDER_TRACK_HEIGHT = "4px"         # スライダートラックの高さ
SLIDER_THUMB_SIZE = "28px"          # スライダーつまみのサイズ

# 10. フォント設定
FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'Hiragino Sans', sans-serif"

# ========================================
# データ処理部分
# ========================================

print("→ 日本語音声を含むCSVを再生成中...")
csv_export_script = """
cd ~/Buzoo_App_Data/full_buzoo_data/app_flutter/databases
sqlite3 SprixDB << 'EOF'
.headers on
.mode csv
.once /home/yamada/Buzoo_App_Data/all_sentences.csv

SELECT
  l.level                         AS "レベル",
  w.unit                          AS "単元",
  w.unit_group                    AS "グループ",
  w.chinese_word                  AS "単語(中文)",
  w.chinese_pinyin                AS "ピンイン",
  w.japanese_word                 AS "訳(日本語)",
  w.chinese_sentence              AS "例文(中文)",
  w.chinese_sentence_pinyin       AS "例文(ピンイン)",
  w.japanese_sentence             AS "例文訳",
  w.chinese_word_sound            AS "単語音声ファイル",
  w.japanese_word_sound           AS "日本語音声ファイル",
  w.chinese_sentence_sound        AS "例文音声ファイル"
FROM tbl_word w
JOIN tbl_level l
  ON w.level_id = l.id
ORDER BY w.level_id, w.unit_group, w.unit;
EOF
"""

subprocess.run(csv_export_script, shell=True)
print("→ CSVエクスポート完了")

# ルビ付きCSVを再生成
print("→ ルビ付きCSVを再生成中...")
subprocess.run([sys.executable, "make_ruby.py"])
print("→ ルビ付きCSV生成完了")

# CSV を読み込み
df = pd.read_csv('all_sentences_with_ruby.csv', dtype=str)

# データベースで既にアプリ順（unit_group順）にソートされているので、そのまま使用
print(f"→ データ読み込み完了。最初の10単語: {df['単語(中文)'].head(10).tolist()}")

# 音声ファイルのパスを生成する関数
def get_audio_path(level, filename):
    """レベルとファイル名から実際のパスを生成"""
    if pd.isna(filename) or filename == '':
        return None
    # 拡張子を小文字に変換（.MP3 → .mp3）
    filename_lower = filename.replace('.MP3', '.mp3')
    return f"external_storage_data/files/Sprix/Sound_level_{level}/{filename_lower}"

# ========================================
# HTML生成部分
# ========================================

html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>HSK 音声学習プレイヤー</title>
  <style>
    /* ========================================
       カスタマイズ可能な変数
       ======================================== */
    :root {{
      /* テキストサイズ */
      --chinese-word-size: {CHINESE_WORD_SIZE};
      --chinese-pinyin-size: {CHINESE_PINYIN_SIZE};
      --japanese-meaning-size: {JAPANESE_MEANING_SIZE};
      --chinese-sentence-size: {CHINESE_SENTENCE_SIZE};
      --japanese-sentence-size: {JAPANESE_SENTENCE_SIZE};
      
      /* 色設定 */
      --primary-color: {PRIMARY_COLOR};
      --success-color: {SUCCESS_COLOR};
      --warning-color: {WARNING_COLOR};
      --danger-color: {DANGER_COLOR};
      --background-color: {BACKGROUND_COLOR};
      --card-background: {CARD_BACKGROUND};
      
      /* レイアウト */
      --mobile-max-width: {MOBILE_MAX_WIDTH};
      --card-border-radius: {CARD_BORDER_RADIUS};
      --card-padding: {CARD_PADDING};
      --section-margin: {SECTION_MARGIN};
      
      /* アニメーション */
      --transition-duration: {TRANSITION_DURATION};
      --pulse-duration: {PULSE_DURATION};
    }}
    
    * {{
      box-sizing: border-box;
      -webkit-tap-highlight-color: transparent;
    }}
    
    body {{ 
      font-family: {FONT_FAMILY};
      margin: 0;
      padding: 0;
      background: var(--background-color);
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }}
    
    .app-container {{
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    
    .header {{
      background: var(--card-background);
      padding: 15px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    
    h1 {{
      font-size: 20px;
      margin: 0;
      text-align: center;
      color: #333;
      font-weight: 600;
    }}
    
    .main-content {{
      flex: 1;
      padding: 10px;
      padding-bottom: 80px;
    }}
    
    .controls {{ 
      background: var(--card-background);
      border-radius: var(--card-border-radius);
      padding: var(--card-padding);
      margin-bottom: var(--section-margin);
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    
    .player-status {{ 
      background: var(--card-background);
      border-radius: var(--card-border-radius);
      padding: 20px;
      margin-bottom: var(--section-margin);
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    
    .current-word {{ 
      font-size: var(--chinese-word-size);
      margin: 10px 0;
      font-weight: bold;
      color: #1a1a1a;
      text-align: center;
      word-break: break-word;
      line-height: 1.4;
    }}
    
    .current-info {{ 
      margin: 10px 0;
      line-height: 1.6;
      text-align: center;
    }}
    
    .current-info.pinyin {{ 
      font-size: var(--chinese-pinyin-size);
      color: #666;
      margin-bottom: 5px;
      font-weight: 500;
    }}
    
    .current-info.meaning {{ 
      font-size: var(--japanese-meaning-size);
      color: #444;
      font-weight: 500;
      margin-bottom: 15px;
    }}
    
    .current-info.sentence {{ 
      margin-top: 20px;
      padding: 15px;
      background: #f8f9fa;
      border-radius: 8px;
      font-size: var(--chinese-sentence-size);
      line-height: 1.8;
      text-align: left;
    }}
    
    .current-info.translation {{ 
      color: #666;
      font-style: italic;
      font-size: var(--japanese-sentence-size);
      line-height: 1.6;
      text-align: left;
      margin-top: 10px;
    }}
    
    /* メインコントロールボタン */
    .main-controls {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: var(--card-background);
      padding: 15px;
      box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
      z-index: 100;
    }}
    
    .control-buttons {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      max-width: 400px;
      margin: 0 auto;
    }}
    
    button {{
      padding: {BUTTON_PADDING};
      font-size: {BUTTON_FONT_SIZE};
      font-weight: 500;
      cursor: pointer;
      border: none;
      border-radius: 8px;
      background: var(--primary-color);
      color: white;
      transition: all var(--transition-duration);
      -webkit-appearance: none;
      touch-action: manipulation;
    }}
    
    button:active {{
      transform: scale(0.95);
    }}
    
    button:disabled {{
      opacity: 0.4;
      background: #C7C7CC;
    }}
    
    .play-button {{
      background: var(--success-color);
      grid-column: span 3;
      font-size: {MAIN_BUTTON_FONT_SIZE};
      padding: {MAIN_BUTTON_PADDING};
    }}
    
    .play-button:active {{
      background: #248A3D;
    }}
    
    .pause-button {{
      background: var(--warning-color);
    }}
    
    .pause-button:active {{
      background: #C93400;
    }}
    
    .stop-button {{
      background: var(--danger-color);
    }}
    
    .stop-button:active {{
      background: #D70015;
    }}
    
    /* コントロールセクション */
    .control-section {{
      margin-bottom: 20px;
    }}
    
    .control-section h3 {{
      font-size: 16px;
      color: #666;
      margin: 0 0 10px 0;
      font-weight: 600;
    }}
    
    /* スライダー */
    .slider-control {{
      margin: 15px 0;
    }}
    
    .slider-label {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 15px;
      color: #333;
    }}
    
    .slider-value {{
      font-weight: 600;
      color: var(--primary-color);
      min-width: 40px;
      text-align: right;
    }}
    
    input[type="range"] {{
      width: 100%;
      height: {SLIDER_THUMB_SIZE};
      -webkit-appearance: none;
      background: transparent;
      margin: 0;
    }}
    
    input[type="range"]::-webkit-slider-track {{
      width: 100%;
      height: {SLIDER_TRACK_HEIGHT};
      background: #E5E5EA;
      border-radius: 2px;
    }}
    
    input[type="range"]::-webkit-slider-thumb {{
      -webkit-appearance: none;
      width: {SLIDER_THUMB_SIZE};
      height: {SLIDER_THUMB_SIZE};
      background: #fff;
      border: 2px solid var(--primary-color);
      border-radius: 50%;
      cursor: pointer;
      margin-top: -12px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }}
    
    /* 入力フィールド */
    .input-group {{
      margin: 15px 0;
    }}
    
    .input-group label {{
      display: block;
      font-size: 15px;
      color: #666;
      margin-bottom: 8px;
      font-weight: 500;
    }}
    
    .input-wrapper {{
      display: flex;
      gap: 8px;
    }}
    
    input[type="text"],
    input[type="number"],
    select {{
      flex: 1;
      padding: 12px;
      font-size: 16px;
      border: 1px solid #C7C7CC;
      border-radius: 8px;
      background: #fff;
      -webkit-appearance: none;
    }}
    
    input[type="text"]:focus,
    input[type="number"]:focus,
    select:focus {{
      outline: none;
      border-color: var(--primary-color);
    }}
    
    select {{
      background-image: url('data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%2714%27%20height%3D%278%27%20viewBox%3D%270%200%2014%208%27%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%3E%3Cpath%20d%3D%27M1%201l6%206%206-6%27%20stroke%3D%27%23C7C7CC%27%20stroke-width%3D%272%27%20fill%3D%27none%27%20fill-rule%3D%27evenodd%27%2F%3E%3C%2Fsvg%3E');
      background-repeat: no-repeat;
      background-position: right 12px center;
      padding-right: 32px;
    }}
    
    /* 検索結果 */
    .search-results {{
      margin: 15px 0;
      padding: 15px;
      background: #f8f9fa;
      border-radius: 8px;
      display: none;
      max-height: {SEARCH_RESULT_MAX_HEIGHT};
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
    }}
    
    .search-results.active {{
      display: block;
    }}
    
    .search-results h4 {{
      margin: 0 0 10px 0;
      color: #666;
      font-size: 14px;
      font-weight: 600;
    }}
    
    .search-result-item {{
      padding: 12px;
      margin: 8px 0;
      background: white;
      border: 1px solid #E5E5EA;
      border-radius: 8px;
      cursor: pointer;
      transition: all var(--transition-duration);
    }}
    
    .search-result-item:active {{
      background: var(--primary-color);
      color: white;
    }}
    
    .search-result-item:active .meaning-info {{
      color: rgba(255,255,255,0.8);
    }}
    
    .search-result-item .word-info {{
      font-weight: 600;
      color: #333;
      font-size: 16px;
    }}
    
    .search-result-item .meaning-info {{
      color: #666;
      font-size: 14px;
      margin-top: 4px;
    }}
    
    /* 進捗表示 */
    .progress {{
      text-align: center;
      font-size: 16px;
      color: #666;
      margin-top: 15px;
      font-weight: 500;
    }}
    
    .progress-numbers {{
      color: var(--primary-color);
      font-weight: 600;
    }}
    
    /* 範囲設定 */
    .range-controls {{
      background: {RANGE_BACKGROUND_COLOR};
      border: 1px solid {RANGE_BORDER_COLOR};
      border-radius: 8px;
      padding: 15px;
      margin-top: 10px;
    }}
    
    .range-inputs {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 15px;
    }}
    
    .range-input-group {{
      display: flex;
      flex-direction: column;
    }}
    
    .range-input-group label {{
      font-size: 13px;
      color: #666;
      margin-bottom: 5px;
    }}
    
    .range-info {{
      text-align: center;
      font-weight: 600;
      color: var(--warning-color);
      margin-top: 10px;
      font-size: 14px;
    }}
    
    /* コラプシブルセクション */
    .collapsible {{
      cursor: pointer;
      padding: 10px 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
      color: #333;
    }}
    
    .collapsible:after {{
      content: '▼';
      font-size: 12px;
      color: #C7C7CC;
      transition: transform var(--transition-duration);
    }}
    
    .collapsible.active:after {{
      transform: rotate(180deg);
    }}
    
    .collapsible-content {{
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.3s ease;
    }}
    
    .collapsible-content.show {{
      max-height: 1000px;
    }}
    
    /* タブレット対応 */
    @media (min-width: 768px) {{
      .main-content {{
        max-width: var(--mobile-max-width);
        margin: 0 auto;
      }}
      
      .main-controls {{
        max-width: var(--mobile-max-width);
        left: 50%;
        transform: translateX(-50%);
      }}
    }}
    
    /* ルビのスタイル */
    ruby {{
      ruby-position: over;
    }}
    
    rt {{
      font-size: 0.5em;
      color: #999;
      font-weight: normal;
    }}
    
    /* アニメーション */
    @keyframes pulse {{
      0% {{ opacity: 1; }}
      50% {{ opacity: 0.6; }}
      100% {{ opacity: 1; }}
    }}
    
    .playing-indicator {{
      animation: pulse var(--pulse-duration) infinite;
    }}
  </style>
</head>
<body>
  <div class="app-container">
    <div class="header">
      <h1>HSK 音声学習プレイヤー</h1>
    </div>
    
    <div class="main-content">
      <div class="player-status">
        <div class="current-word" id="currentWord">-</div>
        <div class="current-info pinyin" id="currentPinyin">-</div>
        <div class="current-info meaning" id="currentMeaning">-</div>
        <div class="current-info sentence" id="currentSentence">-</div>
        <div class="current-info translation" id="currentTranslation">-</div>
        <div class="progress">
          進捗: <span class="progress-numbers"><span id="currentIndex">0</span> / <span id="totalWords">0</span></span>
        </div>
      </div>
      
      <div class="controls">
        <div class="control-section">
          <h3>再生設定</h3>
          
          <div class="slider-control">
            <div class="slider-label">
              <span>中国語速度</span>
              <span class="slider-value" id="speedValue">{DEFAULT_CHINESE_SPEED}</span>
            </div>
            <input type="range" id="speedRange" min="0.5" max="2" step="0.05" value="{DEFAULT_CHINESE_SPEED}" oninput="changeSpeed()">
          </div>
          
          <div class="slider-control">
            <div class="slider-label">
              <span>日本語速度</span>
              <span class="slider-value" id="japaneseSpeedValue">{DEFAULT_JAPANESE_SPEED}</span>
            </div>
            <input type="range" id="japaneseSpeedRange" min="0.5" max="2" step="0.05" value="{DEFAULT_JAPANESE_SPEED}" oninput="changeJapaneseSpeed()">
          </div>
          
          <div class="slider-control">
            <div class="slider-label">
              <span>例文繰り返し</span>
              <span class="slider-value"><span id="repeatValue">{DEFAULT_REPEAT_COUNT}</span>回</span>
            </div>
            <input type="range" id="repeatRange" min="1" max="5" step="1" value="{DEFAULT_REPEAT_COUNT}" oninput="changeRepeatCount()">
          </div>
        </div>
        
        <div class="control-section">
          <h3>学習範囲</h3>
          
          <div class="input-group">
            <label>レベル選択</label>
            <select id="levelSelect" onchange="filterByLevel()">
              <option value="">全レベル</option>
"""

# レベルオプションを追加
levels = sorted(df['レベル'].dropna().unique())
for level in levels:
    html_content += f'              <option value="{level}">レベル {level}</option>\n'

html_content += f"""            </select>
          </div>
          
          <div class="input-group">
            <label>キーワード検索</label>
            <div class="input-wrapper">
              <input type="text" id="searchInput" placeholder="単語、ピンイン、例文など">
              <button onclick="searchWords()">検索</button>
            </div>
          </div>
          
          <div id="searchResults" class="search-results">
            <h4>検索結果: <span id="searchResultCount">0</span>件</h4>
            <div id="searchResultList"></div>
          </div>
        </div>
        
        <div class="control-section">
          <h3>範囲指定再生</h3>
          <div class="range-controls">
            <div style="font-size: 13px; color: #666; margin-bottom: 10px;">
              例: レベル4の120〜150番を繰り返し学習
            </div>
            <div class="range-inputs">
              <div class="range-input-group">
                <label>開始番号</label>
                <input type="number" id="rangeStartInput" min="1" max="{len(df)}" placeholder="120">
              </div>
              <div class="range-input-group">
                <label>終了番号</label>
                <input type="number" id="rangeEndInput" min="1" max="{len(df)}" placeholder="150">
              </div>
            </div>
            <div class="input-group">
              <label>繰り返し回数</label>
              <input type="number" id="rangeRepeatInput" min="1" max="10" value="{RANGE_DEFAULT_REPEAT}">
            </div>
            <div class="input-wrapper" style="gap: 8px;">
              <button onclick="setRange()" style="background: var(--warning-color);">範囲設定</button>
              <button onclick="clearRange()">クリア</button>
            </div>
            <div id="rangeInfo" class="range-info"></div>
          </div>
        </div>
        
        <div class="control-section">
          <div class="collapsible" onclick="toggleCollapsible(this)">
            <span>その他の設定</span>
          </div>
          <div class="collapsible-content">
            <div class="input-group">
              <label>単語番号へジャンプ</label>
              <div class="input-wrapper">
                <input type="number" id="wordNumberInput" min="1" max="{len(df)}" placeholder="番号">
                <button onclick="goToWordByNumber()">移動</button>
              </div>
            </div>
            
            <div class="input-group">
              <label>開始位置選択</label>
              <div class="input-wrapper">
                <select id="startUnitSelect">
                  <option value="">選択してください...</option>
                </select>
                <button onclick="goToSelectedUnit()">移動</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="main-controls">
      <div class="control-buttons">
        <button id="playBtn" class="play-button" onclick="startPlayback()">▶ 再生開始</button>
        <button id="prevBtn" onclick="prevWord()" disabled>◀ 前へ</button>
        <button id="pauseBtn" class="pause-button" onclick="pausePlayback()" disabled>⏸ 一時停止</button>
        <button id="nextBtn" onclick="nextWord()" disabled>次へ ▶</button>
        <button id="stopBtn" class="stop-button" onclick="stopPlayback()" disabled style="grid-column: span 2;">⏹ 停止</button>
      </div>
    </div>
  </div>
  
  <audio id="audioPlayer" onended="onAudioEnded()"></audio>
  
  <script>
    // ========================================
    // 設定値（JavaScriptから変更可能）
    // ========================================
    const CONFIG = {{
      defaultChineseSpeed: {DEFAULT_CHINESE_SPEED},
      defaultJapaneseSpeed: {DEFAULT_JAPANESE_SPEED},
      defaultRepeatCount: {DEFAULT_REPEAT_COUNT},
      searchResultDisplayCount: {SEARCH_RESULT_DISPLAY_COUNT},
      rangeDefaultRepeat: {RANGE_DEFAULT_REPEAT},
      audioIntervalMs: {AUDIO_INTERVAL_MS},
      sentenceRepeatIntervalMs: {SENTENCE_REPEAT_INTERVAL_MS}
    }};
    
    const allWords = [
"""

# JavaScriptの単語データ配列を生成
for idx, row in df.iterrows():
    word_sound = get_audio_path(row['レベル'], row['単語音声ファイル'])
    japanese_sound = get_audio_path(row['レベル'], row['日本語音声ファイル']) if '日本語音声ファイル' in row else None
    sentence_sound = get_audio_path(row['レベル'], row['例文音声ファイル'])
    
    word = str(row['単語(中文)']).replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
    pinyin = str(row['ピンイン']).replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
    meaning = str(row['訳(日本語)']).replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
    sentence = str(row['例文(ルビHTML)']).replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
    translation = str(row['例文訳']).replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
    
    html_content += f"""      {{
        level: '{row['レベル']}',
        unit: '{row['単元']}',
        group: '{row['グループ']}',
        word: '{word}',
        pinyin: '{pinyin}',
        meaning: '{meaning}',
        sentence: '{sentence}',
        translation: '{translation}',
        wordSound: '{word_sound if word_sound else ""}',
        japaneseSound: '{japanese_sound if japanese_sound else ""}',
        sentenceSound: '{sentence_sound if sentence_sound else ""}'
      }},
"""

html_content += f"""    ];
    
    let words = [...allWords];
    let currentWordIndex = 0;
    let isPlaying = false;
    let isPaused = false;
    let currentPhase = 0; // 0: 単語音声, 1: 日本語音声, 2: 例文音声
    let sentenceRepeatCount = 0;
    let maxSentenceRepeat = CONFIG.defaultRepeatCount;
    let rangeStartIndex = -1; // 範囲指定の開始インデックス
    let rangeEndIndex = -1; // 範囲指定の終了インデックス
    let rangeRepeatCount = 0; // 範囲の繰り返し回数
    let maxRangeRepeat = CONFIG.rangeDefaultRepeat; // 範囲の最大繰り返し回数
    let userSpecifiedStartIndex = -1; // ユーザーが指定した開始位置を記憶
    
    const audioPlayer = document.getElementById('audioPlayer');
    const startUnitSelect = document.getElementById('startUnitSelect');
    
    // 設定保存キー
    const SETTINGS_KEY = 'hskPlayerSettings';
    
    function debugLog(message) {{ console.log(`[HSK Player] ${{message}}`); }}
    
    // 設定を保存する関数
    function saveSettings() {{
      const settings = {{
        level: document.getElementById('levelSelect').value,
        chineseSpeed: document.getElementById('speedRange').value,
        japaneseSpeed: document.getElementById('japaneseSpeedRange').value,
        repeatCount: document.getElementById('repeatRange').value,
        searchKeyword: document.getElementById('searchInput').value,
        wordNumber: document.getElementById('wordNumberInput').value,
        rangeStart: document.getElementById('rangeStartInput').value,
        rangeEnd: document.getElementById('rangeEndInput').value,
        rangeRepeat: document.getElementById('rangeRepeatInput').value,
        userSpecifiedStartIndex: userSpecifiedStartIndex,
        currentWordIndex: currentWordIndex
      }};
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
      debugLog('設定を保存しました: ' + JSON.stringify(settings));
    }}
    
    // 設定を読み込む関数
    function loadSettings() {{
      const savedSettings = localStorage.getItem(SETTINGS_KEY);
      if (!savedSettings) {{
        debugLog('保存された設定がありません');
        return;
      }}
      
      try {{
        const settings = JSON.parse(savedSettings);
        debugLog('設定を読み込みました: ' + JSON.stringify(settings));
        
        // レベル選択を復元（最優先）
        if (settings.level !== undefined) {{
          document.getElementById('levelSelect').value = settings.level;
          filterByLevel(); // フィルターを適用
        }}
        
        // スピード設定を復元
        if (settings.chineseSpeed !== undefined) {{
          document.getElementById('speedRange').value = settings.chineseSpeed;
          document.getElementById('speedValue').textContent = settings.chineseSpeed;
        }}
        if (settings.japaneseSpeed !== undefined) {{
          document.getElementById('japaneseSpeedRange').value = settings.japaneseSpeed;
          document.getElementById('japaneseSpeedValue').textContent = settings.japaneseSpeed;
        }}
        
        // 再生回数を復元
        if (settings.repeatCount !== undefined) {{
          document.getElementById('repeatRange').value = settings.repeatCount;
          document.getElementById('repeatValue').textContent = settings.repeatCount;
          maxSentenceRepeat = parseInt(settings.repeatCount);
        }}
        
        // 検索キーワードを復元
        if (settings.searchKeyword !== undefined && settings.searchKeyword !== '') {{
          document.getElementById('searchInput').value = settings.searchKeyword;
          searchWords(); // 検索を実行
        }}
        
        // 範囲設定を復元
        if (settings.rangeStart !== undefined) {{
          document.getElementById('rangeStartInput').value = settings.rangeStart;
        }}
        if (settings.rangeEnd !== undefined) {{
          document.getElementById('rangeEndInput').value = settings.rangeEnd;
        }}
        if (settings.rangeRepeat !== undefined) {{
          document.getElementById('rangeRepeatInput').value = settings.rangeRepeat;
        }}
        
        // ユーザー指定位置を復元
        if (settings.userSpecifiedStartIndex !== undefined && settings.userSpecifiedStartIndex >= 0) {{
          userSpecifiedStartIndex = settings.userSpecifiedStartIndex;
          currentWordIndex = Math.min(userSpecifiedStartIndex, words.length - 1);
        }} else if (settings.currentWordIndex !== undefined && settings.currentWordIndex >= 0) {{
          currentWordIndex = Math.min(settings.currentWordIndex, words.length - 1);
        }}
        
        updateDisplay();
      }} catch (e) {{
        console.error('設定の読み込みに失敗しました:', e);
      }}
    }}
    
    // コラプシブルセクションのトグル
    function toggleCollapsible(element) {{
      element.classList.toggle('active');
      const content = element.nextElementSibling;
      content.classList.toggle('show');
    }}
    
    function updateDisplay() {{
      if (currentWordIndex < 0 || currentWordIndex >= words.length) {{
        debugLog('updateDisplay: 無効なcurrentWordIndexです');
        return;
      }}
      const word = words[currentWordIndex];
      document.getElementById('currentWord').textContent = word.word;
      document.getElementById('currentPinyin').textContent = word.pinyin;
      document.getElementById('currentMeaning').textContent = word.meaning;
      document.getElementById('currentSentence').innerHTML = word.sentence;
      document.getElementById('currentTranslation').textContent = word.translation;
      document.getElementById('currentIndex').textContent = currentWordIndex + 1;
      document.getElementById('totalWords').textContent = words.length;
      
      // 範囲指定の表示更新
      if (rangeStartIndex >= 0 && rangeEndIndex >= 0) {{
        document.getElementById('rangeInfo').textContent = 
          `${{rangeStartIndex + 1}}〜${{rangeEndIndex + 1}}番 (${{rangeRepeatCount + 1}}/${{maxRangeRepeat}}回目)`;
      }} else {{
        document.getElementById('rangeInfo').textContent = '';
      }}
    }}
    
    function populateStartUnitSelect() {{
        const selectedLevel = document.getElementById('levelSelect').value;
        startUnitSelect.innerHTML = '<option value="">選択してください...</option>';
        const filteredWords = selectedLevel === '' ? allWords : allWords.filter(w => w.level === selectedLevel);
        
        // 現在のwordsリストに基づいて選択肢を作成（フィルターや検索結果を反映）
        const displayWords = words; // 現在表示中のリスト
        
        // 10単語ごとにグループ化して表示
        for (let i = 0; i < displayWords.length; i += 10) {{
            const endIndex = Math.min(i + 9, displayWords.length - 1);
            const startWord = displayWords[i].word.substring(0, 8);
            const endWord = displayWords[endIndex].word.substring(0, 8);
            
            const option = document.createElement('option');
            option.value = i; // インデックスを値として使用
            option.textContent = `${{i + 1}}〜${{endIndex + 1}}番: ${{startWord}}...〜${{endWord}}...`;
            startUnitSelect.appendChild(option);
        }}
    }}

    function startPlayback() {{
      debugLog('再生開始');
      
      if (!isPaused) {{
        // ユーザーが指定した開始位置を優先
        if (userSpecifiedStartIndex >= 0 && userSpecifiedStartIndex < words.length) {{
          currentWordIndex = userSpecifiedStartIndex;
          debugLog(`ユーザー指定位置から開始: ${{currentWordIndex + 1}}番`);
        }} else {{
          // セレクトの値をインデックスとして扱う
          const selectedIndex = parseInt(startUnitSelect.value, 10);
          if (!isNaN(selectedIndex) && selectedIndex >= 0 && selectedIndex < words.length) {{
            currentWordIndex = selectedIndex;
            debugLog(`リスト選択位置から開始: ${{currentWordIndex + 1}}番`);
          }}
        }}
      }}

      isPlaying = true;
      isPaused = false;
      document.getElementById('playBtn').disabled = true;
      document.getElementById('playBtn').textContent = '▶ 再生中...';
      document.getElementById('pauseBtn').disabled = false;
      document.getElementById('stopBtn').disabled = false;
      document.getElementById('prevBtn').disabled = false;
      document.getElementById('nextBtn').disabled = false;
      
      // 再生中インジケーター
      document.querySelector('.player-status').classList.add('playing-indicator');
      
      playCurrentPhase();
    }}
    
    function pausePlayback() {{
      debugLog('一時停止');
      isPaused = true;
      audioPlayer.pause();
      document.getElementById('playBtn').disabled = false;
      document.getElementById('playBtn').textContent = '▶ 再生再開';
      document.getElementById('pauseBtn').disabled = true;
      document.querySelector('.player-status').classList.remove('playing-indicator');
    }}
    
    function stopPlayback() {{
      debugLog('停止');
      isPlaying = false;
      isPaused = false;
      currentPhase = 0;
      sentenceRepeatCount = 0;
      audioPlayer.pause();
      audioPlayer.currentTime = 0;
      
      document.getElementById('playBtn').disabled = false;
      document.getElementById('playBtn').textContent = '▶ 再生開始';
      document.getElementById('pauseBtn').disabled = true;
      document.getElementById('stopBtn').disabled = true;
      document.getElementById('prevBtn').disabled = true;
      document.getElementById('nextBtn').disabled = true;
      document.querySelector('.player-status').classList.remove('playing-indicator');
      updateDisplay();
    }}
    
    function prevWord() {{
      debugLog('前の単語へ');
      currentPhase = 0;
      sentenceRepeatCount = 0;
      currentWordIndex--;
      if (currentWordIndex < 0) {{
        currentWordIndex = words.length - 1;
      }}
      saveSettings(); // 位置を保存
      if (isPlaying && !isPaused) {{
        playCurrentPhase();
      }} else {{
        updateDisplay();
      }}
    }}
    
    function nextWord() {{
      debugLog('次の単語へ');
      currentPhase = 0;
      sentenceRepeatCount = 0;
      currentWordIndex++;
      
      // 範囲指定がある場合の処理
      if (rangeStartIndex >= 0 && rangeEndIndex >= 0) {{
        if (currentWordIndex > rangeEndIndex) {{
          rangeRepeatCount++;
          if (rangeRepeatCount < maxRangeRepeat) {{
            // 範囲の最初に戻る
            currentWordIndex = rangeStartIndex;
            debugLog(`範囲繰り返し: ${{rangeRepeatCount + 1}}/${{maxRangeRepeat}}回目開始`);
          }} else {{
            // 範囲繰り返し完了 – 再生停止
            debugLog('範囲繰り返し完了 (停止)');
            stopPlayback();
            alert('範囲指定の繰り返し再生が完了しました！');
            return;
          }}
        }}
      }} else {{
        if (currentWordIndex >= words.length) {{
          currentWordIndex = 0;
        }}
      }}
      
      saveSettings(); // 位置を保存
      if (isPlaying && !isPaused) {{
        playCurrentPhase();
      }} else {{
        updateDisplay();
      }}
    }}
    
    function playCurrentPhase() {{
      if (!isPlaying || isPaused) return;
      
      const chineseSpeed = parseFloat(document.getElementById('speedRange').value);
      const japaneseSpeed = parseFloat(document.getElementById('japaneseSpeedRange').value);

      updateDisplay();
      const word = words[currentWordIndex];
      debugLog(`現在の単語: ${{word.word}}, フェーズ: ${{currentPhase}}`);
      
      switch (currentPhase) {{
        case 0: // 単語音声 (中国語)
          if (word.wordSound) {{
            debugLog(`単語音声を再生: ${{word.wordSound}}`);
            audioPlayer.src = word.wordSound;
            audioPlayer.playbackRate = chineseSpeed;
            audioPlayer.play().then(() => {{
              debugLog('単語音声の再生開始成功');
            }}).catch(error => {{
              console.error('単語音声の再生エラー:', error);
              debugLog(`エラー: ${{error.message}}`);
              // エラーの場合は次のフェーズへ
              currentPhase++;
              setTimeout(() => playCurrentPhase(), CONFIG.audioIntervalMs);
            }});
          }} else {{
            debugLog('単語音声ファイルがありません');
            currentPhase++;
            setTimeout(() => playCurrentPhase(), CONFIG.audioIntervalMs);
          }}
          break;
          
        case 1: // 日本語音声
          if (word.japaneseSound) {{
            debugLog(`日本語音声を再生: ${{word.japaneseSound}}`);
            audioPlayer.src = word.japaneseSound;
            audioPlayer.playbackRate = japaneseSpeed;
            audioPlayer.play().then(() => {{
              debugLog('日本語音声の再生開始成功');
            }}).catch(error => {{
              console.error('日本語音声の再生エラー:', error);
              debugLog(`エラー: ${{error.message}}`);
              // エラーの場合は次のフェーズへ
              currentPhase++;
              setTimeout(() => playCurrentPhase(), CONFIG.audioIntervalMs);
            }});
          }} else {{
            debugLog('日本語音声ファイルがありません');
            currentPhase++;
            setTimeout(() => playCurrentPhase(), CONFIG.audioIntervalMs);
          }}
          break;
          
        case 2: // 例文音声 (中国語)
          if (word.sentenceSound) {{
            debugLog(`例文音声を再生: ${{word.sentenceSound}} (${{sentenceRepeatCount + 1}}/${{maxSentenceRepeat}}回目)`);
            audioPlayer.src = word.sentenceSound;
            audioPlayer.playbackRate = chineseSpeed;
            audioPlayer.play().then(() => {{
              debugLog('例文音声の再生開始成功');
            }}).catch(error => {{
              console.error('例文音声の再生エラー:', error);
              debugLog(`エラー: ${{error.message}}`);
              // エラーの場合は次の単語へ
              nextWord();
            }});
          }} else {{
            debugLog('例文音声ファイルがありません');
            nextWord();
          }}
          break;
      }}
    }}
    
    function onAudioEnded() {{
      if (!isPlaying || isPaused) return;
      
      debugLog('音声再生終了');
      
      if (currentPhase === 0) {{
        // 単語音声が終了
        currentPhase = 1;
        playCurrentPhase();
      }} else if (currentPhase === 1) {{
        // 日本語音声が終了
        currentPhase = 2;
        playCurrentPhase();
      }} else if (currentPhase === 2) {{
        // 例文音声が終了
        sentenceRepeatCount++;
        if (sentenceRepeatCount < maxSentenceRepeat) {{
          // まだmaxSentenceRepeat回再生していない
          debugLog(`例文を再度再生します (${{sentenceRepeatCount + 1}}/${{maxSentenceRepeat}}回目)`);
          setTimeout(() => {{
            // 例文リピート時も中国語の速度を適用
            audioPlayer.playbackRate = parseFloat(document.getElementById('speedRange').value);
            audioPlayer.play().catch(error => {{
              console.error('例文音声の再生エラー:', error);
              nextWord();
            }});
          }}, CONFIG.sentenceRepeatIntervalMs);
        }} else {{
          // maxSentenceRepeat回再生完了、次の単語へ（範囲制御付き）
          sentenceRepeatCount = 0;
          currentPhase = 0;
          nextWord();
        }}
      }}
    }}
    
    function changeSpeed() {{
      const speed = document.getElementById('speedRange').value;
      document.getElementById('speedValue').textContent = speed;
      audioPlayer.playbackRate = parseFloat(speed);
      debugLog(`再生速度変更: ${{speed}}x`);
      saveSettings(); // 設定を保存
    }}
    
    function changeJapaneseSpeed() {{
      const speed = document.getElementById('japaneseSpeedRange').value;
      document.getElementById('japaneseSpeedValue').textContent = speed;
      debugLog(`日本語訳 再生速度変更: ${{speed}}x`);
      saveSettings(); // 設定を保存
    }}
    
    function changeRepeatCount() {{
      const repeatCount = document.getElementById('repeatRange').value;
      document.getElementById('repeatValue').textContent = repeatCount;
      maxSentenceRepeat = parseInt(repeatCount);
      debugLog(`例文再生回数変更: ${{repeatCount}}回`);
      saveSettings(); // 設定を保存
    }}
    
    function filterByLevel() {{
      const selectedLevel = document.getElementById('levelSelect').value;
      if (selectedLevel === '') {{
        words = [...allWords];
      }} else {{
        words = allWords.filter(w => w.level === selectedLevel);
      }}
      document.getElementById('searchInput').value = ''; // レベル変更時に検索キーワードをクリア
      document.getElementById('searchResults').classList.remove('active'); // 検索結果プレビューも非表示
      populateStartUnitSelect();
      
      // ユーザー指定位置をリセット（フィルター後は無効になる可能性があるため）
      userSpecifiedStartIndex = -1;
      currentWordIndex = 0; // フィルター後は先頭から
      
      // 範囲指定もクリア（フィルター後は無効になる可能性があるため）
      clearRange();
      
      stopPlayback(); // 状態をリセットし、表示を更新
      updateDisplay();
      document.getElementById('wordNumberInput').max = words.length;
      document.getElementById('rangeStartInput').max = words.length; // 範囲指定の最大値を更新
      document.getElementById('rangeEndInput').max = words.length; // 範囲指定の最大値を更新
      debugLog(`レベルフィルタ: ${{selectedLevel || '全レベル'}} (${{words.length}}単語)`);
      saveSettings(); // 設定を保存
    }}

    function searchWords() {{
      const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
      debugLog(`検索実行: "${{searchTerm}}"`);
      if (!searchTerm) {{
        words = [...allWords]; // 検索語が空なら全件表示
        document.getElementById('searchResults').classList.remove('active');
        // 検索クリア時はユーザー指定位置と範囲指定をリセット
        userSpecifiedStartIndex = -1;
        clearRange();
      }} else {{
        // レベルフィルターが適用されている場合は、そのレベル内で検索
        const selectedLevel = document.getElementById('levelSelect').value;
        const baseWords = selectedLevel === '' ? allWords : allWords.filter(w => w.level === selectedLevel);
        
        words = baseWords.filter(word => {{
          return (word.word && word.word.toLowerCase().includes(searchTerm)) ||
                 (word.pinyin && word.pinyin.toLowerCase().includes(searchTerm)) ||
                 (word.meaning && word.meaning.toLowerCase().includes(searchTerm)) ||
                 (word.sentence && word.sentence.toLowerCase().includes(searchTerm)) ||
                 (word.translation && word.translation.toLowerCase().includes(searchTerm));
        }});
        
        // 検索結果のプレビュー表示
        displaySearchResults(words, searchTerm);
        // 検索時はユーザー指定位置と範囲指定をリセット
        userSpecifiedStartIndex = -1;
        clearRange();
      }}
      currentWordIndex = 0;
      populateStartUnitSelect();
      stopPlayback(); // 状態リセット & 表示更新
      updateDisplay(); // 検索結果に応じて表示を即時更新
      document.getElementById('wordNumberInput').max = words.length; // 番号指定の最大値を更新
      document.getElementById('rangeStartInput').max = words.length; // 範囲指定の最大値を更新
      document.getElementById('rangeEndInput').max = words.length; // 範囲指定の最大値を更新
      debugLog(`検索結果: ${{words.length}}単語`);
      if (words.length === 0) {{
        alert('指定されたキーワードに一致する単語は見つかりませんでした。');
      }}
      saveSettings(); // 設定を保存
    }}

    function displaySearchResults(results, searchTerm) {{
      const searchResultsDiv = document.getElementById('searchResults');
      const searchResultList = document.getElementById('searchResultList');
      const searchResultCount = document.getElementById('searchResultCount');
      
      searchResultCount.textContent = results.length;
      searchResultList.innerHTML = '';
      
      // 最初の10件（または全件）を表示
      const displayCount = Math.min(results.length, CONFIG.searchResultDisplayCount);
      for (let i = 0; i < displayCount; i++) {{
        const word = results[i];
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item';
        resultItem.innerHTML = `
          <div class="word-info">${{i + 1}}. ${{word.word}} (${{word.pinyin}})</div>
          <div class="meaning-info">${{word.meaning}}</div>
        `;
        resultItem.onclick = () => jumpToSearchResult(i);
        searchResultList.appendChild(resultItem);
      }}
      
      if (results.length > CONFIG.searchResultDisplayCount) {{
        const moreInfo = document.createElement('div');
        moreInfo.style.marginTop = '10px';
        moreInfo.style.color = '#666';
        moreInfo.style.fontSize = '14px';
        moreInfo.textContent = `他 ${{results.length - CONFIG.searchResultDisplayCount}} 件の結果があります...`;
        searchResultList.appendChild(moreInfo);
      }}
      
      searchResultsDiv.classList.add('active');
    }}

    function jumpToSearchResult(index) {{
      currentWordIndex = index;
      userSpecifiedStartIndex = currentWordIndex; // ユーザー指定位置を記憶
      currentPhase = 0;
      sentenceRepeatCount = 0;
      debugLog(`検索結果からジャンプ: インデックス ${{index}} (記憶済み)`);
      
      if (isPlaying && !isPaused) {{
        playCurrentPhase();
      }} else {{
        updateDisplay();
      }}
      
      // 検索結果プレビューを非表示にする
      document.getElementById('searchResults').classList.remove('active');
      saveSettings(); // 設定を保存
    }}

    function clearSearch() {{
      debugLog('検索クリア');
      document.getElementById('searchInput').value = '';
      document.getElementById('searchResults').classList.remove('active');
      const selectedLevel = document.getElementById('levelSelect').value;
      if (selectedLevel === '') {{
          words = [...allWords];
      }} else {{
          // レベルフィルターがかかっている場合は、そのレベルの全単語に戻す
          words = allWords.filter(w => w.level === selectedLevel);
      }}
      // 検索クリア時はユーザー指定位置と範囲指定をリセット
      userSpecifiedStartIndex = -1;
      clearRange();
      currentWordIndex = 0;
      populateStartUnitSelect();
      stopPlayback(); // 状態リセット & 表示更新
      updateDisplay();
      document.getElementById('wordNumberInput').max = words.length;
      document.getElementById('rangeStartInput').max = words.length; // 範囲指定の最大値を更新
      document.getElementById('rangeEndInput').max = words.length; // 範囲指定の最大値を更新
      saveSettings(); // 設定を保存
    }}

    function goToWordByNumber() {{
      const wordNumberInput = document.getElementById('wordNumberInput');
      const number = parseInt(wordNumberInput.value);
      debugLog(`単語番号ジャンプ試行: ${{number}}`);

      if (isNaN(number) || number < 1 || number > words.length) {{
        alert(`無効な単語番号です。1 から ${{words.length}} の間の数値を入力してください。`);
        wordNumberInput.value = '';
        return;
      }}
      currentWordIndex = number - 1;
      userSpecifiedStartIndex = currentWordIndex; // ユーザー指定位置を記憶
      currentPhase = 0;
      sentenceRepeatCount = 0;
      debugLog(`単語番号ジャンプ: インデックス ${{currentWordIndex}} へ (記憶済み)`);
      
      if (isPlaying && !isPaused) {{
        playCurrentPhase();
      }} else {{
        updateDisplay();
      }}
      wordNumberInput.value = ''; // 入力フィールドをクリア
      saveSettings(); // 設定を保存
    }}
    
    // リストから選択して開始位置へジャンプする関数を追加
    function goToSelectedUnit() {{
      const select = document.getElementById('startUnitSelect');
      const val = select.value;
      debugLog(`リスト選択ジャンプ試行: ${{val}}`);
      if (val === '') {{
        alert('有効な範囲を選択してください。');
        return;
      }}
      const index = parseInt(val, 10);
      if (isNaN(index) || index < 0 || index >= words.length) {{
        alert('無効な開始位置です。');
        select.value = '';
        return;
      }}
      currentWordIndex = index;
      userSpecifiedStartIndex = currentWordIndex; // 記憶
      currentPhase = 0;
      sentenceRepeatCount = 0;
      debugLog(`リスト選択からジャンプ: インデックス ${{index}} (記憶済み)`);
      if (isPlaying && !isPaused) {{
        playCurrentPhase();
      }} else {{
        updateDisplay();
      }}
      select.value = '';
      saveSettings(); // 設定を保存
    }}
    
    function setRange() {{
      const startNum = parseInt(document.getElementById('rangeStartInput').value);
      const endNum = parseInt(document.getElementById('rangeEndInput').value);
      const repeatNum = parseInt(document.getElementById('rangeRepeatInput').value);
      
      if (isNaN(startNum) || isNaN(endNum) || isNaN(repeatNum)) {{
        alert('すべての値を正しく入力してください。');
        return;
      }}
      
      if (startNum < 1 || endNum < 1 || startNum > words.length || endNum > words.length) {{
        alert(`番号は1から${{words.length}}の間で入力してください。`);
        return;
      }}
      
      if (startNum > endNum) {{
        alert('開始番号は終了番号以下にしてください。');
        return;
      }}
      
      if (repeatNum < 1 || repeatNum > 10) {{
        alert('繰り返し回数は1から10の間で入力してください。');
        return;
      }}
      
      rangeStartIndex = startNum - 1;
      rangeEndIndex = endNum - 1;
      maxRangeRepeat = repeatNum;
      rangeRepeatCount = 0;
      
      // 範囲の最初に移動
      currentWordIndex = rangeStartIndex;
      userSpecifiedStartIndex = currentWordIndex; // ユーザー指定位置を記憶
      currentPhase = 0;
      sentenceRepeatCount = 0;
      
      debugLog(`範囲設定: ${{startNum}}番〜${{endNum}}番を${{repeatNum}}回繰り返し`);
      alert(`範囲設定完了: ${{startNum}}番〜${{endNum}}番を${{repeatNum}}回繰り返します。`);
      
      updateDisplay();
      saveSettings(); // 設定を保存
    }}
    
    function clearRange() {{
      rangeStartIndex = -1;
      rangeEndIndex = -1;
      rangeRepeatCount = 0;
      maxRangeRepeat = 1;
      
      document.getElementById('rangeStartInput').value = '';
      document.getElementById('rangeEndInput').value = '';
      document.getElementById('rangeRepeatInput').value = CONFIG.rangeDefaultRepeat;
      document.getElementById('rangeInfo').textContent = '';
      
      debugLog('範囲クリア');
      saveSettings(); // 設定を保存
    }}
    
    // タッチイベントのサポート（スワイプ操作）
    let touchStartX = 0;
    let touchEndX = 0;
    
    function handleTouchStart(e) {{
      touchStartX = e.changedTouches[0].screenX;
    }}
    
    function handleTouchEnd(e) {{
      touchEndX = e.changedTouches[0].screenX;
      handleSwipe();
    }}
    
    function handleSwipe() {{
      const swipeThreshold = 50;
      const diff = touchStartX - touchEndX;
      
      if (Math.abs(diff) > swipeThreshold) {{
        if (diff > 0 && !document.getElementById('nextBtn').disabled) {{
          // 左スワイプ - 次へ
          nextWord();
        }} else if (diff < 0 && !document.getElementById('prevBtn').disabled) {{
          // 右スワイプ - 前へ
          prevWord();
        }}
      }}
    }}
    
    // ページ読み込み時の初期化
    window.onload = function() {{
      debugLog('初期化中...');
      
      // 設定を読み込む
      loadSettings();
      
      // 初期表示の設定（設定読み込み後）
      if (words.length === 0) {{
        words = [...allWords];
      }}
      populateStartUnitSelect();
      updateDisplay();
      
      // タッチイベントリスナーを追加
      const playerStatus = document.querySelector('.player-status');
      playerStatus.addEventListener('touchstart', handleTouchStart, false);
      playerStatus.addEventListener('touchend', handleTouchEnd, false);
      
      // iOS Safari でのオーディオ再生制限対策
      document.addEventListener('touchstart', function() {{
        if (audioPlayer.paused && isPlaying && !isPaused) {{
          audioPlayer.play().catch(() => {{}});
        }}
      }}, {{ once: true }});
      
      debugLog(`初期化完了: 総単語数 ${{allWords.length}}`);
    }};
    
    // ページを離れる前に設定を保存
    window.onbeforeunload = function() {{
      saveSettings();
    }};
  </script>
</body>
</html>
"""

# HTMLファイルを保存
with open('audio_player.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("→ audio_player.html を生成しました（カスタマイズ可能版）")
print(f"→ データ読み込み完了。総単語数: {len(df)}")
print("\n重要な設定パラメータはスクリプト上部に配置されています。")
print("必要に応じて調整してください。")