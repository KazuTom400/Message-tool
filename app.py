import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import re
import os
import fitz  # PyMuPDF

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
base_font_size = st.sidebar.number_input("基準文字サイズ (pt)", min_value=5, value=12, step=1)
line_spacing = st.sidebar.number_input("行間", min_value=1.0, value=1.2, step=0.1)

# --- 4. 文字の折り返し計算関数 ---
def get_wrapped_lines(text, max_width_pt, f_name, f_size):
    """指定された幅でテキストを折り返し、行のリストを返す"""
    lines = []
    for paragraph in text.split('\n'):
        current_line = ""
        for char in paragraph:
            test_line = current_line + char
            w = pdfmetrics.stringWidth(test_line, f_name, f_size)
            if w <= max_width_pt:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
        lines.append(current_line)
    return lines

# --- 5. PDF生成関数（自動縮小ロジック付き） ---
def create_card_pdf(msg_list, w_mm, h_mm, start_f_size):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4
    w_pt, h_pt = w_mm * mm, h_mm * mm
    cols = int(page_w // w_pt)
    rows = int(page_h // h_pt)
    
    if cols == 0 or rows == 0:
        return None

    x, y = 0, page_h - h_pt
    margin_pt = 5 * mm 
    max_text_width = w_pt - (margin_pt * 2)
    max_text_height = h_pt - (margin_pt * 2)
    
    for i, msg in enumerate(msg_list):
        c.setLineWidth(0.2)
        c.rect(x, y, w_pt, h_pt)
        
        # --- 自動フォント縮小ロジック ---
        current_f_size = start_f_size
        min_f_size = 5 # 最小サイズを5ptに設定
        
        while current_f_size >= min_f_size:
            display_lines = get_wrapped_lines(msg, max_text_width, USED_FONT, current_f_size)
            total_text_h = len(display_lines) * current_f_size * line_spacing
            
            # 高さが枠内に収まればループ終了
            if total_text_h <= max_text_height:
                break
            # 収まらなければ1pt小さくして再計算
            current_f_size -= 1

        c.setFont(USED_FONT, current_f_size)
        start_y = y + (h_pt + (len(display_lines) * current_f_size * line_spacing))/2 - current_f_size
        
        for idx, line in enumerate(display_lines):
            line_y = start_y - (idx * current_f_size * line_spacing)
            c.drawCentredString(x + w_pt/2, line_y, line)
        
        # 配置移動
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

# --- 6. メイン表示エリア ---
st.header("1. メッセージ入力")
input_text = st.text_area("改行2回でカードを分割します", height=200)

st.header("2. プレビュー & 保存")
if st.button("🛠️ メッセージカードを作成する", type="primary"):
    if input_text.strip():
        messages = re.split(r'\n{2,}', input_text.strip())
        pdf_data = create_card_pdf(messages, card_width, card_height, base_font_size)
        
        if pdf_data:
            # プレビュー画像生成
            doc = fitz.open(stream=pdf_data.getvalue(), filetype="pdf")
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img_bytes = pix.tobytes("png")
            doc.close()
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(img_bytes, caption="プレビュー（1枚目）")
            with col2:
                st.success(f"カード計 {len(messages)} 枚")
                st.download_button(
                    label="📄 PDFを保存する",
                    data=pdf_data.getvalue(),
                    file_name="message_cards.pdf",
                    mime="application/pdf"
                )
                st.info("【iPhoneの方】保存後、ブラウザの『ダウンロードフォルダ』を確認してください。")
    else:
        st.warning("メッセージを入力してください。")
