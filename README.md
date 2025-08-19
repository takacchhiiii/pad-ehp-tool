# パズドラ 簡易EHP/軽減 計算 v7a（ブラウザ版）

Pythonista の `ui` アプリを **HTML + JavaScript** に移植したものです。**GitHub Pages** に置くだけで公開できます。

## 公開手順（GitHub Pages）

1. GitHubで新規リポジトリを作成（例: `pad-ehp-web-v7a`）。
2. このリポジトリに `index.html` `script.js` `styles.css` `README.md` をアップロード＆コミット。
3. リポジトリの **Settings → Pages** で  
   - **Build and deployment**: 「Deploy from a branch」  
   - **Branch**: `main` / `master` の `/ (root)` を選択 → **Save**
4. 数十秒後、`https://<ユーザー名>.github.io/<リポジトリ名>/` で公開されます。

## 仕様（Python版 v7a を踏襲）
- **HP入力モード**: 「素のHP」/「最終HP」
- **チームHP強化**: `(1 + 0.05 * n)`（素のHPモードのときのみ有効）
- **一般軽減は乗算**: リーダー/サブ/追加1/追加2 を `%` で入力（`35` または `35%`）
- **属性軽減は加算**: 覚醒 7% / 潜在 1% / 潜在 2.5% を同属性内で加算（上限 100%）し、敵の属性にのみ適用
- **表示**: 実質軽減率・被ダメ係数・実効HP(EHP)・敵ダメージ時の耐久可否など

---

© あなたの名前
