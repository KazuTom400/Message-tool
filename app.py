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

# --- フォント設定 ---
# リポジトリにアップロードしたフォントファイル名に合わせてください
FONT_FILE = "ipaexg.ttf" 
FONT_NAME = "JapaneseFont"

def register_font():
    if os.path.exists(FONT_FILE):
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
        return True
    return False

has_font = register_font()

st.set_page_config(page_title="メッセージカード作成", layout="wide")
st.title("📇 メッセージカード作成ツール")

# --- サイドバー設定 ---
st.sidebar.header("1. カードサイズ設定 (mm)")
card_width = st.sidebar.number_input("横幅", min_value=10.0, value=91.0, step=1.0)
card_height = st.sidebar.number_input("縦幅", min_value=10.0, value=55.0, step=1.0)
font_size = st.sidebar.number_input("文字サイズ (pt)", min_value=5, value=11, step=1)

# --- 入力エリア ---
input_text = st.text_area("メッセージをスペースで区切って入力", placeholder="田中さん 佐藤さん 鈴木さん", height=200)
messages = re.split(r'\s+', input_text.strip()) if input_text.strip() else []

# PDF生成ロジック (中略：基本は前回と同じですがFONT_NAMEを使用)
def create_card_pdf(msg_list, w_mm, h_mm, f_size):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w_pt, h_pt = w_mm * mm, h_mm * mm
    cols = int(A4[0] // w_pt)
    rows = int(A4[1] // h_pt)
    x, y = 0, A4[1] - h_pt
    
    for i, msg in enumerate(msg_list):
        c.setLineWidth(0.3)
        c.rect(x, y, w_pt, h_pt)
        c.setFont(FONT_NAME if has_font else "Helvetica", f_size)
        
        # 簡易中央揃え（1行）
        c.drawCentredString(x + w_pt/2, y + h_pt/2 - f_size/3, msg)
        
        x += w_pt
        if (i + 1) % cols == 0:
            x = 0
            y -= h_pt
        if (i + 1) % (cols * rows) == 0 and (i + 1) < len(msg_list):
            c.showPage()
            x, y = 0, A4[1] - h_pt
    c.save()
    buffer.seek(0)
    return buffer

if messages:
    pdf_buffer = create_card_pdf(messages, card_width, card_height, font_size)
    if pdf_buffer:
        st.download_button("📩 PDFをダウンロード", data=pdf_buffer, file_name="cards.pdf")
        base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
