# -*- coding: utf-8 -*-
# Pythonista: PAD EHP/軽減 計算 v7a(加算版)
# ・HP入力モード(素のHP/最終HP)
# ・敵属性
# ・覚醒/潜在の属性軽減は「加算」
# ・チームHP強化は (1 + 0.05*n)
# ・結果は箇条書き表示

import ui

ROW_H = 36
MARGIN = 12
GAP = 14
ATTRS = [('火','F'), ('水','W'), ('木','G'), ('光','L'), ('闇','D')]

class Form(ui.View):
    def __init__(self):
        super().__init__()
        self.name = 'パズドラ 簡易EHP/軽減 計算 v7a'
        self.bg_color = 'white'
        self._keyboard_inset = 0

        self.sv = ui.ScrollView(flex='WH', always_bounce_vertical=True)
        self.add_subview(self.sv)

        self.content = ui.View(bg_color='white')
        self.sv.add_subview(self.content)

        self.inputs = {}
        self.rows = []
        self.attr_rows = []  # (label, prefix, {key->tf})

        y = MARGIN

        # --- HP入力モード ---
        mode_label = ui.Label(text='HP入力モード', font=('<System>', 14))
        self.content.add_subview(mode_label)
        self.mode = ui.SegmentedControl(segments=['素のHP', '最終HP'])
        self.mode.selected_index = 0
        self.mode.action = self._on_mode_change
        self.content.add_subview(self.mode)
        self.rows.append((mode_label, None))
        y += 22 + ROW_H + GAP

        def add_row(key, title, ph=''):
            nonlocal y
            lb = ui.Label(text=title); lb.font = ('<System>', 14)
            self.content.add_subview(lb)
            tf = ui.TextField(placeholder=ph)
            tf.border_width = 1; tf.corner_radius = 6
            tf.border_color = (0.85, 0.85, 0.85)
            tf.clear_button_mode = 'while_editing'
            tf.keyboard_type = ui.KEYBOARD_NUMBERS
            tf.delegate = self
            self.content.add_subview(tf)
            self.rows.append((lb, tf))
            self.inputs[key] = tf
            y += 20 + 2 + ROW_H + GAP

        # 入力
        add_row('team_hp',   'チームHP(素のHP または 最終HP)', '例: 123456')
        add_row('teamhp_awkn','チームHP強化(覚醒) 個数', '0')     # ← (1+0.05*n) で加算
        add_row('ldr_hp',    'リーダーHP倍率', '1')
        add_row('sub_hp',    'サブHP倍率', '1')
        add_row('etc_hp',    'その他HP倍率(任意)', '1')
        add_row('ldr_red',   'リーダー軽減率', '例: 35 or 35%')
        add_row('sub_red',   'サブ軽減率', '例: 25 or 25%')
        add_row('add1',      '追加軽減1', '例: 5 or 5% (覚醒/バッジ等)')
        add_row('add2',      '追加軽減2', '')

        # 敵の属性
        attr_label = ui.Label(text='敵の属性(属性軽減の適用先)', font=('<System>', 14))
        self.content.add_subview(attr_label)
        self.enemy_attr = ui.SegmentedControl(segments=[a for a,_ in ATTRS] + ['なし'])
        self.enemy_attr.selected_index = len(ATTRS)  # なし
        self.content.add_subview(self.enemy_attr)
        self.rows.append((attr_label, None))

        # 属性軽減行(覚醒7% / 潜在1% / 潜在+2.5%)
        def add_attr_row(prefix, title):
            lb = ui.Label(text=title); lb.font = ('<System>', 14)
            self.content.add_subview(lb)
            row_tfs = {}
            for _, key in ATTRS:
                tf = ui.TextField(placeholder='0')
                tf.border_width = 1; tf.corner_radius = 6
                tf.border_color = (0.85, 0.85, 0.85)
                tf.clear_button_mode = 'while_editing'
                tf.keyboard_type = ui.KEYBOARD_NUMBERS
                tf.delegate = self
                self.content.add_subview(tf)
                row_tfs[f'{prefix}_{key}'] = tf
                self.inputs[f'{prefix}_{key}'] = tf
            self.attr_rows.append((lb, prefix, row_tfs))

        add_attr_row('aw7',  '属性軽減(覚醒 7%):各属性の個数[火/水/木/光/闇]')
        add_attr_row('lat1', '属性軽減(潜在 1%/1枠):各属性の個数')
        add_attr_row('lat25','属性軽減+(潜在 2.5%/2枠):各属性の個数')

        # 敵ダメージ
        add_row('enemy',     '敵のダメージ(任意)', '例: 999999')

        # ボタン & 結果
        self.btn = ui.Button(title='計算', corner_radius=8,
                             background_color='#007aff', tint_color='white')
        self.btn.action = self.calculate
        self.content.add_subview(self.btn)

        self.result = ui.TextView(editable=False, selectable=True,
                                  border_width=1, corner_radius=6,
                                  border_color=(0.85,0.85,0.85))
        self.content.add_subview(self.result)

        self._relayout()
        self._apply_mode()

    # ---------- レイアウト ----------
    def layout(self): self._relayout()

    def _relayout(self):
        self.sv.frame = self.bounds
        W = self.width - MARGIN*2; x = MARGIN; y = MARGIN

        # HP入力モード
        self.rows[0][0].frame = (x, y, W, 20); y += 22
        self.mode.frame = (x, y, W, ROW_H); y += ROW_H + GAP

        # team_hp〜add2(8行)
        for i in range(1, 9+1):
            lb, tf = self.rows[i]
            lb.frame = (x, y, W, 20); y += 22
            tf.frame = (x, y, W, ROW_H); y += ROW_H + GAP

        # 敵属性
        lb, _ = self.rows[10]
        lb.frame = (x, y, W, 20); y += 22
        self.enemy_attr.frame = (x, y, W, ROW_H); y += ROW_H + GAP

        # 属性行は5分割
        col_gap = 8
        col_w = (W - col_gap*4) / 5.0
        for lb, prefix, row_tfs in self.attr_rows:
            lb.frame = (x, y, W, 20); y += 22
            cx = x
            for _, key in ATTRS:
                row_tfs[f'{prefix}_{key}'].frame = (cx, y, col_w, ROW_H)
                cx += col_w + col_gap
            y += ROW_H + GAP

        # 敵ダメージ(rows[11])
        lb, tf = self.rows[11]
        lb.frame = (x, y, W, 20); y += 22
        tf.frame = (x, y, W, ROW_H); y += ROW_H + GAP

        self.btn.frame = (x, y, W, 44); y += 54
        self.result.frame = (x, y, W, 200); y += 200 + MARGIN

        self.content.frame = (0, 0, self.width, y)
        self.sv.content_size = (self.width, y + self._keyboard_inset)

    # ---------- TextField delegate ----------
    def textfield_did_begin_editing(self, tf):
        self._keyboard_inset = 320
        self.sv.content_inset = (0, 0, self._keyboard_inset, 0)
        target_y = max(tf.y - 60, 0)
        max_off = max(0, self.sv.content_size[1] - self.sv.height)
        self.sv.content_offset = (0, min(target_y, max_off))

    def textfield_did_end_editing(self, tf):
        self._keyboard_inset = 0
        self.sv.content_inset = (0, 0, 0, 0)
        self._relayout()

    # ---------- モード ----------
    def _on_mode_change(self, sender): self._apply_mode()

    def _apply_mode(self):
        final_mode = (self.mode.selected_index == 1)  # 1=最終HP
        for key in ('ldr_hp', 'sub_hp', 'etc_hp'):
            tf = self.inputs[key]
            if final_mode:
                tf.text = '1'; tf.enabled = False; tf.alpha = 0.5
            else:
                if not tf.text: tf.text = '1'
                tf.enabled = True; tf.alpha = 1.0
        tf_hpawk = self.inputs['teamhp_awkn']
        if final_mode:
            tf_hpawk.text = '0'; tf_hpawk.enabled = False; tf_hpawk.alpha = 0.5
        else:
            tf_hpawk.enabled = True; tf_hpawk.alpha = 1.0

    # ---------- パース ----------
    def _pct(self, s):
        s = (s or '').strip().replace('%', '')
        if not s: return 0.0
        try: return float(s)/100.0
        except: return 0.0

    def _mul(self, s):
        s = (s or '').strip()
        if not s: return 1.0
        try: return float(s)
        except: return 1.0

    def _to_int(self, s):
        try: return int((s or '0').replace(',', ''))
        except: return 0

    def _to_nonneg_int(self, s):
        v = self._to_int(s);  return max(v, 0)

    # 属性軽減(同属性内は加算、合計上限100%)
    def _attr_coeff_and_desc(self):
        seg = self.enemy_attr.selected_index
        if seg >= len(ATTRS):
            return 1.0, '—', 0, 0, 0, 0.0
        jp, key = ATTRS[seg][0], ATTRS[seg][1]
        n7   = self._to_nonneg_int(self.inputs[f'aw7_{key}'].text)
        n1   = self._to_nonneg_int(self.inputs[f'lat1_{key}'].text)
        n25  = self._to_nonneg_int(self.inputs[f'lat25_{key}'].text)
        total = 0.07*n7 + 0.01*n1 + 0.025*n25   # ← 加算
        total = max(0.0, min(total, 1.0))       # 上限100%
        coeff = 1.0 - total
        return coeff, jp, n7, n1, n25, total*100.0

    # ---------- 計算 ----------
    def calculate(self, sender):
        input_hp = self._to_int(self.inputs['team_hp'].text)
        final_mode = (self.mode.selected_index == 1)

        hp_mul = self._mul(self.inputs['ldr_hp'].text) \
               * self._mul(self.inputs['sub_hp'].text) \
               * self._mul(self.inputs['etc_hp'].text)

        # チームHP強化:加算 (1 + 0.05*n)
        hp_awk_n = self._to_nonneg_int(self.inputs['teamhp_awkn'].text)
        if not final_mode:
            hp_mul *= (1.0 + 0.05*hp_awk_n)

        final_hp = input_hp if final_mode else int(round(input_hp * hp_mul))

        # 一般軽減(乗算)
        base_coeff = 1.0
        for k in ('ldr_red','sub_red','add1','add2'):
            base_coeff *= (1.0 - self._pct(self.inputs[k].text))

        # 属性軽減(加算→係数へ)
        attr_coeff, attr_jp, n7, n1, n25, attr_pct = self._attr_coeff_and_desc()

        dmg_coeff = base_coeff * attr_coeff
        total_red = 1.0 - dmg_coeff
        ehp = int(round(final_hp / max(dmg_coeff, 1e-9)))

        enemy = self._to_int(self.inputs['enemy'].text)

        lines = []
        b = '・ '
        lines.append(b + f'HP入力モード: {"最終HP" if final_mode else "素のHP"}')
        if not final_mode:
            lines.append(b + f'HP倍率の積(チームHP強化含む): ×{hp_mul:.4f}  '
                           f'※チームHP強化={hp_awk_n}個 → ×(1+0.05×{hp_awk_n})')

        lines.append(b + f'最終HP: {final_hp:,}')
        lines.append(b + f'総軽減(実質軽減率): {total_red*100:.2f}%')
        lines.append(b + f'被ダメ係数: {dmg_coeff:.6f}')
        lines.append(b + f'実効HP(EHP): {ehp:,}')

        if self.enemy_attr.selected_index < len(ATTRS):
            lines.append(b + f'属性軽減(敵属性: {attr_jp}) [加算] '
                           f'覚醒7%×{n7}, 潜在1%×{n1}, 潜在2.5%×{n25} '
                           f'合計: {attr_pct:.2f}%')

        if enemy > 0:
            taken = int(round(enemy * dmg_coeff))
            remain = final_hp - taken
            remain_pct = (remain/final_hp*100.0) if final_hp>0 else 0.0
            need_hp = int(enemy * dmg_coeff) + 1
            lives = remain >= 1
            lines.append(b + f'敵ダメージ: {enemy:,}')
            lines.append(b + f'実際に受けるダメージ: {taken:,}')
            lines.append(b + f'残りHP: {max(remain,0):,} ({max(remain_pct,0):.2f}%)')
            lines.append(b + f'生存可否: {"◯ 生存" if lives else "× 撃沈"}')
            lines.append(b + f'このダメージを1残しで耐える最終HP: {need_hp:,}')

        self.result.text = '\n'.join(lines)

def main():
    v = Form()
    v.present('fullscreen')

if __name__ == '__main__':
    main()
