# --- 入力エリアの処理部分を以下に差し替え ---

# 【変更点】区切り文字を「半角スペース」と「全角スペース」のみに限定
# これにより、改行が含まれていても同じカード内の文字として扱われます
messages = re.split(r'[ 　]+', input_text.strip()) if input_text.strip() else []

# --- PDF生成ロジック（描画部分）の修正 ---
def create_card_pdf(msg_list, w_mm, h_mm, f_size):
    # ... (前後のコードは共通) ...
    
    for i, msg in enumerate(msg_list):
        c.setLineWidth(0.2)
        c.rect(x, y, w_pt, h_pt)
        c.setFont(FONT_NAME if HAS_FONT else "Helvetica", f_size)
        
        # 【修正】メッセージ内の改行コード(\n)を維持しつつ、長い行を自動折り返し
        raw_lines = msg.split('\n') # まずユーザーが打った改行で分ける
        all_display_lines = []
        
        # カード幅に収まる文字数を計算
        chars_per_line = max(1, int((w_pt * 0.8) / (f_size * 0.6)))
        
        for r_line in raw_lines:
            # ユーザーが打った1行が長すぎる場合はさらに分割
            split_lines = [r_line[j:j+chars_per_line] for j in range(0, len(r_line), chars_per_line)]
            all_display_lines.extend(split_lines if split_lines else [""])

        # 垂直中央揃えの計算（全行数に基づき算出）
        total_text_h = len(all_display_lines) * f_size * line_spacing
        start_y = y + (h_pt + total_text_h)/2 - f_size
        
        for idx, line in enumerate(all_display_lines):
            line_y = start_y - (idx * f_size * line_spacing)
            c.drawCentredString(x + w_pt/2, line_y, line)
            
        # ... (配置移動・改ページ処理は共通) ...
