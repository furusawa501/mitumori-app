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

- [x] `routes/customers.py` を作成
  - [x] `GET  /customers` — 一覧
  - [x] `GET  /customers/new` — 登録フォーム
  - [x] `POST /customers` — 作成
  - [x] `GET  /customers/{id}` — 詳細
  - [x] `GET  /customers/{id}/edit` — 編集フォーム
  - [x] `POST /customers/{id}/edit` — 更新
  - [x] `POST /customers/{id}/delete` — 削除（関連データありは 400）
- [x] `templates/customers/list.html`
- [x] `templates/customers/form.html`（新規・編集共用）
- [x] `templates/customers/detail.html`

---

## Phase 2 — 見積書

- [x] `services/numbering.py` を作成（`next_quote_number`, `next_invoice_number`）
- [x] `routes/quotes.py` を作成
  - [x] `GET  /quotes` — 一覧（`?status=` フィルタ付き）
  - [x] `GET  /quotes/new` — 作成フォーム
  - [x] `POST /quotes` — 作成（採番・金額初期化）
  - [x] `GET  /quotes/{id}` — 詳細
  - [x] `GET  /quotes/{id}/edit` — 編集フォーム
  - [x] `POST /quotes/{id}` — 更新（`draft` のみ、金額再計算）
  - [x] `POST /quotes/{id}/delete` — 削除（`draft` のみ）
  - [x] `POST /quotes/{id}/status` — ステータス変更（`send` / `accept` / `reject`）
  - [x] `POST /quotes/{id}/items` — 明細行追加
  - [x] `POST /quotes/{id}/items/{item_id}` — 明細行更新
  - [x] `POST /quotes/{id}/items/{item_id}/delete` — 明細行削除
- [x] `templates/quotes/list.html`
- [x] `templates/quotes/detail.html`（ステータスに応じたボタン切り替え）
- [x] `templates/quotes/form.html`（新規・編集共用、明細行の動的追加/削除は vanilla JS）

---

## Phase 3 — 請求書（変換）

- [x] `services/conversion.py` を作成（`convert_quote_to_invoice`）
  - `Quote.status` を `converted` に更新
  - 明細行・顧客・金額をコピーして `Invoice`（`status=draft`）を作成
  - `Invoice.quote_id` に元の `Quote.id` を記録
- [x] `routes/quotes.py` に変換エンドポイント追加
  - [x] `POST /quotes/{id}/convert` — 請求書に変換（`accepted` のみ）
- [x] `routes/invoices.py` を作成
  - [x] `GET  /invoices` — 一覧（`?status=` フィルタ付き）
  - [x] `GET  /invoices/{id}` — 詳細
  - [x] `GET  /invoices/{id}/edit` — 編集フォーム（`draft` のみ表示）
  - [x] `POST /invoices/{id}` — 更新（`draft` のみ、金額再計算）
  - [x] `POST /invoices/{id}/status` — ステータス変更（`send` / `pay` / `overdue`）
  - [x] `POST /invoices/{id}/items` — 明細行追加
  - [x] `POST /invoices/{id}/items/{item_id}` — 明細行更新
  - [x] `POST /invoices/{id}/items/{item_id}/delete` — 明細行削除
- [x] `templates/invoices/list.html`
- [x] `templates/invoices/detail.html`（ステータスに応じたボタン切り替え、変換元リンク）
- [x] `templates/invoices/form.html`（編集用）

---

## Phase 4 — PDF 生成

- [x] `services/pdf.py` を作成（`generate_quote_pdf`, `generate_invoice_pdf`）
- [x] `templates/pdf/quote.html`（WeasyPrint 用、印刷スタイル付き）
- [x] `templates/pdf/invoice.html`（WeasyPrint 用、印刷スタイル付き）
- [x] `routes/quotes.py` に PDF エンドポイント追加
  - [x] `GET /quotes/{id}/pdf`
- [x] `routes/invoices.py` に PDF エンドポイント追加
  - [x] `GET /invoices/{id}/pdf`

---

## Phase 5 — ダッシュボード

- [x] `routes/dashboard.py` を作成（`GET /`）
  - `sent` 状態の見積書件数・合計金額
  - `sent` + `overdue` 状態の請求書件数・合計金額
  - 直近5件の見積書・請求書
- [x] `templates/dashboard.html`

---

## 運用メモ

- 各 Phase は上から順に実装する（下位 Phase が上位に依存）
- タスク完了後はこのファイルの `[ ]` を `[x]` に更新してコミット
- スコープ追加が必要になったら末尾に `## 追加タスク` セクションを作る
