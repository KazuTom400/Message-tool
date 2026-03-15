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
        try:
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
            return True
        except:
            return False
    return False

HAS_FONT = register_font()
USED_FONT = FONT_NAME if HAS_FONT else "Helvetica"

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
    "メッセージを入力（改行2回で次のカードへ）",
    placeholder="田中さん\nお疲れ様でした！\n\n佐藤さん\nいつもありがとうございます。",
    height=250
)

messages = re.split(r'\n{2,}', input_text.strip()) if input_text.strip() else []

# --- 5. 文字の折り返し計算ロジック ---
def wrap_text(text, max_width_pt, f_name, f_size):
    """フォントサイズとカード幅から、文字を折り返す"""
    lines = []
    # ユーザーの改行でまず分ける
    for paragraph in text.split('\n'):
        current_line = ""
        for char in paragraph:
            # 現在の行に1文字足した時の横幅を計算
            test_line = current_line + char
            w = pdfmetrics.stringWidth(test_line, f_name, f_size)
            if w <= max_width_pt:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
        lines.append(current_line)
    return lines

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
    margin_pt = 5 * mm # 左右に最低限の余白(5mm)を確保
    max_text_width = w_pt - (margin_pt * 2)
    
    for i, msg in enumerate(msg_list):
        c.setLineWidth(0.2)
        c.rect(x, y, w_pt, h_pt)
        c.setFont(USED_FONT, f_size)
        
        # 動的な折り返し処理
        display_lines = wrap_text(msg, max_text_width, USED_FONT, f_size)

        # 垂直中央揃え
        total_text_h = len(display_lines) * f_size * line_spacing
        start_y = y + (h_pt + total_text_h)/2 - f_size
        
        for idx, line in enumerate(display_lines):
            line_y = start_y - (idx * f_size * line_spacing)
            c.drawCentredString(x + w_pt/2, line_y, line)
        
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

# --- 7. メイン表示エリア ---
if messages:
    pdf_buffer = create_card_pdf(messages, card_width, card_height, font_size)
    if pdf_buffer:
        st.header("2. プレビュー & 保存")
        st.info(f"合計 {len(messages)} 枚のカードを作成しました。")
        
        # プレビューが見られない場合のためのダウンロードボタンを強調
        st.download_button(
            label="📩 PDFをダウンロードして確認",
            data=pdf_buffer,
            file_name="message_cards.pdf",
            mime="application/pdf",
            primary=True
        )
        
        # プレビュー表示の改善
        try:
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            # ChromeやEdgeで表示されやすいようembedタグに変更
            pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">'
            st.markdown(pdf_display, unsafe_allow_html=True)
        except Exception as e:
            st.warning("お使いのブラウザではプレビューを表示できません。上のボタンから保存してください。")
else:
    st.info("メッセージを入力するとプレビューが表示されます。")
