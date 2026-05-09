# APIエンドポイント一覧

FastAPI + Jinja2 構成。HTMLフォームの送信は `POST`、JavaScript からのアクション（ステータス変更・明細行操作）も `POST` で統一。削除系は `POST /xxx/delete` パターン。

レスポンスの規則：
- 画面系（GET）→ HTML レンダリング
- アクション系（POST）→ 成功時は `303 See Other` でリダイレクト
- エラー時は `400` / `403` / `404` を返し、フラッシュメッセージで詳細を表示

---

## ダッシュボード

| メソッド | パス | 概要 |
|---------|------|------|
| `GET` | `/` | ダッシュボード表示 |

**GET /** レスポンス（テンプレート変数）

| 変数 | 内容 |
|------|------|
| `sent_quotes_count` | `sent` 状態の見積書件数 |
| `sent_quotes_total` | `sent` 状態の見積書合計金額（税込） |
| `pending_invoices_count` | `sent` + `overdue` 状態の請求書件数 |
| `pending_invoices_total` | `sent` + `overdue` 状態の請求書合計金額（税込） |
| `recent_quotes` | 直近5件の見積書（id, quote_number, customer_name, status, total, issue_date） |
| `recent_invoices` | 直近5件の請求書（id, invoice_number, customer_name, status, total, issue_date） |

---

## 顧客（Customers）

| メソッド | パス | 概要 | 対応画面 |
|---------|------|------|---------|
| `GET` | `/customers` | 顧客一覧 | S02 |
| `GET` | `/customers/new` | 顧客登録フォーム | S03 |
| `POST` | `/customers` | 顧客作成 | — |
| `GET` | `/customers/{id}` | 顧客詳細 | S04 |
| `GET` | `/customers/{id}/edit` | 顧客編集フォーム | S05 |
| `POST` | `/customers/{id}/edit` | 顧客更新 | — |
| `POST` | `/customers/{id}/delete` | 顧客削除 | — |

### POST /customers（顧客作成）

**フォームフィールド**

| フィールド | 必須 | 備考 |
|-----------|------|------|
| `company_name` | ✓ | |
| `contact_name` | ✓ | |
| `email` | ✓ | |
| `phone` | | |
| `address` | | 改行含む |
| `notes` | | |

**レスポンス**
- 成功 → `303` `/customers/{id}`
- バリデーションエラー → `400` フォーム再表示

### POST /customers/{id}/edit（顧客更新）

フォームフィールドは作成と同一。

**レスポンス**
- 成功 → `303` `/customers/{id}`

### POST /customers/{id}/delete（顧客削除）

**レスポンス**
- 成功 → `303` `/customers`
- 見積書または請求書が存在する場合 → `400` エラーメッセージ

---

## 見積書（Quotes）

| メソッド | パス | 概要 | 対応画面 |
|---------|------|------|---------|
| `GET` | `/quotes` | 見積書一覧 | S06 |
| `GET` | `/quotes/new` | 見積書作成フォーム | S07 |
| `POST` | `/quotes` | 見積書作成 | — |
| `GET` | `/quotes/{id}` | 見積書詳細 | S08 |
| `GET` | `/quotes/{id}/edit` | 見積書編集フォーム | S09 |
| `POST` | `/quotes/{id}` | 見積書更新 | — |
| `POST` | `/quotes/{id}/delete` | 見積書削除（draft のみ） | — |
| `POST` | `/quotes/{id}/status` | ステータス変更 | — |
| `POST` | `/quotes/{id}/convert` | 請求書に変換 | — |

### GET /quotes（見積書一覧）

**クエリパラメータ**

| パラメータ | デフォルト | 備考 |
|-----------|-----------|------|
| `status` | （全件） | `draft` / `sent` / `accepted` / `rejected` / `converted` でフィルタ |

### POST /quotes（見積書作成）

**フォームフィールド**

| フィールド | 必須 | 備考 |
|-----------|------|------|
| `customer_id` | ✓ | |
| `title` | ✓ | |
| `issue_date` | ✓ | YYYY-MM-DD |
| `valid_until` | | YYYY-MM-DD |
| `notes` | | |

**レスポンス**
- 成功 → `303` `/quotes/{id}`

### POST /quotes/{id}（見積書更新）

フォームフィールドは作成と同一。

**制約**
- `draft` 状態のみ更新可。それ以外は `403`

**レスポンス**
- 成功 → `303` `/quotes/{id}`

### POST /quotes/{id}/delete（見積書削除）

**制約**
- `draft` 状態のみ削除可。それ以外は `403`

**レスポンス**
- 成功 → `303` `/quotes`

### POST /quotes/{id}/status（ステータス変更）

**フォームフィールド**

| フィールド | 値 | 意味 |
|-----------|-----|------|
| `action` | `send` | `draft` → `sent`（明細行1件以上が条件） |
| `action` | `accept` | `sent` → `accepted` |
| `action` | `reject` | `sent` → `rejected` |

**レスポンス**
- 成功 → `303` `/quotes/{id}`
- 不正遷移 → `400`
- 明細行なしで `send` → `400`

### POST /quotes/{id}/convert（請求書に変換）

**前提条件**
- `accepted` 状態であること

**処理内容**
1. `Quote.status` を `converted` に更新
2. 明細行・顧客・金額をコピーして `Invoice`（`status=draft`）を作成
3. `Invoice.quote_id` に元の `Quote.id` を記録

**レスポンス**
- 成功 → `303` `/invoices/{new_invoice_id}`
- 不正ステータス → `400`

---

## 見積書明細行

| メソッド | パス | 概要 |
|---------|------|------|
| `POST` | `/quotes/{id}/items` | 明細行追加 |
| `POST` | `/quotes/{id}/items/{item_id}` | 明細行更新 |
| `POST` | `/quotes/{id}/items/{item_id}/delete` | 明細行削除 |

**フォームフィールド（追加・更新共通）**

| フィールド | 必須 | 備考 |
|-----------|------|------|
| `description` | ✓ | 品目名 |
| `quantity` | ✓ | 数値（0.5 等の小数可） |
| `unit` | | 単位（式・個・時間 etc.） |
| `unit_price` | ✓ | 整数（円） |
| `sort_order` | ✓ | 表示順（1始まり） |

**自動計算**
- `amount = floor(quantity × unit_price)`
- 明細行の変更後、親レコード（`subtotal` / `tax_amount` / `total`）を自動再計算

**制約**
- 見積書が `draft` 状態のみ操作可。それ以外は `403`

**レスポンス（全操作共通）**
- 成功 → `303` `/quotes/{id}/edit`

---

## 請求書（Invoices）

| メソッド | パス | 概要 | 対応画面 |
|---------|------|------|---------|
| `GET` | `/invoices` | 請求書一覧 | S11 |
| `GET` | `/invoices/{id}` | 請求書詳細 | S12 |
| `GET` | `/invoices/{id}/edit` | 請求書編集フォーム | S13 |
| `POST` | `/invoices/{id}` | 請求書更新 | — |
| `POST` | `/invoices/{id}/status` | ステータス変更 | — |
| `GET` | `/invoices/{id}/pdf` | 請求書PDF表示 | S14 |

> 請求書は見積書からの変換のみで作成する。手動作成（`POST /invoices`）は MVP 対象外。

### GET /invoices（請求書一覧）

**クエリパラメータ**

| パラメータ | デフォルト | 備考 |
|-----------|-----------|------|
| `status` | （全件） | `draft` / `sent` / `paid` / `overdue` でフィルタ |

### POST /invoices/{id}（請求書更新）

**フォームフィールド**

| フィールド | 必須 | 備考 |
|-----------|------|------|
| `title` | ✓ | |
| `issue_date` | ✓ | YYYY-MM-DD |
| `due_date` | | YYYY-MM-DD |
| `notes` | | |

**制約**
- `draft` 状態のみ更新可。それ以外は `403`

**レスポンス**
- 成功 → `303` `/invoices/{id}`

### POST /invoices/{id}/status（ステータス変更）

**フォームフィールド**

| フィールド | 値 | 意味 |
|-----------|-----|------|
| `action` | `send` | `draft` → `sent`（明細行1件以上が条件） |
| `action` | `pay` | `sent` → `paid` または `overdue` → `paid` |
| `action` | `overdue` | `sent` → `overdue` |

**レスポンス**
- 成功 → `303` `/invoices/{id}`
- 不正遷移 → `400`
- 明細行なしで `send` → `400`

---

## 請求書明細行

| メソッド | パス | 概要 |
|---------|------|------|
| `POST` | `/invoices/{id}/items` | 明細行追加 |
| `POST` | `/invoices/{id}/items/{item_id}` | 明細行更新 |
| `POST` | `/invoices/{id}/items/{item_id}/delete` | 明細行削除 |

フォームフィールド・自動計算ルールは見積書明細行と同一。

**制約**
- 請求書が `draft` 状態のみ操作可。それ以外は `403`

**レスポンス（全操作共通）**
- 成功 → `303` `/invoices/{id}/edit`

---

## PDF

| メソッド | パス | 概要 |
|---------|------|------|
| `GET` | `/quotes/{id}/pdf` | 見積書PDF（ブラウザ表示） |
| `GET` | `/invoices/{id}/pdf` | 請求書PDF（ブラウザ表示） |

**レスポンス**
- `Content-Type: application/pdf`
- `Content-Disposition: inline; filename="EST-YYYY-NNN.pdf"` / `INV-YYYY-NNN.pdf`

---

## エラーコード一覧

| コード | 意味 | 主なケース |
|-------|------|-----------|
| `400` | Bad Request | 不正ステータス遷移、明細行なしで送付、関連データあり顧客削除 |
| `403` | Forbidden | 変更不可ステータスへの編集・削除操作 |
| `404` | Not Found | 存在しないリソース |
