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
  <title>HSK 音声学習プレイヤー</title>
  <style>
    body { font-family: sans-serif; margin: 20px; max-width: 800px; margin: 0 auto; padding: 20px; }
    .controls { margin: 20px 0; padding: 20px; background: #f0f0f0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .player-status { margin: 20px 0; padding: 15px; background: #e8f4f8; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .current-word { font-size: 28px; margin: 15px 0; font-weight: bold; color: #333; }
    .current-info { margin: 8px 0; line-height: 1.6; }
    .current-info.pinyin { font-size: 20px; color: #666; }
    .current-info.meaning { font-size: 18px; color: #444; font-weight: 500; }
    .current-info.sentence { margin-top: 15px; padding: 10px; background: #f9f9f9; border-radius: 5px; font-size: 20px; line-height: 1.8; }
    .current-info.translation { color: #666; font-style: italic; font-size: 18px; line-height: 1.6; }
    button { padding: 10px 20px; margin: 5px; font-size: 16px; cursor: pointer; border: none; border-radius: 5px; background: #4CAF50; color: white; transition: background 0.3s; }
    button:hover:not(:disabled) { background: #45a049; }
    button:disabled { opacity: 0.5; cursor: not-allowed; background: #ccc; }
    .control-buttons { display: flex; gap: 10px; margin-bottom: 15px; }
    .speed-control, .start-from-control { margin: 15px 0; }
    .progress { margin: 20px 0; font-size: 16px; }
    ruby { ruby-position: over; }
    rt { font-size: 0.6em; color: gray; }
    h1 { text-align: center; color: #333; }
    h3 { color: #555; margin-bottom: 15px; }
    label { font-weight: 500; }
    select, input[type="range"] { margin-left: 10px; }
    select { padding: 5px; border-radius: 3px; border: 1px solid #ddd; }
    input[type="range"] { width: 200px; vertical-align: middle; }
    .search-results {
      margin: 15px 0;
      padding: 10px;
      background: #f9f9f9;
      border-radius: 5px;
      display: none;
    }
    .search-results.active {
      display: block;
    }
    .search-results h4 {
      margin: 0 0 10px 0;
      color: #555;
    }
    .search-result-item {
      padding: 8px;
      margin: 5px 0;
      background: white;
      border: 1px solid #ddd;
      border-radius: 3px;
      cursor: pointer;
      transition: background 0.2s;
    }
    .search-result-item:hover {
      background: #e8f4f8;
    }
    .search-result-item .word-info {
      font-weight: bold;
      color: #333;
    }
    .search-result-item .meaning-info {
      color: #666;
      font-size: 14px;
      margin-top: 3px;
    }
  </style>
</head>
<body>
  <h1>HSK 音声学習プレイヤー</h1>
  
  <div class="controls">
    <h3>再生コントロール</h3>
    <div class="control-buttons">
      <button id="playBtn" onclick="startPlayback()">▶️ 再生開始</button>
      <button id="pauseBtn" onclick="pausePlayback()" disabled>⏸️ 一時停止</button>
      <button id="stopBtn" onclick="stopPlayback()" disabled>⏹️ 停止</button>
      <button id="prevBtn" onclick="prevWord()" disabled>⏮️ 前の単語</button>
      <button id="nextBtn" onclick="nextWord()" disabled>⏭️ 次の単語</button>
    </div>
    
    <div class="speed-control">
      <label>中国語 再生速度: <span id="speedValue">1.0</span>x</label>
      <input type="range" id="speedRange" min="0.5" max="2" step="0.05" value="1" onchange="changeSpeed()">
    </div>
    
    <div class="speed-control">
      <label>日本語訳 再生速度: <span id="japaneseSpeedValue">1.0</span>x</label>
      <input type="range" id="japaneseSpeedRange" min="0.5" max="2" step="0.05" value="1" onchange="changeJapaneseSpeed()">
    </div>
    
    <div class="speed-control">
      <label>例文再生回数: <span id="repeatValue">4</span>回</label>
      <input type="range" id="repeatRange" min="1" max="5" step="1" value="4" onchange="changeRepeatCount()">
    </div>

    <div>
      <label>キーワード検索:
        <input type="text" id="searchInput" placeholder="単語、ピンイン、例文、訳など..." style="width: 200px; margin-left: 10px; padding: 5px; border-radius: 3px; border: 1px solid #ddd;">
        <button onclick="searchWords()" style="margin-left: 5px;">検索</button>
        <button onclick="clearSearch()" style="margin-left: 5px;">クリア</button>
      </label>
    </div>
    <div class="search-results" id="searchResults">
      <h4>検索結果: <span id="searchResultCount">0</span>件</h4>
      <div id="searchResultList"></div>
    </div>
    
    <div style="margin: 15px 0; padding: 15px; background: #e8f5e8; border-radius: 5px; border: 1px solid #c3e6c3;">
      <h4 style="margin: 0 0 10px 0; color: #2d5a2d;">開始位置指定</h4>
      <div style="margin: 8px 0;">
        <label>番号で指定:
          <input type="number" id="wordNumberInput" min="1" style="width: 80px; margin-left: 10px; padding: 5px; border-radius: 3px; border: 1px solid #ddd;">
          <button onclick="goToWordByNumber()" style="margin-left: 5px;">ジャンプ</button>
        </label>
      </div>
      <div style="margin: 8px 0;">
        <label>リストから選択:
          <select id="startUnitSelect" style="margin-left: 10px; padding: 5px; border-radius: 3px; border: 1px solid #ddd; min-width: 200px;">
            <option value="">選択してください...</option>
          </select>
          <button onclick="goToSelectedUnit()" style="margin-left: 5px;">ジャンプ</button>
        </label>
      </div>
    </div>
    
    <div style="margin: 15px 0; padding: 15px; background: #fff3cd; border-radius: 5px; border: 1px solid #ffeaa7;">
      <h4 style="margin: 0 0 10px 0; color: #856404;">範囲指定繰り返し再生</h4>
      <div style="margin: 8px 0;">
        <label>開始番号:
          <input type="number" id="rangeStartInput" min="1" style="width: 80px; margin-left: 10px; padding: 5px; border-radius: 3px; border: 1px solid #ddd;">
        </label>
        <label style="margin-left: 15px;">終了番号:
          <input type="number" id="rangeEndInput" min="1" style="width: 80px; margin-left: 10px; padding: 5px; border-radius: 3px; border: 1px solid #ddd;">
        </label>
        <label style="margin-left: 15px;">繰り返し回数:
          <input type="number" id="rangeRepeatInput" min="1" max="10" value="3" style="width: 60px; margin-left: 10px; padding: 5px; border-radius: 3px; border: 1px solid #ddd;">
        </label>
      </div>
      <div style="margin: 10px 0;">
        <button onclick="setRange()" style="background: #28a745; margin-right: 10px;">範囲設定</button>
        <button onclick="clearRange()" style="background: #dc3545;">範囲クリア</button>
      </div>
      <div id="rangeInfo" style="margin: 5px 0; font-weight: bold; color: #856404;"></div>
    </div>
    
    <div>
      <label>レベル選択: 
        <select id="levelSelect" onchange="filterByLevel()">
          <option value="">全レベル</option>
"""

# レベルオプションを追加
levels = sorted(df['レベル'].dropna().unique())
for level in levels:
    html_content += f'          <option value="{level}">レベル {level}</option>\n'

html_content += """        </select>
      </label>
    </div>
  </div>
  
  <div class="player-status">
    <h3>現在の学習状況</h3>
    <div class="current-word" id="currentWord">-</div>
    <div class="current-info pinyin" id="currentPinyin">-</div>
    <div class="current-info meaning" id="currentMeaning">-</div>
    <div class="current-info sentence" id="currentSentence">-</div>
    <div class="current-info translation" id="currentTranslation">-</div>
    <div class="progress">
      進捗: <span id="currentIndex">0</span> / <span id="totalWords">0</span>
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
    
    let words = [...allWords];
    let currentWordIndex = 0;
    let isPlaying = false;
    let isPaused = false;
    let currentPhase = 0; // 0: 単語音声, 1: 日本語音声, 2: 例文音声
    let sentenceRepeatCount = 0;
    let maxSentenceRepeat = 4; // デフォルトは4回
    let rangeStartIndex = -1; // 範囲指定の開始インデックス
    let rangeEndIndex = -1; // 範囲指定の終了インデックス
    let rangeRepeatCount = 0; // 範囲の繰り返し回数
    let maxRangeRepeat = 1; // 範囲の最大繰り返し回数
    let userSpecifiedStartIndex = -1; // ユーザーが指定した開始位置を記憶
    
    const audioPlayer = document.getElementById('audioPlayer');
    const startUnitSelect = document.getElementById('startUnitSelect');
    
    function debugLog(message) { console.log(`[HSK Player] ${message}`); }
    
    function updateDisplay() {
      if (currentWordIndex < 0 || currentWordIndex >= words.length) {
        debugLog('updateDisplay: 無効なcurrentWordIndexです');
        return;
      }
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
        startUnitSelect.innerHTML = '<option value="">選択してください...</option>'; // Reset
        const filteredWords = selectedLevel === '' ? allWords : allWords.filter(w => w.level === selectedLevel);
        
        // 現在のwordsリストに基づいて選択肢を作成（フィルターや検索結果を反映）
        const displayWords = words; // 現在表示中のリスト
        
        // 10単語ごとにグループ化して表示
        for (let i = 0; i < displayWords.length; i += 10) {
            const endIndex = Math.min(i + 9, displayWords.length - 1);
            const startWord = displayWords[i].word.substring(0, 8);
            const endWord = displayWords[endIndex].word.substring(0, 8);
            
            const option = document.createElement('option');
            option.value = i; // インデックスを値として使用
            option.textContent = `${i + 1}〜${endIndex + 1}番: ${startWord}...〜${endWord}...`;
            startUnitSelect.appendChild(option);
        }
    }

    function startPlayback() {
      debugLog('再生開始');
      
      if (!isPaused) {
        // ユーザーが指定した開始位置を優先
        if (userSpecifiedStartIndex >= 0 && userSpecifiedStartIndex < words.length) {
          currentWordIndex = userSpecifiedStartIndex;
          debugLog(`ユーザー指定位置から開始: ${currentWordIndex + 1}番`);
        } else {
          // セレクトの値をインデックスとして扱う
          const selectedIndex = parseInt(startUnitSelect.value, 10);
          if (!isNaN(selectedIndex) && selectedIndex >= 0 && selectedIndex < words.length) {
            currentWordIndex = selectedIndex;
            debugLog(`リスト選択位置から開始: ${currentWordIndex + 1}番`);
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
      debugLog('一時停止');
      isPaused = true;
      audioPlayer.pause();
      document.getElementById('playBtn').disabled = false;
      document.getElementById('pauseBtn').disabled = true;
    }
    
    function stopPlayback() {
      debugLog('停止');
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
      debugLog('前の単語へ');
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
      debugLog('次の単語へ');
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
            debugLog(`範囲繰り返し: ${rangeRepeatCount + 1}/${maxRangeRepeat}回目開始`);
          } else {
            // 範囲繰り返し完了 – 再生停止
            debugLog('範囲繰り返し完了 (停止)');
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
      debugLog(`現在の単語: ${word.word}, フェーズ: ${currentPhase}`);
      
      switch (currentPhase) {
        case 0: // 単語音声 (中国語)
          if (word.wordSound) {
            debugLog(`単語音声を再生: ${word.wordSound}`);
            audioPlayer.src = word.wordSound;
            audioPlayer.playbackRate = chineseSpeed;
            audioPlayer.play().then(() => {
              debugLog('単語音声の再生開始成功');
            }).catch(error => {
              console.error('単語音声の再生エラー:', error);
              debugLog(`エラー: ${error.message}`);
              // エラーの場合は次のフェーズへ
              currentPhase++;
              setTimeout(() => playCurrentPhase(), 50);
            });
          } else {
            debugLog('単語音声ファイルがありません');
            currentPhase++;
            setTimeout(() => playCurrentPhase(), 50);
          }
          break;
          
        case 1: // 日本語音声
          if (word.japaneseSound) {
            debugLog(`日本語音声を再生: ${word.japaneseSound}`);
            audioPlayer.src = word.japaneseSound;
            audioPlayer.playbackRate = japaneseSpeed;
            audioPlayer.play().then(() => {
              debugLog('日本語音声の再生開始成功');
            }).catch(error => {
              console.error('日本語音声の再生エラー:', error);
              debugLog(`エラー: ${error.message}`);
              // エラーの場合は次のフェーズへ
              currentPhase++;
              setTimeout(() => playCurrentPhase(), 50);
            });
          } else {
            debugLog('日本語音声ファイルがありません');
            currentPhase++;
            setTimeout(() => playCurrentPhase(), 50);
          }
          break;
          
        case 2: // 例文音声 (中国語)
          if (word.sentenceSound) {
            debugLog(`例文音声を再生: ${word.sentenceSound} (${sentenceRepeatCount + 1}/${maxSentenceRepeat}回目)`);
            audioPlayer.src = word.sentenceSound;
            audioPlayer.playbackRate = chineseSpeed;
            audioPlayer.play().then(() => {
              debugLog('例文音声の再生開始成功');
            }).catch(error => {
              console.error('例文音声の再生エラー:', error);
              debugLog(`エラー: ${error.message}`);
              // エラーの場合は次の単語へ
              nextWord();
            });
          } else {
            debugLog('例文音声ファイルがありません');
            nextWord();
          }
          break;
      }
    }
    
    function onAudioEnded() {
      if (!isPlaying || isPaused) return;
      
      debugLog('音声再生終了');
      
      if (currentPhase === 0) {
        // 単語音声が終了
        currentPhase = 1;
        playCurrentPhase();
      } else if (currentPhase === 1) {
        // 日本語音声が終了
        currentPhase = 2;
        playCurrentPhase();
      } else if (currentPhase === 2) {
        // 例文音声が終了
        sentenceRepeatCount++;
        if (sentenceRepeatCount < maxSentenceRepeat) {
          // まだmaxSentenceRepeat回再生していない
          debugLog(`例文を再度再生します (${sentenceRepeatCount + 1}/${maxSentenceRepeat}回目)`);
          setTimeout(() => {
            // 例文リピート時も中国語の速度を適用
            audioPlayer.playbackRate = parseFloat(document.getElementById('speedRange').value);
            audioPlayer.play().catch(error => {
              console.error('例文音声の再生エラー:', error);
              nextWord();
            });
          }, 50);
        } else {
          // maxSentenceRepeat回再生完了、次の単語へ（範囲制御付き）
          sentenceRepeatCount = 0;
          currentPhase = 0;
          nextWord();
        }
      }
    }
    
    function changeSpeed() {
      const speed = document.getElementById('speedRange').value;
      document.getElementById('speedValue').textContent = speed;
      audioPlayer.playbackRate = parseFloat(speed);
      debugLog(`再生速度変更: ${speed}x`);
    }
    
    function changeJapaneseSpeed() {
      const speed = document.getElementById('japaneseSpeedRange').value;
      document.getElementById('japaneseSpeedValue').textContent = speed;
      debugLog(`日本語訳 再生速度変更: ${speed}x`);
    }
    
    function changeRepeatCount() {
      const repeatCount = document.getElementById('repeatRange').value;
      document.getElementById('repeatValue').textContent = repeatCount;
      maxSentenceRepeat = parseInt(repeatCount);
      debugLog(`例文再生回数変更: ${repeatCount}回`);
    }
    
    function filterByLevel() {
      const selectedLevel = document.getElementById('levelSelect').value;
      if (selectedLevel === '') {
        words = [...allWords];
      } else {
        words = allWords.filter(w => w.level === selectedLevel);
      }
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
      debugLog(`レベルフィルタ: ${selectedLevel || '全レベル'} (${words.length}単語)`);
    }

    function searchWords() {
      const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
      debugLog(`検索実行: "${searchTerm}"`);
      if (!searchTerm) {
        words = [...allWords]; // 検索語が空なら全件表示
        document.getElementById('searchResults').classList.remove('active');
        // 検索クリア時はユーザー指定位置と範囲指定をリセット
        userSpecifiedStartIndex = -1;
        clearRange();
      } else {
        words = allWords.filter(word => {
          return (word.word && word.word.toLowerCase().includes(searchTerm)) ||
                 (word.pinyin && word.pinyin.toLowerCase().includes(searchTerm)) ||
                 (word.meaning && word.meaning.toLowerCase().includes(searchTerm)) ||
                 (word.sentence && word.sentence.toLowerCase().includes(searchTerm)) ||
                 (word.translation && word.translation.toLowerCase().includes(searchTerm));
        });
        
        // 検索結果のプレビュー表示
        displaySearchResults(words, searchTerm);
        // 検索時はユーザー指定位置と範囲指定をリセット
        userSpecifiedStartIndex = -1;
        clearRange();
      }
      currentWordIndex = 0;
      populateStartUnitSelect();
      stopPlayback(); // 状態リセット & 表示更新
      updateDisplay(); // 検索結果に応じて表示を即時更新
      document.getElementById('wordNumberInput').max = words.length; // 番号指定の最大値を更新
      document.getElementById('rangeStartInput').max = words.length; // 範囲指定の最大値を更新
      document.getElementById('rangeEndInput').max = words.length; // 範囲指定の最大値を更新
      debugLog(`検索結果: ${words.length}単語`);
      if (words.length === 0) {
        alert('指定されたキーワードに一致する単語は見つかりませんでした。');
      }
    }

    function displaySearchResults(results, searchTerm) {
      const searchResultsDiv = document.getElementById('searchResults');
      const searchResultList = document.getElementById('searchResultList');
      const searchResultCount = document.getElementById('searchResultCount');
      
      searchResultCount.textContent = results.length;
      searchResultList.innerHTML = '';
      
      // 最初の10件（または全件）を表示
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
      
      searchResultsDiv.classList.add('active');
    }

    function jumpToSearchResult(index) {
      currentWordIndex = index;
      userSpecifiedStartIndex = currentWordIndex; // ユーザー指定位置を記憶
      currentPhase = 0;
      sentenceRepeatCount = 0;
      debugLog(`検索結果からジャンプ: インデックス ${index} (記憶済み)`);
      
      if (isPlaying && !isPaused) {
        playCurrentPhase();
      } else {
        updateDisplay();
      }
      
      // 検索結果プレビューを非表示にする
      document.getElementById('searchResults').classList.remove('active');
    }

    function clearSearch() {
      debugLog('検索クリア');
      document.getElementById('searchInput').value = '';
      document.getElementById('searchResults').classList.remove('active');
      const selectedLevel = document.getElementById('levelSelect').value;
      if (selectedLevel === '') {
          words = [...allWords];
      } else {
          // レベルフィルターがかかっている場合は、そのレベルの全単語に戻す
          words = allWords.filter(w => w.level === selectedLevel);
      }
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
    }

    function goToWordByNumber() {
      const wordNumberInput = document.getElementById('wordNumberInput');
      const number = parseInt(wordNumberInput.value);
      debugLog(`単語番号ジャンプ試行: ${number}`);

      if (isNaN(number) || number < 1 || number > words.length) {
        alert(`無効な単語番号です。1 から ${words.length} の間の数値を入力してください。`);
        wordNumberInput.value = '';
        return;
      }
      currentWordIndex = number - 1;
      userSpecifiedStartIndex = currentWordIndex; // ユーザー指定位置を記憶
      currentPhase = 0;
      sentenceRepeatCount = 0;
      debugLog(`単語番号ジャンプ: インデックス ${currentWordIndex} へ (記憶済み)`);
      
      if (isPlaying && !isPaused) {
        playCurrentPhase();
      } else {
        updateDisplay();
      }
      wordNumberInput.value = ''; // 入力フィールドをクリア
    }
    
    // リストから選択して開始位置へジャンプする関数を追加
    function goToSelectedUnit() {
      const select = document.getElementById('startUnitSelect');
      const val = select.value;
      debugLog(`リスト選択ジャンプ試行: ${val}`);
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
      userSpecifiedStartIndex = currentWordIndex; // 記憶
      currentPhase = 0;
      sentenceRepeatCount = 0;
      debugLog(`リスト選択からジャンプ: インデックス ${index} (記憶済み)`);
      if (isPlaying && !isPaused) {
        playCurrentPhase();
      } else {
        updateDisplay();
      }
      select.value = '';
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
      userSpecifiedStartIndex = currentWordIndex; // ユーザー指定位置を記憶
      currentPhase = 0;
      sentenceRepeatCount = 0;
      
      debugLog(`範囲設定: ${startNum}番〜${endNum}番を${repeatNum}回繰り返し`);
      alert(`範囲設定完了: ${startNum}番〜${endNum}番を${repeatNum}回繰り返します。`);
      
      updateDisplay();
    }
    
    function clearRange() {
      rangeStartIndex = -1;
      rangeEndIndex = -1;
      rangeRepeatCount = 0;
      maxRangeRepeat = 1;
      
      document.getElementById('rangeStartInput').value = '';
      document.getElementById('rangeEndInput').value = '';
      document.getElementById('rangeRepeatInput').value = '3';
      
      debugLog('範囲指定をクリアしました');
      updateDisplay();
    }
    
    // 初期表示と設定
    populateStartUnitSelect();
    updateDisplay();
    document.getElementById('wordNumberInput').max = words.length; // 初期ロード時にも設定
    document.getElementById('rangeStartInput').max = words.length; // 範囲指定の最大値設定
    document.getElementById('rangeEndInput').max = words.length; // 範囲指定の最大値設定
    debugLog('音声学習プレイヤー初期化完了');
    debugLog(`総単語数: ${words.length}`);
  </script>
</body>
</html>
"""

# HTMLファイルを保存
with open('audio_player.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("→ audio_player.html (開始位置選択機能付き) を生成しました。")
print("→ ブラウザで開いて音声学習を開始できます。")
print("→ 再生順序: 単語音声 → 日本語音声 → 例文音声×4回") 