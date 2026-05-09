import math
from datetime import date, timedelta
from database import Base, engine, SessionLocal
from models import Customer, Invoice, Quote, LineItem
from services.conversion import convert_quote_to_invoice
from services.numbering import next_invoice_number

Base.metadata.create_all(engine)

CUSTOMERS = [
    ("株式会社アクシア", "田中 誠", "tanaka@axia.co.jp", "03-1234-5678", "東京都千代田区丸の内1-1-1"),
    ("合同会社ブルームテック", "佐藤 花子", "sato@bloomtech.jp", "06-2345-6789", "大阪府大阪市北区梅田2-3-4"),
    ("株式会社クリエイトワン", "鈴木 太郎", "suzuki@createone.co.jp", "052-345-6789", "愛知県名古屋市中村区名駅3-5-7"),
    ("有限会社デジタルフロンティア", "高橋 優", "takahashi@dfrontier.jp", "011-456-7890", "北海道札幌市中央区大通西4-1"),
    ("株式会社エコソリューションズ", "渡辺 恵", "watanabe@ecosol.co.jp", "092-567-8901", "福岡県福岡市博多区博多駅前1-2-3"),
    ("フューチャービジョン株式会社", "伊藤 健司", "ito@futurevision.jp", "075-678-9012", "京都府京都市中京区烏丸通四条上る"),
    ("株式会社グローバルネット", "山田 彩", "yamada@globalnet.co.jp", "045-789-0123", "神奈川県横浜市西区みなとみらい2-2-1"),
    ("合同会社ハーモニー工房", "中村 拓也", "nakamura@harmony-kobo.jp", "022-890-1234", "宮城県仙台市青葉区一番町3-7-9"),
    ("株式会社インサイトパートナーズ", "小林 美穂", "kobayashi@insight-p.co.jp", "082-901-2345", "広島県広島市中区基町6-78"),
    ("ジャパンクラフト株式会社", "加藤 龍", "kato@japancraft.jp", "076-012-3456", "石川県金沢市香林坊1-1-1"),
]

QUOTES = [
    # (customer_idx, title, status, items, issue_date_offset_days)
    # status="converted" は見積書作成後に変換サービスを通じて請求書も生成する
    (0, "Webサイト制作のご提案", "sent",
     [("要件定義・設計", 1, "式", 150000), ("デザイン制作", 1, "式", 200000), ("コーディング", 1, "式", 250000)],
     -30),
    (0, "SEOコンサルティング契約", "draft",
     [("月次SEO分析レポート", 3, "ヶ月", 80000), ("キーワード戦略策定", 1, "式", 50000)],
     -5),
    (1, "基幹システム開発", "accepted",
     [("要件定義", 2, "人月", 600000), ("開発・実装", 5, "人月", 1500000), ("テスト・品質保証", 1, "人月", 300000), ("導入支援", 0.5, "人月", 150000)],
     -45),
    (1, "社内研修プログラム設計", "converted",
     [("カリキュラム設計", 1, "式", 120000), ("研修資料作成", 1, "式", 80000), ("講師費用", 2, "日", 60000)],
     -60),
    (2, "ECサイトリニューアル", "sent",
     [("現状分析・UX設計", 1, "式", 180000), ("デザイン刷新", 1, "式", 220000), ("フロントエンド実装", 1, "式", 300000), ("バックエンド改修", 1, "式", 250000)],
     -20),
    (2, "ロゴ・ブランドデザイン", "rejected",
     [("ブランドリサーチ", 1, "式", 50000), ("ロゴデザイン（3案）", 1, "式", 150000), ("ブランドガイドライン作成", 1, "式", 80000)],
     -40),
    (3, "クラウド移行支援", "accepted",
     [("現行インフラ調査", 1, "式", 100000), ("移行計画策定", 1, "式", 150000), ("移行作業", 2, "人月", 600000), ("運用設計", 1, "式", 120000)],
     -15),
    (3, "セキュリティ監査", "draft",
     [("脆弱性診断", 1, "式", 200000), ("ペネトレーションテスト", 1, "式", 300000), ("改善レポート作成", 1, "式", 80000)],
     -3),
    (4, "採用サイト制作", "sent",
     [("サイト設計・ワイヤーフレーム", 1, "式", 80000), ("デザイン制作", 1, "式", 150000), ("CMS導入", 1, "式", 100000)],
     -25),
    (4, "動画制作・編集", "draft",
     [("企画・脚本", 1, "式", 100000), ("撮影", 2, "日", 80000), ("編集・MA", 1, "式", 120000)],
     -8),
    (5, "スマートフォンアプリ開発", "sent",
     [("要件定義・設計", 1, "式", 200000), ("iOS開発", 3, "人月", 900000), ("Android開発", 3, "人月", 900000), ("QAテスト", 1, "人月", 300000)],
     -35),
    (5, "データ分析ダッシュボード構築", "accepted",
     [("データ設計", 1, "式", 150000), ("BIツール導入・設定", 1, "式", 200000), ("ダッシュボード開発", 2, "人月", 600000)],
     -50),
    (6, "マーケティング戦略策定", "converted",
     [("市場調査・競合分析", 1, "式", 200000), ("戦略立案", 1, "式", 150000), ("実行計画作成", 1, "式", 100000)],
     -70),
    (6, "コーポレートサイト保守", "sent",
     [("月次定期メンテナンス", 6, "ヶ月", 30000), ("コンテンツ更新作業", 6, "ヶ月", 15000)],
     -10),
    (7, "社内ポータルサイト構築", "draft",
     [("要件整理・設計", 1, "式", 120000), ("SharePoint設定", 1, "式", 180000), ("コンテンツ移行", 1, "式", 80000)],
     -2),
    (7, "ITインフラ設計・構築", "accepted",
     [("現状調査・要件定義", 1, "式", 150000), ("ネットワーク設計", 1, "式", 200000), ("機器調達・設定", 1, "式", 350000), ("テスト・納品", 1, "式", 100000)],
     -55),
    (8, "人事システム導入支援", "sent",
     [("システム選定支援", 1, "式", 100000), ("導入設定", 1, "式", 200000), ("データ移行", 1, "式", 150000), ("操作研修", 2, "日", 60000)],
     -18),
    (8, "Webマーケティング支援", "draft",
     [("広告運用（Google/Meta）", 3, "ヶ月", 50000), ("LP制作", 1, "式", 200000), ("月次レポート作成", 3, "ヶ月", 30000)],
     -7),
    (9, "製品カタログ制作", "sent",
     [("撮影ディレクション", 1, "日", 80000), ("デザイン制作（A4 16P）", 1, "式", 200000), ("印刷管理", 1, "式", 50000)],
     -22),
    (9, "業務フロー改善コンサルティング", "accepted",
     [("現状ヒアリング・分析", 1, "式", 150000), ("改善案策定", 1, "式", 200000), ("実施支援", 2, "人月", 600000)],
     -42),
]


def recalc(items):
    subtotal = sum(math.floor(qty * price) for _, qty, _, price in items)
    tax = math.floor(subtotal * 0.10)
    return subtotal, tax, subtotal + tax


with SessionLocal() as db:
    # 既存データをクリア
    db.query(LineItem).delete()
    db.query(Invoice).delete()
    db.query(Quote).delete()
    db.query(Customer).delete()
    db.commit()

    today = date.today()
    year = today.year

    customers = []
    for company, contact, email, phone, address in CUSTOMERS:
        c = Customer(
            company_name=company,
            contact_name=contact,
            email=email,
            phone=phone,
            address=address,
        )
        db.add(c)
        customers.append(c)
    db.flush()

    quotes = []
    for i, (cust_idx, title, target_status, items, offset) in enumerate(QUOTES, start=1):
        issue = today + timedelta(days=offset)
        valid = issue + timedelta(days=30)
        subtotal, tax, total = recalc(items)
        # converted は一度 accepted で作り、後で変換する
        initial_status = "accepted" if target_status == "converted" else target_status
        q = Quote(
            quote_number=f"EST-{year}-{i:03d}",
            customer_id=customers[cust_idx].id,
            status=initial_status,
            title=title,
            issue_date=issue,
            valid_until=valid,
            notes="ご不明な点がございましたらお気軽にお問い合わせください。",
            subtotal=subtotal,
            tax_amount=tax,
            total=total,
        )
        db.add(q)
        db.flush()
        for order, (desc, qty, unit, unit_price) in enumerate(items, start=1):
            db.add(LineItem(
                quote_id=q.id,
                sort_order=order,
                description=desc,
                quantity=qty,
                unit=unit,
                unit_price=unit_price,
                amount=math.floor(qty * unit_price),
            ))
        db.flush()
        quotes.append((q, target_status))

    db.commit()

    # converted 扱いの見積書を変換サービス経由で請求書に変換する
    for q, target_status in quotes:
        if target_status == "converted":
            db.refresh(q)
            inv = convert_quote_to_invoice(db, q)
            # 支払期限を発行日+30日に設定
            inv.due_date = q.issue_date + timedelta(days=30)
            inv.status = "sent"
            db.commit()

    invoice_count = db.query(Invoice).count()
    print(f"テストデータを作成しました：顧客10件、見積書20件、請求書{invoice_count}件")
