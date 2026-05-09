# 実装タスク

実装が完了したタスクは `[ ]` を `[x]` に更新すること。
設計書: `docs/schema.md` / `docs/screen-flow.md` / `docs/api.md`

---

## Phase 0 — 基盤

- [x] `.env` を `.env.example` からコピーして `SECRET_KEY` を設定
- [x] `database.py` を作成（`Base`, `engine`, `SessionLocal`, `get_db`）
- [x] `models.py` を作成（`Customer`, `Quote`, `Invoice`, `LineItem`）
- [x] `main.py` を作成（`FastAPI` インスタンス、セッションミドルウェア、ルーター登録、起動時 DB 初期化）
- [x] `templates/base.html` を作成（Tailwind CDN, ナビゲーション, フラッシュメッセージ枠）

---

## Phase 1 — 顧客管理

- [ ] `routes/customers.py` を作成
  - [ ] `GET  /customers` — 一覧
  - [ ] `GET  /customers/new` — 登録フォーム
  - [ ] `POST /customers` — 作成
  - [ ] `GET  /customers/{id}` — 詳細
  - [ ] `GET  /customers/{id}/edit` — 編集フォーム
  - [ ] `POST /customers/{id}/edit` — 更新
  - [ ] `POST /customers/{id}/delete` — 削除（関連データありは 400）
- [ ] `templates/customers/list.html`
- [ ] `templates/customers/form.html`（新規・編集共用）
- [ ] `templates/customers/detail.html`

---

## Phase 2 — 見積書

- [ ] `services/numbering.py` を作成（`next_quote_number`, `next_invoice_number`）
- [ ] `routes/quotes.py` を作成
  - [ ] `GET  /quotes` — 一覧（`?status=` フィルタ付き）
  - [ ] `GET  /quotes/new` — 作成フォーム
  - [ ] `POST /quotes` — 作成（採番・金額初期化）
  - [ ] `GET  /quotes/{id}` — 詳細
  - [ ] `GET  /quotes/{id}/edit` — 編集フォーム
  - [ ] `POST /quotes/{id}` — 更新（`draft` のみ、金額再計算）
  - [ ] `POST /quotes/{id}/delete` — 削除（`draft` のみ）
  - [ ] `POST /quotes/{id}/status` — ステータス変更（`send` / `accept` / `reject`）
  - [ ] `POST /quotes/{id}/items` — 明細行追加
  - [ ] `POST /quotes/{id}/items/{item_id}` — 明細行更新
  - [ ] `POST /quotes/{id}/items/{item_id}/delete` — 明細行削除
- [ ] `templates/quotes/list.html`
- [ ] `templates/quotes/detail.html`（ステータスに応じたボタン切り替え）
- [ ] `templates/quotes/form.html`（新規・編集共用、明細行の動的追加/削除は vanilla JS）

---

## Phase 3 — 請求書（変換）

- [ ] `services/conversion.py` を作成（`convert_quote_to_invoice`）
  - `Quote.status` を `converted` に更新
  - 明細行・顧客・金額をコピーして `Invoice`（`status=draft`）を作成
  - `Invoice.quote_id` に元の `Quote.id` を記録
- [ ] `routes/quotes.py` に変換エンドポイント追加
  - [ ] `POST /quotes/{id}/convert` — 請求書に変換（`accepted` のみ）
- [ ] `routes/invoices.py` を作成
  - [ ] `GET  /invoices` — 一覧（`?status=` フィルタ付き）
  - [ ] `GET  /invoices/{id}` — 詳細
  - [ ] `GET  /invoices/{id}/edit` — 編集フォーム（`draft` のみ表示）
  - [ ] `POST /invoices/{id}` — 更新（`draft` のみ、金額再計算）
  - [ ] `POST /invoices/{id}/status` — ステータス変更（`send` / `pay` / `overdue`）
  - [ ] `POST /invoices/{id}/items` — 明細行追加
  - [ ] `POST /invoices/{id}/items/{item_id}` — 明細行更新
  - [ ] `POST /invoices/{id}/items/{item_id}/delete` — 明細行削除
- [ ] `templates/invoices/list.html`
- [ ] `templates/invoices/detail.html`（ステータスに応じたボタン切り替え、変換元リンク）
- [ ] `templates/invoices/form.html`（編集用）

---

## Phase 4 — PDF 生成

- [ ] `services/pdf.py` を作成（`generate_quote_pdf`, `generate_invoice_pdf`）
- [ ] `templates/pdf/quote.html`（WeasyPrint 用、印刷スタイル付き）
- [ ] `templates/pdf/invoice.html`（WeasyPrint 用、印刷スタイル付き）
- [ ] `routes/quotes.py` に PDF エンドポイント追加
  - [ ] `GET /quotes/{id}/pdf`
- [ ] `routes/invoices.py` に PDF エンドポイント追加
  - [ ] `GET /invoices/{id}/pdf`

---

## Phase 5 — ダッシュボード

- [ ] `routes/dashboard.py` を作成（`GET /`）
  - `sent` 状態の見積書件数・合計金額
  - `sent` + `overdue` 状態の請求書件数・合計金額
  - 直近5件の見積書・請求書
- [ ] `templates/dashboard.html`

---

## 運用メモ

- 各 Phase は上から順に実装する（下位 Phase が上位に依存）
- タスク完了後はこのファイルの `[ ]` を `[x]` に更新してコミット
- スコープ追加が必要になったら末尾に `## 追加タスク` セクションを作る
