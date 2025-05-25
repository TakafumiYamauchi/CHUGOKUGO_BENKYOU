import pandas as pd
from pypinyin import pinyin, Style

# all_sentences.csv を読み込み
df = pd.read_csv('all_sentences.csv')

def to_ruby(chinese: str) -> str:
    """
    １文字ずつ <ruby>漢字<rt>pīn​yīn</rt></ruby> に変換。
    句読点や英数字はそのまま出力します。
    """
    pys = pinyin(chinese, style=Style.TONE, strict=False)
    out = []
    for ch, py in zip(chinese, pys):
        if '\u4e00' <= ch <= '\u9fff':  # 漢字範囲
            tone = py[0]
            out.append(f'<ruby>{ch}<rt>{tone}</rt></ruby>')
        else:
            out.append(ch)
    return ''.join(out)

# ルビ列を追加
df['例文(ルビHTML)'] = df['例文(中文)'].map(to_ruby)

# 必要に応じて「例文(ピンイン)」列は削除して構いません
# df = df.drop(columns=['例文(ピンイン)'])

# 新ファイルとして出力
df.to_csv('all_sentences_with_ruby.csv', index=False)
print("→ all_sentences_with_ruby.csv を出力しました")
