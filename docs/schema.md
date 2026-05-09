# データモデル設計書

## ビジネスルール前提

| 項目 | 決定事項 |
|------|---------|
| 消費税 | 税別表示・固定10%・行ごとでなく合計に対して課税 |
| 端数処理 | 消費税額は**切り捨て**（`floor`） |
| 金額単位 | すべて**円・整数**で保存（小数なし） |
| 見積書番号 | `EST-YYYY-NNN`（例：EST-2026-001）年ごとにリセット |
| 請求書番号 | `INV-YYYY-NNN`（例：INV-2026-001）年ごとにリセット |
| 有効期限 | 見積書のみ・任意入力・期限到達による自動ステータス変更なし |

---

## テーブル定義

### `customers`（顧客）

| カラム | 型 | 制約 | 備考 |
|--------|----|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | |
| `company_name` | TEXT | NOT NULL | 会社名・屋号 |
| `contact_name` | TEXT | NOT NULL | 担当者名 |
| `email` | TEXT | NOT NULL | |
| `phone` | TEXT | | 任意 |
| `address` | TEXT | | 任意・改行含む |
| `notes` | TEXT | | 社内メモ |
| `created_at` | DATETIME | NOT NULL, DEFAULT now | |
| `updated_at` | DATETIME | NOT NULL, DEFAULT now | |

---

### `quotes`（見積書）

| カラム | 型 | 制約 | 備考 |
|--------|----|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | |
| `quote_number` | TEXT | NOT NULL, UNIQUE | `EST-YYYY-NNN` |
| `customer_id` | INTEGER | FK→customers, NOT NULL | |
| `status` | TEXT | NOT NULL, DEFAULT `draft` | `draft` / `sent` / `accepted` / `rejected` / `converted` |
| `title` | TEXT | NOT NULL | 件名（例：「Webサイト制作のご提案」） |
| `issue_date` | DATE | NOT NULL | 発行日 |
| `valid_until` | DATE | | 有効期限（任意） |
| `notes` | TEXT | | 備考・振込先など |
| `subtotal` | INTEGER | NOT NULL, DEFAULT 0 | 税抜合計 |
| `tax_amount` | INTEGER | NOT NULL, DEFAULT 0 | 消費税額（切り捨て） |
| `total` | INTEGER | NOT NULL, DEFAULT 0 | 税込合計 |
| `created_at` | DATETIME | NOT NULL, DEFAULT now | |
| `updated_at` | DATETIME | NOT NULL, DEFAULT now | |

---

### `invoices`（請求書）

| カラム | 型 | 制約 | 備考 |
|--------|----|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | |
| `invoice_number` | TEXT | NOT NULL, UNIQUE | `INV-YYYY-NNN` |
| `quote_id` | INTEGER | FK→quotes | 変換元（手動作成時は NULL） |
| `customer_id` | INTEGER | FK→customers, NOT NULL | |
| `status` | TEXT | NOT NULL, DEFAULT `draft` | `draft` / `sent` / `paid` / `overdue` |
| `title` | TEXT | NOT NULL | 件名 |
| `issue_date` | DATE | NOT NULL | 発行日 |
| `due_date` | DATE | | 支払期限（任意） |
| `notes` | TEXT | | 備考・振込先など |
| `subtotal` | INTEGER | NOT NULL, DEFAULT 0 | 税抜合計 |
| `tax_amount` | INTEGER | NOT NULL, DEFAULT 0 | 消費税額（切り捨て） |
| `total` | INTEGER | NOT NULL, DEFAULT 0 | 税込合計 |
| `created_at` | DATETIME | NOT NULL, DEFAULT now | |
| `updated_at` | DATETIME | NOT NULL, DEFAULT now | |

---

### `line_items`（明細行）

| カラム | 型 | 制約 | 備考 |
|--------|----|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | |
| `quote_id` | INTEGER | FK→quotes | `quote_id` か `invoice_id` の一方のみ設定 |
| `invoice_id` | INTEGER | FK→invoices | 同上 |
| `sort_order` | INTEGER | NOT NULL | 表示順（1始まり） |
| `description` | TEXT | NOT NULL | 品目名 |
| `quantity` | REAL | NOT NULL | 数量（0.5など小数許容） |
| `unit` | TEXT | | 単位（式・個・時間 etc.） |
| `unit_price` | INTEGER | NOT NULL | 単価（円） |
| `amount` | INTEGER | NOT NULL | 小計 = `floor(quantity × unit_price)` |

**制約：** `quote_id` と `invoice_id` はどちらか一方のみ NOT NULL（アプリ層で保証）

---

## ER図

```
customers
  │
  ├──< quotes ──< line_items
  │       │
  │       └──< invoices ──< line_items
  │
  └──< invoices（手動作成時のみ直接紐付け）
```

---

## 採番ロジック

```python
# services/numbering.py
def next_quote_number(db, year: int) -> str:
    prefix = f"EST-{year}-"
    count = db.query(Quote).filter(Quote.quote_number.like(f"{prefix}%")).count()
    return f"{prefix}{count + 1:03d}"

def next_invoice_number(db, year: int) -> str:
    prefix = f"INV-{year}-"
    count = db.query(Invoice).filter(Invoice.invoice_number.like(f"{prefix}%")).count()
    return f"{prefix}{count + 1:03d}"
```

> MVPは単一ユーザー前提のためレースコンディション対策は不要。

---

## 金額計算ルール

```python
# 明細行の小計
amount = math.floor(quantity * unit_price)

# 見積書・請求書の合計
subtotal   = sum(item.amount for item in line_items)
tax_amount = math.floor(subtotal * 0.10)
total      = subtotal + tax_amount
```

**合計の更新タイミング：** 明細行の追加・編集・削除のたびに `quotes` / `invoices` の集計カラムを再計算して保存する。

---

## インデックス

```sql
CREATE INDEX ix_quotes_customer_id   ON quotes(customer_id);
CREATE INDEX ix_quotes_status        ON quotes(status);
CREATE INDEX ix_invoices_customer_id ON invoices(customer_id);
CREATE INDEX ix_invoices_quote_id    ON invoices(quote_id);
CREATE INDEX ix_invoices_status      ON invoices(status);
CREATE INDEX ix_line_items_quote_id  ON line_items(quote_id);
CREATE INDEX ix_line_items_invoice_id ON line_items(invoice_id);
```
