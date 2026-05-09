# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

**見積書→請求書変換管理ツール**（個人・小規模事業者向けSaaS・MVP）

- 見積書を作成し、承認後ワンクリックで請求書に変換する
- ステータス管理（見積：draft/sent/accepted/rejected/converted、請求：draft/sent/paid/overdue）
- PDF出力（見積書・請求書）
- 決済機能はMVP対象外（後フェーズでStripe追加予定）

---

## 技術スタック

| 層 | 採用技術 |
|----|---------|
| Web framework | FastAPI |
| テンプレート | Jinja2 |
| ORM | SQLAlchemy 2.x（非同期なし、同期セッション） |
| DB | SQLite（`data/app.db`） |
| PDF生成 | WeasyPrint |
| 認証 | Starlette セッション（`itsdangerous`） |
| スタイル | Tailwind CSS（CDN、ビルドステップなし） |
| Python | 3.12+ |

---

## ディレクトリ構成

```
Business/
├── CLAUDE.md
├── docs/                    # 設計書
└── mitumori-app/            # アプリ本体
    ├── main.py              # FastAPI app, router登録, DB初期化
    ├── models.py            # SQLAlchemy モデル定義
    ├── database.py          # engine, SessionLocal, get_db依存
    ├── routes/
    │   ├── quotes.py        # 見積書CRUD
    │   ├── invoices.py      # 請求書CRUD
    │   └── customers.py     # 顧客管理
    ├── services/
    │   ├── conversion.py    # 見積→請求書変換ロジック
    │   ├── numbering.py     # 採番ロジック
    │   └── pdf.py           # PDF生成
    ├── templates/           # Jinja2 HTMLテンプレート
    ├── static/              # CSS・JS（最小限）
    ├── data/                # SQLiteファイル（.gitignore対象）
    ├── .env                 # 環境変数（.gitignore対象）
    └── requirements.txt
```

---

## データモデル

```
Customer       1──* Quote         1──* LineItem
                       │
                       └──(converted)──* Invoice  1──* LineItem
```

- `Quote` と `Invoice` はそれぞれ独立した `LineItem` を持つ（変換時にコピー）
- `Invoice.quote_id` で変換元を追跡

---

## 作業ルール

**DBアクセス**
- `get_db` 依存（`with SessionLocal() as db`）を必ず使う。スコープ外でセッションを持ち越さない
- `db.commit()` はルートハンドラ側でなくサービス関数内で完結させる

**見積→請求書変換**
- `services/conversion.py` の `convert_quote_to_invoice()` のみが変換を担当する
- 変換後は `Quote.status = "converted"` にセットし、再変換を防ぐ

**PDF生成**
- ルートハンドラからPDF生成を直接呼ばない。`services/pdf.py` 経由のみ
- テンプレートは `templates/pdf/` に分離する

**ステータス遷移**
- 不正なステータス遷移は `400 Bad Request` を返す。サイレントに無視しない
- 遷移ルールは各サービス関数の先頭にコメントで明示する

**フロントエンド**
- Tailwind はCDN版のみ。ビルドステップを追加しない
- インタラクティブな要素はvanilla JSで書く。jQueryは使わない

---

## 禁止事項

- **生SQLを書かない**（SQLAlchemy ORM のみ）
- **グローバル変数にDBセッションを持たせない**
- **ルートハンドラにビジネスロジックを書かない**（サービス層に委譲）
- **`data/` ディレクトリをコミットしない**（`.gitignore` 対象）
- **MVP段階でStripe・メール送信・マルチテナントを実装しない**

---

## 開発コマンド

```bash
cd mitumori-app

# 仮想環境
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 起動
uvicorn main:app --reload

# DB初期化（初回 or モデル変更後）
python -c "from database import Base, engine; Base.metadata.create_all(engine)"
```

---

## 参照すべき設計書

| ドキュメント | 場所 | 内容 |
|------------|------|------|
| 画面フロー図 | `docs/screen-flow.md` | 画面遷移・ステータス遷移の正規定義 |
| APIエンドポイント一覧 | `docs/api.md` | ルートごとのリクエスト/レスポンス仕様 |
| データモデル詳細 | `docs/schema.md` | 各テーブルのカラム定義・制約 |

> `docs/` は実装前に作成すること。設計書なしで実装を始めない。
