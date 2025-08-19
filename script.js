// Browser port of Pythonista 'PAD EHP/軽減 計算 v7a(加算版)'
// - HP入力モード（素のHP/最終HP）
// - チームHP強化 (1 + 0.05*n) ※素のHPモードのときのみ有効
// - 一般軽減は乗算（リーダー/サブ/追加1/追加2）
// - 属性軽減（覚醒7%, 潜在1%, 潜在2.5%）は同属性内で加算、上限100%
// - 実効HP、被ダメ係数、実際の被ダメ、耐える/耐えない等を表示

const ATTRS = [
  ['火', 'F'], ['水', 'W'], ['木', 'G'], ['光', 'L'], ['闇', 'D']
];

function toInt(s) {
  if (s === null || s === undefined) return 0;
  s = String(s).replace(/,/g, '').trim();
  if (s === '') return 0;
  const v = parseInt(s, 10);
  return Number.isFinite(v) ? v : 0;
}

function toNonNegInt(s) {
  return Math.max(0, toInt(s));
}

function toMul(s) {
  if (s === null || s === undefined) return 1.0;
  s = String(s).trim();
  if (s === '') return 1.0;
  const v = parseFloat(s);
  return Number.isFinite(v) ? v : 1.0;
}

// "35" / "35%" -> 0.35
function pct(s) {
  s = (s ?? '').toString().trim().replace('%', '');
  if (!s) return 0.0;
  const v = parseFloat(s);
  return Number.isFinite(v) ? v / 100.0 : 0.0;
}

function fmtInt(n) { return Math.round(n).toLocaleString('ja-JP'); }
function fmt(n, d=4) { return Number(n).toFixed(d); }

function attrCoeffAndDesc() {
  const sel = document.getElementById('enemy_attr').value;
  if (sel === 'none') return { coeff: 1.0, jp: '—', n7:0, n1:0, n25:0, totalPct:0.0 };

  const map = {F:'火', W:'水', G:'木', L:'光', D:'闇'};
  const jp = map[sel];

  const n7 = toNonNegInt(document.getElementById(`aw7_${sel}`).value);
  const n1 = toNonNegInt(document.getElementById(`lat1_${sel}`).value);
  const n25 = toNonNegInt(document.getElementById(`lat25_${sel}`).value);

  let total = 0.07*n7 + 0.01*n1 + 0.025*n25;    // 加算
  total = Math.min(1.0, Math.max(0.0, total));   // 0〜1に制限
  const coeff = 1.0 - total;
  return { coeff, jp, n7, n1, n25, totalPct: total*100.0 };
}

function applyMode() {
  const finalMode = document.getElementById('modeFinal').checked;
  const idsMul = ['ldr_hp','sub_hp','etc_hp'];
  idsMul.forEach(id => {
    const el = document.getElementById(id);
    if (finalMode) { el.value = '1'; el.disabled = true; el.classList.add('disabled'); }
    else { if (!el.value) el.value = '1'; el.disabled = false; el.classList.remove('disabled'); }
  });
  const awk = document.getElementById('teamhp_awkn');
  if (finalMode) { awk.value = '0'; awk.disabled = true; awk.classList.add('disabled'); }
  else { awk.disabled = false; awk.classList.remove('disabled'); }
}

function calc() {
  const finalMode = document.getElementById('modeFinal').checked;

  const input_hp = toInt(document.getElementById('team_hp').value);
  let hp_mul = toMul(document.getElementById('ldr_hp').value)
             * toMul(document.getElementById('sub_hp').value)
             * toMul(document.getElementById('etc_hp').value);

  const hp_awk_n = toNonNegInt(document.getElementById('teamhp_awkn').value);
  if (!finalMode) hp_mul *= (1.0 + 0.05 * hp_awk_n);

  const final_hp = finalMode ? input_hp : Math.round(input_hp * hp_mul);

  // 一般軽減（乗算）
  let base_coeff = 1.0;
  ['ldr_red','sub_red','add1','add2'].forEach(id => {
    base_coeff *= (1.0 - pct(document.getElementById(id).value));
  });

  // 属性軽減（加算→係数）
  const attr = attrCoeffAndDesc();
  const dmg_coeff = base_coeff * attr.coeff;
  const total_red = 1.0 - dmg_coeff;
  const ehp = Math.round(final_hp / Math.max(dmg_coeff, 1e-9));

  // 敵ダメージ
  const enemy = toInt(document.getElementById('enemy').value);
  const bullet = '・ ';
  const lines = [];
  lines.push(bullet + 'HP入力モード: ' + (finalMode ? '最終HP' : '素のHP'));

  if (!finalMode) {
    lines.push(bullet + `HP倍率の積(チームHP強化含む): ×${fmt(hp_mul)}  ※チームHP強化=${hp_awk_n}個 → ×(1+0.05×${hp_awk_n})`);
  }

  lines.push(bullet + `最終HP: ${fmtInt(final_hp)}`);
  lines.push(bullet + `総軽減(実質軽減率): ${(total_red*100).toFixed(2)}%`);
  lines.push(bullet + `被ダメ係数: ${dmg_coeff.toFixed(6)}`);
  lines.push(bullet + `実効HP(EHP): ${fmtInt(ehp)}`);

  if (document.getElementById('enemy_attr').value !== 'none') {
    lines.push(bullet + `属性軽減(敵属性: ${attr.jp}) [加算] 覚醒7%×${attr.n7}, 潜在1%×${attr.n1}, 潜在2.5%×${attr.n25} 合計: ${attr.totalPct.toFixed(2)}%`);
  }

  if (enemy > 0) {
    const taken = Math.round(enemy * dmg_coeff);
    const remain = final_hp - taken;
    const remain_pct = final_hp > 0 ? (remain / final_hp * 100.0) : 0.0;
    const need_hp = Math.floor(enemy * dmg_coeff) + 1;
    const lives = remain >= 1;

    lines.push(bullet + `敵ダメージ: ${fmtInt(enemy)}`);
    lines.push(bullet + `実際に受けるダメージ: ${fmtInt(taken)}`);
    lines.push(bullet + `残りHP: ${fmtInt(Math.max(remain,0))} (${Math.max(remain_pct,0).toFixed(2)}%)`);
    lines.push(bullet + `生存可否: ${lives ? '◯ 生存' : '× 撃沈'}`);
    lines.push(bullet + `このダメージを1残しで耐える最終HP: ${fmtInt(need_hp)}`);
  }

  document.getElementById('results').textContent = lines.join('\n');
}

document.getElementById('modeBase').addEventListener('change', applyMode);
document.getElementById('modeFinal').addEventListener('change', applyMode);
document.getElementById('calcBtn').addEventListener('click', calc);

applyMode();
