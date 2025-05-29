import subprocess
import sys

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

import pandas as pd
import os

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

# HTML生成
html_content = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>HSK 音声学習プレイヤー（モバイル対応）</title>
  <style>
    * {
      box-sizing: border-box;
      -webkit-tap-highlight-color: transparent;
    }
    
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      margin: 0;
      padding: 10px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      color: #333;
    }
    
    .container {
      max-width: 800px;
      margin: 0 auto;
      background: rgba(255, 255, 255, 0.95);
      border-radius: 20px;
      padding: 15px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      backdrop-filter: blur(10px);
    }
    
    h1 {
      text-align: center;
      margin: 0 0 20px 0;
      color: #333;
      font-size: 24px;
      font-weight: 700;
    }
    
    .offline-controls {
      background: #e8f5e8;
      border: 2px solid #4CAF50;
      border-radius: 15px;
      padding: 15px;
      margin-bottom: 20px;
    }
    
    .offline-controls h3 {
      margin: 0 0 15px 0;
      color: #2d5a2d;
      font-size: 18px;
    }
    
    .offline-status {
      display: flex;
      align-items: center;
      margin-bottom: 15px;
      padding: 10px;
      background: white;
      border-radius: 10px;
      font-weight: 500;
    }
    
    .status-indicator {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      margin-right: 10px;
    }
    
    .status-online { background: #4CAF50; }
    .status-offline { background: #f44336; }
    .status-caching { background: #ff9800; }
    
    .cache-progress {
      width: 100%;
      height: 8px;
      background: #ddd;
      border-radius: 4px;
      overflow: hidden;
      margin: 10px 0;
    }
    
    .cache-progress-bar {
      height: 100%;
      background: linear-gradient(90deg, #4CAF50, #45a049);
      width: 0%;
      transition: width 0.3s ease;
    }
    
    .controls {
      background: rgba(255, 255, 255, 0.9);
      border-radius: 15px;
      padding: 15px;
      margin-bottom: 15px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .mobile-controls {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 15px;
    }
    
    .mobile-controls.wide {
      grid-template-columns: 1fr 1fr 1fr;
    }
    
    button {
      padding: 15px 10px;
      font-size: 14px;
      font-weight: 600;
      border: none;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 50px;
      user-select: none;
      -webkit-user-select: none;
    }
    
    button:active {
      transform: scale(0.95);
    }
    
    .btn-primary {
      background: linear-gradient(135deg, #4CAF50, #45a049);
      color: white;
      box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
    }
    
    .btn-secondary {
      background: linear-gradient(135deg, #2196F3, #1976D2);
      color: white;
      box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
    }
    
    .btn-warning {
      background: linear-gradient(135deg, #FF9800, #F57C00);
      color: white;
      box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
    }
    
    .btn-danger {
      background: linear-gradient(135deg, #f44336, #d32f2f);
      color: white;
      box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
    }
    
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      background: #ccc !important;
      box-shadow: none !important;
      transform: none !important;
    }
    
    .player-status {
      background: rgba(255, 255, 255, 0.9);
      border-radius: 15px;
      padding: 20px;
      margin-bottom: 15px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .current-word {
      font-size: 32px;
      font-weight: bold;
      color: #333;
      text-align: center;
      margin-bottom: 10px;
    }
    
    .current-info {
      margin: 8px 0;
      line-height: 1.6;
      text-align: center;
    }
    
    .current-info.pinyin {
      font-size: 20px;
      color: #666;
      font-weight: 500;
    }
    
    .current-info.meaning {
      font-size: 18px;
      color: #444;
      font-weight: 600;
    }
    
    .current-info.sentence {
      margin-top: 15px;
      padding: 15px;
      background: rgba(249, 249, 249, 0.8);
      border-radius: 10px;
      font-size: 18px;
      line-height: 1.8;
    }
    
    .current-info.translation {
      color: #666;
      font-style: italic;
      font-size: 16px;
      line-height: 1.6;
    }
    
    .progress {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      padding: 15px;
      border-radius: 10px;
      text-align: center;
      font-weight: 600;
      font-size: 16px;
      margin-bottom: 15px;
    }
    
    .mobile-slider {
      margin: 15px 0;
      padding: 15px;
      background: rgba(255, 255, 255, 0.7);
      border-radius: 10px;
    }
    
    .slider-container {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 10px 0;
    }
    
    .slider-container label {
      font-weight: 600;
      font-size: 14px;
      min-width: 120px;
    }
    
    input[type="range"] {
      flex: 1;
      height: 8px;
      border-radius: 4px;
      background: #ddd;
      outline: none;
      -webkit-appearance: none;
    }
    
    input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #4CAF50;
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    
    .value-display {
      min-width: 40px;
      text-align: center;
      font-weight: bold;
      color: #4CAF50;
    }
    
    .search-section {
      background: rgba(255, 255, 255, 0.9);
      border-radius: 15px;
      padding: 15px;
      margin-bottom: 15px;
    }
    
    .search-input {
      width: 100%;
      padding: 12px 15px;
      border: 2px solid #ddd;
      border-radius: 10px;
      font-size: 16px;
      margin-bottom: 10px;
    }
    
    .search-input:focus {
      outline: none;
      border-color: #4CAF50;
    }
    
    .search-results {
      margin-top: 15px;
      max-height: 200px;
      overflow-y: auto;
      border-radius: 10px;
      display: none;
    }
    
    .search-results.active {
      display: block;
    }
    
    .search-result-item {
      padding: 12px;
      margin: 5px 0;
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid #ddd;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    
    .search-result-item:active {
      transform: scale(0.98);
      background: #e8f4f8;
    }
    
    .collapsible {
      background: rgba(255, 255, 255, 0.9);
      border-radius: 15px;
      margin-bottom: 15px;
      overflow: hidden;
    }
    
    .collapsible-header {
      padding: 15px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      cursor: pointer;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .collapsible-content {
      padding: 15px;
      display: none;
    }
    
    .collapsible.active .collapsible-content {
      display: block;
    }
    
    .collapsible-arrow {
      transition: transform 0.3s ease;
    }
    
    .collapsible.active .collapsible-arrow {
      transform: rotate(180deg);
    }
    
    ruby {
      ruby-position: over;
    }
    
    rt {
      font-size: 0.6em;
      color: gray;
    }
    
    @media (max-width: 600px) {
      .container {
        padding: 10px;
        margin: 5px;
        border-radius: 15px;
      }
      
      .current-word {
        font-size: 28px;
      }
      
      .current-info.sentence {
        font-size: 16px;
      }
      
      .mobile-controls {
        grid-template-columns: 1fr 1fr;
        gap: 8px;
      }
      
      button {
        padding: 12px 8px;
        font-size: 13px;
        min-height: 45px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>HSK 音声学習プレイヤー</h1>
    
    <div class="offline-controls">
      <h3>💾 オフライン音声キャッシュ（ディスク保存）</h3>
      <div class="offline-status">
        <div class="status-indicator status-online" id="statusIndicator"></div>
        <span id="statusText">オンライン</span>
      </div>
      <div class="mobile-controls">
        <button class="btn-primary" onclick="startCaching()">💾 音声をディスクキャッシュ</button>
        <button class="btn-danger" onclick="clearCache()">🗑️ キャッシュクリア</button>
      </div>
      <div class="cache-progress">
        <div class="cache-progress-bar" id="cacheProgressBar"></div>
      </div>
      <div id="cacheStatus">ディスクキャッシュ準備完了</div>
    </div>
    
    <div class="player-status">
      <div class="current-word" id="currentWord">-</div>
      <div class="current-info pinyin" id="currentPinyin">-</div>
      <div class="current-info meaning" id="currentMeaning">-</div>
      <div class="current-info sentence" id="currentSentence">-</div>
      <div class="current-info translation" id="currentTranslation">-</div>
    </div>
    
    <div class="progress">
      進捗: <span id="currentIndex">0</span> / <span id="totalWords">0</span>
    </div>
    
    <div class="controls">
      <div class="mobile-controls wide">
        <button class="btn-primary" id="playBtn" onclick="startPlayback()">▶️ 再生</button>
        <button class="btn-warning" id="pauseBtn" onclick="pausePlayback()" disabled>⏸️ 停止</button>
        <button class="btn-danger" id="stopBtn" onclick="stopPlayback()" disabled>⏹️ 停止</button>
      </div>
      
      <div class="mobile-controls">
        <button class="btn-secondary" id="prevBtn" onclick="prevWord()" disabled>⏮️ 前</button>
        <button class="btn-secondary" id="nextBtn" onclick="nextWord()" disabled>⏭️ 次</button>
      </div>
    </div>
    
    <div class="mobile-slider">
      <div class="slider-container">
        <label>中国語速度:</label>
        <input type="range" id="speedRange" min="0.5" max="2" step="0.05" value="1" onchange="changeSpeed()">
        <div class="value-display" id="speedValue">1.0x</div>
      </div>
      
      <div class="slider-container">
        <label>日本語速度:</label>
        <input type="range" id="japaneseSpeedRange" min="0.5" max="2" step="0.05" value="1" onchange="changeJapaneseSpeed()">
        <div class="value-display" id="japaneseSpeedValue">1.0x</div>
      </div>
      
      <div class="slider-container">
        <label>例文回数:</label>
        <input type="range" id="repeatRange" min="1" max="5" step="1" value="4" onchange="changeRepeatCount()">
        <div class="value-display" id="repeatValue">4回</div>
      </div>
    </div>
    
    <div class="search-section">
      <input type="text" class="search-input" id="searchInput" placeholder="🔍 単語、ピンイン、例文、訳など..." onkeyup="handleSearchInput()">
      <div class="mobile-controls">
        <button class="btn-secondary" onclick="searchWords()">🔍 検索</button>
        <button class="btn-warning" onclick="clearSearch()">❌ クリア</button>
      </div>
      <div class="search-results" id="searchResults">
        <div id="searchResultList"></div>
      </div>
    </div>
    
    <div class="collapsible">
      <div class="collapsible-header" onclick="toggleCollapsible(this)">
        詳細コントロール
        <span class="collapsible-arrow">▼</span>
      </div>
      <div class="collapsible-content">
        <div class="mobile-slider">
          <label>レベル選択:</label>
          <select id="levelSelect" onchange="filterByLevel()" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ddd; margin-top: 10px;">
            <option value="">全レベル</option>""" + "".join([f'\n            <option value="{level}">レベル {level}</option>' for level in sorted(df['レベル'].dropna().unique())]) + """
          </select>
        </div>
        
        <div class="mobile-slider">
          <h4 style="margin: 0 0 15px 0; color: #333;">開始位置指定</h4>
          <div style="margin: 10px 0;">
            <label>番号で指定:</label>
            <div style="display: flex; gap: 10px; margin-top: 10px;">
              <input type="number" id="wordNumberInput" min="1" style="flex: 1; padding: 10px; border-radius: 8px; border: 1px solid #ddd;">
              <button class="btn-secondary" onclick="goToWordByNumber()">ジャンプ</button>
            </div>
          </div>
          <div style="margin: 10px 0;">
            <label>リストから選択:</label>
            <select id="startUnitSelect" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ddd; margin-top: 10px;">
              <option value="">選択してください...</option>
            </select>
            <button class="btn-secondary" onclick="goToSelectedUnit()" style="width: 100%; margin-top: 10px;">選択した位置へジャンプ</button>
          </div>
        </div>
        
        <div class="mobile-slider">
          <h4 style="margin: 0 0 15px 0; color: #333;">範囲指定繰り返し再生</h4>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
            <div>
              <label>開始番号:</label>
              <input type="number" id="rangeStartInput" min="1" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ddd; margin-top: 5px;">
            </div>
            <div>
              <label>終了番号:</label>
              <input type="number" id="rangeEndInput" min="1" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ddd; margin-top: 5px;">
            </div>
          </div>
          <div style="margin-bottom: 15px;">
            <label>繰り返し回数:</label>
            <input type="number" id="rangeRepeatInput" min="1" max="10" value="3" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ddd; margin-top: 5px;">
          </div>
          <div class="mobile-controls">
            <button class="btn-primary" onclick="setRange()">範囲設定</button>
            <button class="btn-danger" onclick="clearRange()">範囲クリア</button>
          </div>
          <div id="rangeInfo" style="margin: 10px 0; font-weight: bold; color: #333; text-align: center;"></div>
        </div>
      </div>
    </div>
  </div>
  
  <audio id="audioPlayer" onended="onAudioEnded()"></audio>
  
  <script>
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

html_content += """    ];
    
    // グローバル変数
    let words = [...allWords];
    let currentWordIndex = 0;
    let isPlaying = false;
    let isPaused = false;
    let currentPhase = 0;
    let sentenceRepeatCount = 0;
    let maxSentenceRepeat = 4;
    let rangeStartIndex = -1;
    let rangeEndIndex = -1;
    let rangeRepeatCount = 0;
    let maxRangeRepeat = 1;
    let userSpecifiedStartIndex = -1;
    
    // オフラインキャッシュ関連（Cache API使用でディスク保存）
    let diskCache = null;
    const cacheName = 'hsk-audio-cache-v1';
    let cacheProgress = 0;
    let isCaching = false;
    
    const audioPlayer = document.getElementById('audioPlayer');
    const startUnitSelect = document.getElementById('startUnitSelect');
    
    // Cache API初期化
    async function initializeCache() {
      try {
        diskCache = await caches.open(cacheName);
        console.log('ディスクキャッシュ初期化完了');
      } catch (error) {
        console.warn('Cache API未対応のブラウザです:', error);
        // フォールバック: 少量のメモリキャッシュのみ使用
        diskCache = null;
      }
    }
    
    // 初期化実行
    initializeCache();
    
    // Service Worker登録（オフライン機能用）
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
          .then((registration) => {
            console.log('SW registered: ', registration);
          })
          .catch((registrationError) => {
            console.log('SW registration failed: ', registrationError);
          });
      });
    }
    
    // オンライン/オフライン状態の監視
    function updateOnlineStatus() {
      const statusIndicator = document.getElementById('statusIndicator');
      const statusText = document.getElementById('statusText');
      
      if (navigator.onLine) {
        statusIndicator.className = 'status-indicator status-online';
        statusText.textContent = 'オンライン';
      } else {
        statusIndicator.className = 'status-indicator status-offline';
        statusText.textContent = 'オフライン';
      }
    }
    
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();
    
    // 音声キャッシュ機能（ディスク保存）
    async function startCaching() {
      if (isCaching) return;
      
      if (!diskCache) {
        alert('申し訳ございません。このブラウザではディスクキャッシュがサポートされていません。');
        return;
      }
      
      isCaching = true;
      const statusIndicator = document.getElementById('statusIndicator');
      const statusText = document.getElementById('statusText');
      const progressBar = document.getElementById('cacheProgressBar');
      const cacheStatus = document.getElementById('cacheStatus');
      
      statusIndicator.className = 'status-indicator status-caching';
      statusText.textContent = 'ディスクキャッシュ中...';
      
      const audioFiles = [];
      words.forEach(word => {
        if (word.wordSound) audioFiles.push(word.wordSound);
        if (word.japaneseSound) audioFiles.push(word.japaneseSound);
        if (word.sentenceSound) audioFiles.push(word.sentenceSound);
      });
      
      const uniqueFiles = [...new Set(audioFiles)];
      let cached = 0;
      let totalSize = 0;
      
      for (const audioFile of uniqueFiles) {
        try {
          // すでにキャッシュされているかチェック
          const cachedResponse = await diskCache.match(audioFile);
          if (cachedResponse) {
            cached++;
            const progress = (cached / uniqueFiles.length) * 100;
            progressBar.style.width = progress + '%';
            cacheStatus.textContent = `キャッシュ済み: ${cached}/${uniqueFiles.length} (ディスク保存)`;
            continue;
          }
          
          // ファイルをダウンロードしてディスクキャッシュに保存
          const response = await fetch(audioFile);
          if (response.ok) {
            // ファイルサイズ情報取得
            const fileSize = parseInt(response.headers.get('content-length') || '0');
            totalSize += fileSize;
            
            // Cache APIにレスポンスを保存（ディスクに保存される）
            await diskCache.put(audioFile, response.clone());
            cached++;
            
            const progress = (cached / uniqueFiles.length) * 100;
            progressBar.style.width = progress + '%';
            const sizeMB = (totalSize / (1024 * 1024)).toFixed(1);
            cacheStatus.textContent = `キャッシュ中: ${cached}/${uniqueFiles.length} (${sizeMB}MB ディスク保存)`;
          }
        } catch (error) {
          console.warn('音声ファイルのキャッシュに失敗:', audioFile, error);
        }
      }
      
      isCaching = false;
      statusIndicator.className = 'status-indicator status-online';
      statusText.textContent = 'ディスクキャッシュ完了';
      const finalSizeMB = (totalSize / (1024 * 1024)).toFixed(1);
      cacheStatus.textContent = `キャッシュ完了: ${cached}ファイル (${finalSizeMB}MB ディスク保存)`;
      
      // 振動フィードバック（対応デバイスのみ）
      if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100]);
      }
    }
    
    async function clearCache() {
      // キャッシュクリア前の確認ダイアログ
      const userConfirmed = confirm(
        'キャッシュをクリアしますか？\n\n' +
        '⚠️ 注意: すべての音声データをダウンロードするのに数時間かかります。\n' +
        '本当にキャッシュをクリアしますか？\n\n' +
        '「OK」を押すとキャッシュが削除されます。\n' +
        '「キャンセル」を押すと操作を中止します。'
      );
      
      if (!userConfirmed) {
        // ユーザーがキャンセルした場合
        document.getElementById('cacheStatus').textContent = 'キャッシュクリアを中止しました';
        return;
      }
      
      try {
        if (diskCache) {
          await caches.delete(cacheName);
          diskCache = await caches.open(cacheName);
        }
        
        document.getElementById('cacheProgressBar').style.width = '0%';
        document.getElementById('cacheStatus').textContent = 'ディスクキャッシュクリア完了';
        
        if (navigator.vibrate) {
          navigator.vibrate(200);
        }
      } catch (error) {
        console.error('キャッシュクリアエラー:', error);
        document.getElementById('cacheStatus').textContent = 'キャッシュクリアに失敗しました';
      }
    }
    
    // 音声再生（ディスクキャッシュ優先）
    async function playAudio(src) {
      try {
        let audioUrl = src;
        
        // ディスクキャッシュから取得を試行
        if (diskCache) {
          const cachedResponse = await diskCache.match(src);
          if (cachedResponse) {
            // キャッシュされた音声ファイルのURLを取得
            audioUrl = cachedResponse.url;
            console.log('ディスクキャッシュから音声再生:', src);
          }
        }
        
        return new Promise((resolve, reject) => {
          audioPlayer.src = audioUrl;
          audioPlayer.play()
            .then(resolve)
            .catch(reject);
        });
      } catch (error) {
        console.warn('キャッシュ取得失敗、元URLで再生:', error);
        return new Promise((resolve, reject) => {
          audioPlayer.src = src;
          audioPlayer.play()
            .then(resolve)
            .catch(reject);
        });
      }
    }
    
    function updateDisplay() {
      if (currentWordIndex < 0 || currentWordIndex >= words.length) return;
      
      const word = words[currentWordIndex];
      document.getElementById('currentWord').textContent = word.word;
      document.getElementById('currentPinyin').textContent = word.pinyin;
      document.getElementById('currentMeaning').textContent = '訳: ' + word.meaning;
      document.getElementById('currentSentence').innerHTML = '例文: ' + word.sentence;
      document.getElementById('currentTranslation').textContent = '例文訳: ' + word.translation;
      document.getElementById('currentIndex').textContent = currentWordIndex + 1;
      document.getElementById('totalWords').textContent = words.length;
      
      // 範囲指定の表示更新
      if (rangeStartIndex >= 0 && rangeEndIndex >= 0) {
        document.getElementById('rangeInfo').textContent = 
          `範囲: ${rangeStartIndex + 1}番〜${rangeEndIndex + 1}番 (${rangeRepeatCount + 1}/${maxRangeRepeat}回目)`;
      } else {
        document.getElementById('rangeInfo').textContent = '';
      }
    }
    
    function populateStartUnitSelect() {
      const selectedLevel = document.getElementById('levelSelect').value;
      startUnitSelect.innerHTML = '<option value="">選択してください...</option>';
      const displayWords = words;
      
      // 10単語ごとにグループ化して表示
      for (let i = 0; i < displayWords.length; i += 10) {
        const endIndex = Math.min(i + 9, displayWords.length - 1);
        const startWord = displayWords[i].word.substring(0, 8);
        const endWord = displayWords[endIndex].word.substring(0, 8);
        
        const option = document.createElement('option');
        option.value = i;
        option.textContent = `${i + 1}〜${endIndex + 1}番: ${startWord}...〜${endWord}...`;
        startUnitSelect.appendChild(option);
      }
    }
    
    function startPlayback() {
      if (!isPaused) {
        // ユーザーが指定した開始位置を優先
        if (userSpecifiedStartIndex >= 0 && userSpecifiedStartIndex < words.length) {
          currentWordIndex = userSpecifiedStartIndex;
        } else {
          // セレクトの値をインデックスとして扱う
          const selectedIndex = parseInt(startUnitSelect.value, 10);
          if (!isNaN(selectedIndex) && selectedIndex >= 0 && selectedIndex < words.length) {
            currentWordIndex = selectedIndex;
          }
        }
      }

      isPlaying = true;
      isPaused = false;
      document.getElementById('playBtn').disabled = true;
      document.getElementById('pauseBtn').disabled = false;
      document.getElementById('stopBtn').disabled = false;
      document.getElementById('prevBtn').disabled = false;
      document.getElementById('nextBtn').disabled = false;
      
      playCurrentPhase();
    }
    
    function pausePlayback() {
      isPaused = true;
      audioPlayer.pause();
      document.getElementById('playBtn').disabled = false;
      document.getElementById('pauseBtn').disabled = true;
    }
    
    function stopPlayback() {
      isPlaying = false;
      isPaused = false;
      currentPhase = 0;
      sentenceRepeatCount = 0;
      audioPlayer.pause();
      audioPlayer.currentTime = 0;
      
      document.getElementById('playBtn').disabled = false;
      document.getElementById('pauseBtn').disabled = true;
      document.getElementById('stopBtn').disabled = true;
      document.getElementById('prevBtn').disabled = true;
      document.getElementById('nextBtn').disabled = true;
      updateDisplay();
    }
    
    function prevWord() {
      currentPhase = 0;
      sentenceRepeatCount = 0;
      currentWordIndex--;
      if (currentWordIndex < 0) {
        currentWordIndex = words.length - 1;
      }
      if (isPlaying && !isPaused) {
        playCurrentPhase();
      } else {
        updateDisplay();
      }
    }
    
    function nextWord() {
      currentPhase = 0;
      sentenceRepeatCount = 0;
      currentWordIndex++;
      
      // 範囲指定がある場合の処理
      if (rangeStartIndex >= 0 && rangeEndIndex >= 0) {
        if (currentWordIndex > rangeEndIndex) {
          rangeRepeatCount++;
          if (rangeRepeatCount < maxRangeRepeat) {
            // 範囲の最初に戻る
            currentWordIndex = rangeStartIndex;
          } else {
            // 範囲繰り返し完了 – 再生停止
            stopPlayback();
            alert('範囲指定の繰り返し再生が完了しました！');
            return;
          }
        }
      } else {
        if (currentWordIndex >= words.length) {
          currentWordIndex = 0;
        }
      }
      
      if (isPlaying && !isPaused) {
        playCurrentPhase();
      } else {
        updateDisplay();
      }
    }
    
    function playCurrentPhase() {
      if (!isPlaying || isPaused) return;
      
      const chineseSpeed = parseFloat(document.getElementById('speedRange').value);
      const japaneseSpeed = parseFloat(document.getElementById('japaneseSpeedRange').value);

      updateDisplay();
      const word = words[currentWordIndex];
      
      switch (currentPhase) {
        case 0: // 単語音声
          if (word.wordSound) {
            audioPlayer.playbackRate = chineseSpeed;
            playAudio(word.wordSound).catch(error => {
              console.error('単語音声の再生エラー:', error);
              currentPhase++;
              setTimeout(() => playCurrentPhase(), 50);
            });
          } else {
            currentPhase++;
            setTimeout(() => playCurrentPhase(), 50);
          }
          break;
          
        case 1: // 日本語音声
          if (word.japaneseSound) {
            audioPlayer.playbackRate = japaneseSpeed;
            playAudio(word.japaneseSound).catch(error => {
              console.error('日本語音声の再生エラー:', error);
              currentPhase++;
              setTimeout(() => playCurrentPhase(), 50);
            });
          } else {
            currentPhase++;
            setTimeout(() => playCurrentPhase(), 50);
          }
          break;
          
        case 2: // 例文音声
          if (word.sentenceSound) {
            audioPlayer.playbackRate = chineseSpeed;
            playAudio(word.sentenceSound).catch(error => {
              console.error('例文音声の再生エラー:', error);
              nextWord();
            });
          } else {
            nextWord();
          }
          break;
      }
    }
    
    function onAudioEnded() {
      if (!isPlaying || isPaused) return;
      
      if (currentPhase === 0) {
        currentPhase = 1;
        playCurrentPhase();
      } else if (currentPhase === 1) {
        currentPhase = 2;
        playCurrentPhase();
      } else if (currentPhase === 2) {
        sentenceRepeatCount++;
        if (sentenceRepeatCount < maxSentenceRepeat) {
          setTimeout(() => {
            audioPlayer.playbackRate = parseFloat(document.getElementById('speedRange').value);
            audioPlayer.play().catch(error => {
              console.error('例文音声の再生エラー:', error);
              nextWord();
            });
          }, 50);
        } else {
          sentenceRepeatCount = 0;
          currentPhase = 0;
          nextWord();
        }
      }
    }
    
    function changeSpeed() {
      const speed = document.getElementById('speedRange').value;
      document.getElementById('speedValue').textContent = speed + 'x';
      audioPlayer.playbackRate = parseFloat(speed);
    }
    
    function changeJapaneseSpeed() {
      const speed = document.getElementById('japaneseSpeedRange').value;
      document.getElementById('japaneseSpeedValue').textContent = speed + 'x';
    }
    
    function changeRepeatCount() {
      const repeatCount = document.getElementById('repeatRange').value;
      document.getElementById('repeatValue').textContent = repeatCount + '回';
      maxSentenceRepeat = parseInt(repeatCount);
    }
    
    function searchWords() {
      const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
      if (!searchTerm) {
        words = [...allWords];
        document.getElementById('searchResults').classList.remove('active');
      } else {
        words = allWords.filter(word => {
          return (word.word && word.word.toLowerCase().includes(searchTerm)) ||
                 (word.pinyin && word.pinyin.toLowerCase().includes(searchTerm)) ||
                 (word.meaning && word.meaning.toLowerCase().includes(searchTerm)) ||
                 (word.sentence && word.sentence.toLowerCase().includes(searchTerm)) ||
                 (word.translation && word.translation.toLowerCase().includes(searchTerm));
        });
        displaySearchResults(words, searchTerm);
      }
      currentWordIndex = 0;
      stopPlayback();
      updateDisplay();
      
      if (words.length === 0) {
        alert('指定されたキーワードに一致する単語は見つかりませんでした。');
      }
    }
    
    function displaySearchResults(results, searchTerm) {
      const searchResults = document.getElementById('searchResults');
      const searchResultList = document.getElementById('searchResultList');
      
      searchResultList.innerHTML = '';
      
      const displayCount = Math.min(results.length, 10);
      for (let i = 0; i < displayCount; i++) {
        const word = results[i];
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item';
        resultItem.innerHTML = `
          <div class="word-info">${i + 1}. ${word.word} (${word.pinyin})</div>
          <div class="meaning-info">${word.meaning}</div>
        `;
        resultItem.onclick = () => jumpToSearchResult(i);
        searchResultList.appendChild(resultItem);
      }
      
      if (results.length > 10) {
        const moreInfo = document.createElement('div');
        moreInfo.style.marginTop = '10px';
        moreInfo.style.color = '#666';
        moreInfo.style.fontSize = '14px';
        moreInfo.textContent = `他 ${results.length - 10} 件の結果があります...`;
        searchResultList.appendChild(moreInfo);
      }
      
      searchResults.classList.add('active');
    }
    
    function jumpToSearchResult(index) {
      currentWordIndex = index;
      currentPhase = 0;
      sentenceRepeatCount = 0;
      
      if (isPlaying && !isPaused) {
        playCurrentPhase();
      } else {
        updateDisplay();
      }
      
      document.getElementById('searchResults').classList.remove('active');
      
      // 振動フィードバック
      if (navigator.vibrate) {
        navigator.vibrate(50);
      }
    }
    
    function clearSearch() {
      document.getElementById('searchInput').value = '';
      document.getElementById('searchResults').classList.remove('active');
      words = [...allWords];
      currentWordIndex = 0;
      stopPlayback();
      updateDisplay();
    }
    
    function handleSearchInput() {
      const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
      if (searchTerm.length > 2) {
        searchWords();
      } else if (searchTerm.length === 0) {
        clearSearch();
      }
    }
    
    function toggleCollapsible(header) {
      const collapsible = header.parentElement;
      collapsible.classList.toggle('active');
    }
    
    function filterByLevel() {
      const selectedLevel = document.getElementById('levelSelect').value;
      if (selectedLevel === '') {
        words = [...allWords];
      } else {
        words = allWords.filter(w => w.level === selectedLevel);
      }
      document.getElementById('searchInput').value = '';
      document.getElementById('searchResults').classList.remove('active');
      populateStartUnitSelect();
      
      userSpecifiedStartIndex = -1;
      currentWordIndex = 0;
      clearRange();
      
      stopPlayback();
      updateDisplay();
      document.getElementById('wordNumberInput').max = words.length;
      document.getElementById('rangeStartInput').max = words.length;
      document.getElementById('rangeEndInput').max = words.length;
    }
    
    function goToWordByNumber() {
      const wordNumberInput = document.getElementById('wordNumberInput');
      const number = parseInt(wordNumberInput.value);

      if (isNaN(number) || number < 1 || number > words.length) {
        alert(`無効な単語番号です。1 から ${words.length} の間の数値を入力してください。`);
        wordNumberInput.value = '';
        return;
      }
      currentWordIndex = number - 1;
      userSpecifiedStartIndex = currentWordIndex;
      currentPhase = 0;
      sentenceRepeatCount = 0;
      
      if (isPlaying && !isPaused) {
        playCurrentPhase();
      } else {
        updateDisplay();
      }
      wordNumberInput.value = '';
      
      // 振動フィードバック
      if (navigator.vibrate) {
        navigator.vibrate(50);
      }
    }
    
    function goToSelectedUnit() {
      const select = document.getElementById('startUnitSelect');
      const val = select.value;
      if (val === '') {
        alert('有効な範囲を選択してください。');
        return;
      }
      const index = parseInt(val, 10);
      if (isNaN(index) || index < 0 || index >= words.length) {
        alert('無効な開始位置です。');
        select.value = '';
        return;
      }
      currentWordIndex = index;
      userSpecifiedStartIndex = currentWordIndex;
      currentPhase = 0;
      sentenceRepeatCount = 0;
      if (isPlaying && !isPaused) {
        playCurrentPhase();
      } else {
        updateDisplay();
      }
      select.value = '';
      
      // 振動フィードバック
      if (navigator.vibrate) {
        navigator.vibrate(50);
      }
    }
    
    function setRange() {
      const startNum = parseInt(document.getElementById('rangeStartInput').value);
      const endNum = parseInt(document.getElementById('rangeEndInput').value);
      const repeatNum = parseInt(document.getElementById('rangeRepeatInput').value);
      
      if (isNaN(startNum) || isNaN(endNum) || isNaN(repeatNum)) {
        alert('すべての値を正しく入力してください。');
        return;
      }
      
      if (startNum < 1 || endNum < 1 || startNum > words.length || endNum > words.length) {
        alert(`番号は1から${words.length}の間で入力してください。`);
        return;
      }
      
      if (startNum > endNum) {
        alert('開始番号は終了番号以下にしてください。');
        return;
      }
      
      if (repeatNum < 1 || repeatNum > 10) {
        alert('繰り返し回数は1から10の間で入力してください。');
        return;
      }
      
      rangeStartIndex = startNum - 1;
      rangeEndIndex = endNum - 1;
      maxRangeRepeat = repeatNum;
      rangeRepeatCount = 0;
      
      // 範囲の最初に移動
      currentWordIndex = rangeStartIndex;
      userSpecifiedStartIndex = currentWordIndex;
      currentPhase = 0;
      sentenceRepeatCount = 0;
      
      alert(`範囲設定完了: ${startNum}番〜${endNum}番を${repeatNum}回繰り返します。`);
      updateDisplay();
      
      // 振動フィードバック
      if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100]);
      }
    }
    
    function clearRange() {
      rangeStartIndex = -1;
      rangeEndIndex = -1;
      rangeRepeatCount = 0;
      maxRangeRepeat = 1;
      
      document.getElementById('rangeStartInput').value = '';
      document.getElementById('rangeEndInput').value = '';
      document.getElementById('rangeRepeatInput').value = '3';
      
      updateDisplay();
      
      // 振動フィードバック
      if (navigator.vibrate) {
        navigator.vibrate(100);
      }
    }
    
    // 初期設定
    populateStartUnitSelect();
    updateDisplay();
    document.getElementById('wordNumberInput').max = words.length;
    document.getElementById('rangeStartInput').max = words.length;
    document.getElementById('rangeEndInput').max = words.length;
    
    // タッチイベントの最適化
    document.addEventListener('touchstart', function(e) {
      // パッシブリスナーで性能向上
    }, {passive: true});
    
    // キーボードショートカット（モバイルでも便利）
    document.addEventListener('keydown', function(e) {
      if (e.target.tagName.toLowerCase() === 'input') return;
      
      switch(e.key) {
        case ' ':
          e.preventDefault();
          if (isPlaying && !isPaused) {
            pausePlayback();
          } else {
            startPlayback();
          }
          break;
        case 'ArrowLeft':
          e.preventDefault();
          prevWord();
          break;
        case 'ArrowRight':
          e.preventDefault();
          nextWord();
          break;
        case 'Escape':
          e.preventDefault();
          stopPlayback();
          break;
      }
    });
    
    console.log('HSK音声学習プレイヤー（モバイル対応）初期化完了');
    console.log(`総単語数: ${words.length}`);
  </script>
</body>
</html>
"""

# HTMLファイルを保存
with open('audio_player_mobile_enhanced.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("→ audio_player_mobile_enhanced.html を生成しました。")
print("→ スマホ対応とオフライン音声ディスクキャッシュ機能を搭載！")
print("→ タッチ操作に最適化、美しいUI、メモリ効率的なキャッシュシステム") 