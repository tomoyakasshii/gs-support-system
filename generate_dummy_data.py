import random
import uuid
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker

# 日本語向けのFakerを設定
fake = Faker('ja_JP')

def generate_gs_yokohama_dummy_data(num_records=5000):
    data = []
    
    # ガソリンスタンド特化型のデータ選択肢
    purposes = ["給油", "タイヤ相談", "オイル交換", "車検見積", "洗車", "その他"]
    customer_types = ["一般", "常連", "業者", "新規"]
    genders = ["男性", "女性", "不明"]
    
    # リアルな車両・タイヤの組み合わせデータ
    car_templates = [
        {"maker": "トヨタ", "model": "VOXY", "size": "LL", "tire": "195/65R15"},
        {"maker": "トヨタ", "model": "プリウス", "size": "M", "tire": "195/65R15"},
        {"maker": "トヨタ", "model": "ハイエース", "size": "XL", "tire": "195/80R15"},
        {"maker": "ホンダ", "model": "N-BOX", "size": "S", "tire": "155/65R14"},
        {"maker": "日産", "model": "セレナ", "size": "L", "tire": "195/65R16"},
        {"maker": "マツダ", "model": "CX-5", "size": "L", "tire": "225/65R17"},
        {"maker": "ダイハツ", "model": "タント", "size": "S", "tire": "155/65R14"},
        {"maker": "BMW", "model": "ミニクーパー", "size": "S", "tire": "175/65R15"}
    ]
    
    # 匿名化された正しいスタッフ名のリスト
    staff_list = ["所長", "ベテラン社員", "主任リーダー", "派遣社員", "社員A", "ベテランPA", "PA1", "PA2", "未選択"]
    
    # 基準となる開始日（例: 2024年1月1日）
    start_date = datetime(2024, 1, 1)
    
    print(f"🚀 地名を「横浜」に固定して {num_records}件の顧客データを生成中...")
    
    for i in range(num_records):
        # 1. 日時のランダム生成
        random_days = random.randint(0, 800)  # 約2年分の幅
        random_hours = random.randint(7, 21)  # 営業時間内
        random_minutes = random.randint(0, 59)
        date_obj = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
        date_str = date_obj.strftime("%Y/%m/%d(%a) %H:%M")
        
        # 2. 車両・タイヤ情報のランダム選択
        car = random.choice(car_templates)
        
        # 3. ナンバープレートの生成（地名は「横浜」に完全固定！）
        plate_place = "横浜"
        plate_class = random.choice(["300", "500", "580", "330"])
        plate_kana = random.choice(["さ", "き", "る", "ま", "れ"])
        plate_num = f"{random.randint(1, 9999):04d}"
        
        # 4. レコードの組み立て
        record = {
            "日時": date_str,
            "来店目的": random.choice(purposes),
            "種別": random.choice(customer_types),
            "ナンバー地名": plate_place,
            "ナンバー3桁": plate_class,
            "ナンバーかな": plate_kana,
            "ナンバー下4桁": plate_num,
            "メーカー": car["maker"],
            "車種": car["model"],
            "サイズ": car["size"],
            "カラー": random.choice(["ホワイト", "ブラック", "シルバー", "ブルー", "レッド"]),
            "年齢": random.choice(["20代", "30代", "40代", "50代", "60代以上", "不明"]),
            "性別": random.choice(genders),
            "タイヤサイズ": car["tire"],
            "製造年": str(random.randint(2021, 2025)),
            "タイヤメーカー": random.choice(["ブリヂストン", "ヨコハマ", "ダンロップ", "トーヨー", "未選択"]),
            "タイヤ商品名": random.choice(["REGNO", "Ecopia", "BluEarth", "Enasave", "未選択"]),
            "車検日": (date_obj + timedelta(days=random.randint(30, 730))).strftime("%Y/%m/%d"),
            "天気": random.choice(["晴れ", "曇り", "雨", "雪"]),
            "担当者": random.choice(staff_list),
            "空気圧点検": random.choice(["実施", "未実施"]),
            "備考": fake.sentence() if random.random() > 0.5 else ""
        }
        data.append(record)
    
    # DataFrameに変換して日付順にソート
    df = pd.DataFrame(data)
    df['sort_date'] = pd.to_datetime(df['日時'].str.slice(0, 10))
    df = df.sort_values(by='sort_date', ascending=False).drop(columns=['sort_date'])
    
    # CSVとして保存
    output_file = "gs_historical_data.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✨ 生成完了！ファイル名: {output_file} ({len(df)} 件)")

def generate_schedule_dummy_data():
    """schedule.csv をリアルなGS予約データで上書き生成する"""
    random.seed(42)

    # 日付範囲: 2026/05/10 ～ 2026/06/15
    start_dt  = datetime(2026, 5, 10)
    date_span = (datetime(2026, 6, 15) - start_dt).days   # 36日

    # 営業時間内の時刻選択肢
    time_slots = [
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "13:00", "13:30", "14:00", "15:00", "15:30", "16:00", "17:00",
    ]

    # 作業種別マスタ: title / detail候補 / 標準工数(分) / ピット使用
    job_templates = [
        {
            "title":    "タイヤ交換",
            "details":  ["4本交換 195/65R15", "4本交換 225/50R17",
                         "持ち込みスタッドレス脱着", "2本交換 155/65R14"],
            "duration": (50, 90), "pit": 1,
        },
        {
            "title":    "タイヤ交換（4本）",
            "details":  ["195/65R15 REGNO GR-XIII", "195/65R15 BluEarth ES32",
                         "スタッドレス BLIZZAK VRX3 4本", "持ち込みホイール付き4本"],
            "duration": (60, 100), "pit": 1,
        },
        {
            "title":    "車検",
            "details":  ["2年車検 整備込み", "継続車検 法定点検込み",
                         "新規登録車検"],
            "duration": (60, 90), "pit": 1,
        },
        {
            "title":    "車検見積もり",
            "details":  ["2年車検 概算見積", "車検見積もり", "法定費用確認"],
            "duration": (30, 50), "pit": 0,
        },
        {
            "title":    "オイル交換",
            "details":  ["5W-30 4L", "0W-20 4L エレメント同時交換",
                         "エレメント交換セット", "5W-30 4.5L"],
            "duration": (20, 30), "pit": 1,
        },
        {
            "title":    "手洗い洗車",
            "details":  ["撥水コート洗車 プリウスクラス",
                         "手洗い洗車 ミニバンクラス",
                         "撥水コート洗車 軽クラス"],
            "duration": (30, 45), "pit": 0,
        },
        {
            "title":    "バッテリー交換",
            "details":  ["N-65B24L交換 充電確認込み",
                         "標準バッテリー交換"],
            "duration": (20, 30), "pit": 0,
        },
    ]

    staff_list  = ["所長", "ベテラン社員", "主任リーダー", "派遣社員",
                   "社員A", "作業専門PA", "接客専門PA", "学生PA", ""]
    cust_types  = ["一般", "一般", "一般", "常連", "常連", "業者", "新規"]
    loaner_cars = ["マーチ", "ティーダ", "サクシードバン"]
    statuses    = ["予定", "予定", "予定", "完了", "完了"]

    records = []
    n = random.randint(25, 30)

    for _ in range(n):
        dt       = start_dt + timedelta(days=random.randint(0, date_span))
        job      = random.choice(job_templates)
        status   = random.choice(statuses)
        want_lnr = random.choice([0, 0, 0, 1])   # 貸出車は少なめ

        records.append({
            "id":             str(uuid.uuid4()),
            "date":           dt.strftime("%Y/%m/%d"),
            "time":           random.choice(time_slots),
            "title":          job["title"],
            "detail":         random.choice(job["details"]),
            "status":         status,
            "plate_num":      f"{random.randint(1, 9999):04d}",
            "cust_type":      random.choice(cust_types),
            "sb_duration":    random.randint(job["duration"][0], job["duration"][1]),
            "sb_use_pit":     job["pit"],
            "sb_want_loaner": want_lnr,
            "cust_name":      "",
            "cust_contact":   "",
            "cust_car":       "",
            "loaner_car":     random.choice(loaner_cars) if want_lnr else "",
            "sb_staff":       random.choice(staff_list),
        })

    df = (pd.DataFrame(records)
            .sort_values(["date", "time"])
            .reset_index(drop=True))

    df.to_csv("schedule.csv", index=False, encoding="utf-8")
    print(f"📅 schedule.csv 生成完了（{len(df)} 件） → テストデータをクレンジング済み")


def generate_change_log_dummy_data():
    """change_log.csv をリアルな業務操作ログで上書き生成する"""
    random.seed(99)

    # timestamp 範囲: 2026-05-20 ～ 2026-06-02
    log_start   = datetime(2026, 5, 20, 8, 0, 0)
    log_end     = datetime(2026, 6, 2, 23, 59, 59)
    ts_span_sec = int((log_end - log_start).total_seconds())

    # 操作対象レコードの date/time
    rec_start  = datetime(2026, 5, 10)
    rec_span   = 36
    time_slots = [
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "13:00", "13:30", "14:00", "15:00", "15:30", "16:00", "17:00",
    ]

    # action ごとの memo テンプレート
    memo_map = {
        "新規登録": [
            "195/65R15 商品A: REGNO GR-XIII / 商品B: ECOPIA EP300 を新規登録",
            "タイヤ交換（4本）195/65R15 BLIZZAK VRX3 予約を新規作成",
            "オイル交換 5W-30 4L 予約を新規登録",
            "手洗い洗車 撥水コート洗車 プリウスクラス を新規登録",
            "車検見積もり 予約を新規作成",
            "バッテリー交換 N-65B24L 予約を新規登録",
            "2年車検 整備込み の予約を新規作成",
            "エレメント交換セット 予約を新規登録",
        ],
        "更新": [
            "担当：ベテラン社員 へ変更",
            "担当：主任リーダー へ変更",
            "手洗い洗車 プリウスクラス 予約枠の時間を変更",
            "キャラバン タイヤ交換 FBC のステータスを更新",
            "ステータスを「完了」に更新",
            "タイヤサイズを 195/65R15 に修正",
            "所要時間を 60 分に変更",
            "担当：所長 へ変更",
            "商品名を ECOPIA EP300 に修正",
            "お客様名・連絡先を追記",
        ],
        "削除": [
            "キャンセルに伴う予約削除",
            "お客様都合によりキャンセル・削除",
            "重複登録のため削除",
            "日程未確定のためいったん削除",
        ],
        "復元": [
            "誤削除分を復元",
            "担当：主任リーダー の予約を復元",
            "キャンセル取り消し・予約を復元",
        ],
    }

    # 出現頻度（新規:更新:削除:復元 ≈ 6:9:3:2）
    actions_pool = (
        ["新規登録"] * 6 + ["更新"] * 9 + ["削除"] * 3 + ["復元"] * 2
    )

    n = random.randint(15, 20)

    # timestamp を n 個生成し時系列でソート
    timestamps = sorted(
        log_start + timedelta(seconds=random.randint(0, ts_span_sec))
        for _ in range(n)
    )

    records = []
    for ts in timestamps:
        action = random.choice(actions_pool)
        rec_dt = rec_start + timedelta(days=random.randint(0, rec_span))
        records.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "action":    action,
            "date":      rec_dt.strftime("%Y/%m/%d"),
            "time":      random.choice(time_slots),
            "memo":      random.choice(memo_map[action]),
        })

    df = pd.DataFrame(records)
    df.to_csv("change_log.csv", index=False, encoding="utf-8")
    print(f"📝 change_log.csv 生成完了（{len(df)} 件） → テストデータをクレンジング済み")


if __name__ == "__main__":
    # とりあえず5000件で生成。1万件にしたければここを10000に変えてOK！
    generate_gs_yokohama_dummy_data(5000)
    generate_schedule_dummy_data()
    generate_change_log_dummy_data()