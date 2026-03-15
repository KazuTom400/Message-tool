import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import re
import base64
import os

# --- 1. フォント設定 ---
FONT_FILE = "ipaexg.ttf" 
FONT_NAME = "JapaneseFont"

def register_font():
    if os.path.exists(FONT_FILE):
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
        return True
    return False

HAS_FONT = register_font()

# --- 2. ページ設定 ---
st.set_page_config(page_title="メッセージカード作成", layout="wide")
st.title("📇 メッセージカード作成ツール")

# --- 3. サイドバー設定 ---
st.sidebar.header("カードサイズ設定 (mm)")
card_width = st.sidebar.number_input("横幅", min_value=10.0, value=91.0, step=1.0)
card_height = st.sidebar.number_input("縦幅", min_value=10.0, value=55.0, step=1.0)
font_size = st.sidebar.number_input("文字サイズ (pt)", min_value=5, value=11, step=1)
line_spacing = st.sidebar.number_input("行間", min_value=1.0, value=1.2, step=0.1)

# --- 4. メッセージ入力 ---
st.header("1. メッセージ入力")
input_text = st.text_area(
    "メッセージを入力してください。改行2回（空行）で次のカードに分かれます。スペースや1回の改行は同じカードに入ります。",
    placeholder="田中さん\nお疲れ様でした！\n\n佐藤さん\nいつもありがとうございます。\nスペース も 使えます。",
    height=300
)

# --- 5. メッセージ分割ロジック ---
# 【変更点】改行2回以上（\n\n+）を区切りとして分割
messages = re.split(r'\n{2,}', input_text.strip()) if input_text.strip() else []

# --- 6. PDF生成関数 ---
def create_card_pdf(msg_list, w_mm, h_mm, f_size):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4
    w_pt, h_pt = w_mm * mm, h_mm * mm
    
    cols = int(page_w // w_pt)
    rows = int(page_h // h_pt)
    
    if cols == 0 or rows == 0:
        return None

    x, y = 0, page_h - h_pt
    
    for i, msg in enumerate(msg_list):
        # 枠線
        c.setLineWidth(0.2)
        c.rect(x, y, w_pt, h_pt)
        c.setFont(FONT_NAME if HAS_FONT else "Helvetica", f_size)
        
        # 内部の改行と自動折り返しを処理
        raw_lines = msg.split('\n')
        all_display_lines = []
        chars_per_line = max(1, int((w_pt * 0.8) / (f_size * 0.6)))
        
        for r_line in raw_lines:
            if r_line == "":
                all_display_lines.append("")
            else:
                # 1行がカード幅を超える場合は分割
                split_sublines = [r_line[j:j+chars_per_line] for j in range(0, len(r_line), chars_per_line)]
                all_display_lines.extend(split_sublines)

        # 垂直中央揃え
        total_text_h = len(all_display_lines) * f_size * line_spacing
        start_y = y + (h_pt + total_text_h)/2 - f_size
        
        for idx, line in enumerate(all_display_lines):
            line_y = start_y - (idx * f_size * line_spacing)
            c.drawCentredString(x + w_pt/2, line_y, line)
        
        # 次の配置へ
        x += w_pt
        if (i + 1) % cols == 0:
            x = 0
            y -= h_pt
        if (i + 1) % (cols * rows) == 0 and (i + 1) < len(msg_list):
            c.showPage()
            x, y = 0, page_h - h_pt
            
    c.save()
    buffer.seek(0)
    return buffer

# --- 7. プレビュー表示 ---
if messages:
    pdf_buffer = create_card_pdf(messages, card_width, card_height, font_size)
    if pdf_buffer:
        st.header("2. プレビュー & ダウンロード")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.info(f"合計 {len(messages)} 枚")
            st.download_button("📄 PDFを保存", data=pdf_buffer, file_name="message_cards.pdf", mime="application/pdf")
        with col2:
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
else:
    st.info("メッセージを入力するとプレビューが表示されます。")
