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
    <div class="start-from-control">
      <label>開始位置 (元No.): 
        <select id="startUnitSelect">
          <option value="">最初から</option>
        </select>
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
    }
    
    function populateStartUnitSelect() {
        const selectedLevel = document.getElementById('levelSelect').value;
        startUnitSelect.innerHTML = '<option value="">最初から</option>'; // Reset
        const filteredWords = selectedLevel === '' ? allWords : allWords.filter(w => w.level === selectedLevel);
        
        // アプリ順でソートされた単語から元のunitと単語情報を取得して選択肢に追加
        const uniqueUnits = [];
        const unitSet = new Set();
        filteredWords.forEach(word => {
            if (!unitSet.has(word.unit)) {
                uniqueUnits.push({unit: word.unit, word: word.word, group: word.group });
                unitSet.add(word.unit);
            }
        });
        // データベースで既にアプリ順にソートされているので、そのまま使用
        
        uniqueUnits.forEach((item, index) => {
            const option = document.createElement('option');
            option.value = item.unit; // 元のunitを値として使用
            option.textContent = `アプリ順 ${index + 1}: No.${item.unit} (${item.word.substring(0, 10)})`;
            startUnitSelect.appendChild(option);
        });
    }

    function startPlayback() {
      debugLog('再生開始');
      const selectedStartUnit = startUnitSelect.value;
      if (selectedStartUnit !== '') {
        const startIndex = words.findIndex(w => w.unit === selectedStartUnit && (document.getElementById('levelSelect').value === '' || w.level === document.getElementById('levelSelect').value) );
        if (startIndex !== -1) {
            currentWordIndex = startIndex;
        } else {
            currentWordIndex = 0; // 見つからなければ最初から
        }
      } else {
        currentWordIndex = 0;
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
      currentWordIndex = 0;
      currentPhase = 0;
      sentenceRepeatCount = 0;
      audioPlayer.pause();
      audioPlayer.currentTime = 0;
      
      document.getElementById('playBtn').disabled = false;
      document.getElementById('pauseBtn').disabled = true;
      document.getElementById('stopBtn').disabled = true;
      document.getElementById('prevBtn').disabled = true;
      document.getElementById('nextBtn').disabled = true;
      populateStartUnitSelect();
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
      if (currentWordIndex >= words.length) {
        currentWordIndex = 0;
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
          // maxSentenceRepeat回再生完了、次の単語へ
          sentenceRepeatCount = 0;
          currentPhase = 0;
          currentWordIndex++;
          if (currentWordIndex >= words.length) {
            stopPlayback();
            alert('すべての単語の再生が完了しました！');
          } else {
            setTimeout(() => playCurrentPhase(), 50);
          }
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
      populateStartUnitSelect();
      stopPlayback();
      debugLog(`レベルフィルタ: ${selectedLevel || '全レベル'} (${words.length}単語)`);
    }
    
    // 初期表示と設定
    populateStartUnitSelect();
    updateDisplay();
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