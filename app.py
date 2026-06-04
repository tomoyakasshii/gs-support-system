import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import re
import uuid
import json
import os
import subprocess
import streamlit.components.v1 as components

BASE_DIR        = Path(__file__).parent
HISTORY_CSV     = BASE_DIR / "history.csv"
SCHEDULE_CSV    = BASE_DIR / "schedule.csv"
CHANGE_LOG_CSV  = BASE_DIR / "change_log.csv"

# ── マスターデータ ─────────────────────────────────────────────────────────────
PURPOSE_OPTIONS   = ["給油","燃料券","洗車","オイル交換","バッテリー交換","タイヤ見積","タイヤ交換","車検見積","車検","空気圧点検","電気","その他"]
CUST_TYPE_OPTIONS = ["なし","一般","業者","常連"]
PLATE_AREAS = [
    "(未選択)","札幌","函館","旭川","釧路","帯広","北見","室蘭","苫小牧",
    "青森","八戸","盛岡","仙台","秋田","山形","福島","郡山","いわき",
    "水戸","土浦","宇都宮","那須","高崎","熊谷","大宮","川越","春日部","所沢","越谷","川口",
    "習志野","千葉","柏","市川","成田","袖ヶ浦",
    "品川","足立","練馬","多摩","八王子","相模","横浜","川崎","湘南","横須賀","平塚",
    "新潟","長岡","富山","石川","福井","長野","松本","諏訪",
    "静岡","浜松","沼津","富士山",
    "名古屋","岡崎","豊田","春日井","三河","一宮","岐阜","三重","四日市",
    "滋賀","京都","大阪","なにわ","和泉","堺","神戸","姫路","尼崎","奈良","和歌山",
    "鳥取","島根","岡山","広島","福山","山口",
    "徳島","香川","愛媛","高知",
    "福岡","北九州","久留米","佐賀","長崎","熊本","大分","宮崎","鹿児島","沖縄",
]
MAKER_OPTIONS      = ["(未選択)","トヨタ","レクサス","ホンダ","日産","マツダ","スバル","スズキ","ダイハツ","三菱","メルセデス","BMW","アウディ","VW","ボルボ","ジャガー","ランドローバー","その他"]
COLOR_OPTIONS      = ["(未選択)","ホワイト","パールホワイト","シルバー","ガンメタ","ブラック","グレー","ネイビー","ブルー","レッド","ピンク","グリーン","ゴールド","ブラウン","ベージュ","オレンジ","その他"]
AGE_OPTIONS        = ["(未選択)","10代","20代","30代","40代","50代","60代","70代","80代以上"]
GENDER_OPTIONS     = ["無記名","男","女"]
TIRE_MAKER_OPTIONS = ["(未選択)","ブリヂストン","ヨコハマ","ダンロップ","トーヨー","住友(ファルケン)","ミシュラン","コンチネンタル","ピレリ","グッドイヤー","ハンコック","ネクセン","その他"]
TIRE_YEAR_OPTIONS  = ["","26","25","24","23","22","21","20","19","18","17","16","15","14","13","12","11","10","09","08","07","06","05","04","03","02","01","00"]
KANA_OPTIONS       = ["(未選択)"] + list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん")

# ── タイヤ商品名→メーカー 自動推定マップ ────────────────────────────────────
TIRE_PRODUCT_MAKER_MAP: dict[str, list[str]] = {
    "ブリヂストン": [
        "REGNO","レグノ","ECOPIA","エコピア","NEXTRY","ネクストリー",
        "POTENZA","ポテンザ","ALENZA","アレンザ","BLIZZAK","ブリザック",
        "VRX","ブイアールエックス","TURANZA","トランザ","DUELER","デューラー",
        "PLAYZ","プレイズ","SEIBERLING","セイバーリング","NEWNO","ニューノ",
    ],
    "ヨコハマ": [
        "BluEarth","ブルーアース","ADVAN","アドバン","GEOLANDAR","ジオランダー",
        "iG70","iG60","iG50","iG30","IG70","IG60","IG50","IG30","ECOS","エコス",
        "ice GUARD","アイスガード","PARADA","パラダ","SUPERVAN","ENVIGOR",
    ],
    "ダンロップ": [
        "ENASAVE","エナセーブ","LE MANS","ルマン","LMFIVE","LM5","VEURO",
        "DIREZZA","ディレッツァ","GRANDTREK","グランドトレック","グラントレック",
        "WINTER MAXX","ウィンターマックス","SP SPORT","SPORT MAXX",
    ],
    "トーヨー": [
        "PROXES","プロクセス","TRANPATH","トランパス","NANOENERGY","ナノエナジー",
        "OPEN COUNTRY","オープンカントリー","OBSERVE","オブザーブ",
        "CELSIUS","GARIT","ガリット","SD-7",
    ],
    "住友(ファルケン)": [
        "ZIEX","ジーテックス","SINCERA","シンセラ","AZENIS","アゼニス",
        "ESPIA","エスピア","SL201","SL501","SL201H",
    ],
    "ミシュラン": [
        "PRIMACY","プライマシー","PILOT","パイロット","CROSSCLIMATE","クロスクライメート",
        "LATITUDE","ラティチュード","X-ICE","エックスアイス","DEFENDER","AGILIS","ENERGY",
    ],
    "コンチネンタル": [
        "PremiumContact","プレミアムコンタクト","SportContact","スポーツコンタクト",
        "EcoContact","エココンタクト","ContiSeal","CrossContact","WinterContact","NorthContact",
    ],
    "ピレリ": [
        "P ZERO","PZERO","ピーゼロ","CINTURATO","チントゥラート",
        "SCORPION","スコーピオン","SOTTOZERO","CARRIER","DRAGON",
    ],
    "グッドイヤー": [
        "Eagle","イーグル","EfficientGrip","エフィシェントグリップ",
        "VEC","VECTOR","Assurance","アシュアランス","UltraGrip","ウルトラグリップ",
    ],
    "ハンコック": [
        "Kinergy","キナジー","Ventus","ベンタス","Dynapro","ダイナプロ",
        "iCept","Winter i","OPTIMO","オプティモ",
    ],
    "ネクセン": [
        "N'FERA","NFERA","エヌフェラ","ROADIAN","ロードアン","WINGUARD","ウィンガード",
        "CP672","N Blue","エヌブルー",
    ],
}

# ── 担当者リスト（ここで一元管理）────────────────────────────────────────────
STAFF_OPTIONS = ["(未選択)", "所長", "ベテラン社員", "主任リーダー", "派遣社員", "社員A", "作業専門PA", "接客専門PA", "学生PA"]

# ── スマート予約 マスター定義 ──────────────────────────────────────────────────
SHIFT_HOURS  = {"A":(8,17),"D":(9,18),"Q":(11,20),"C":(9,18),"H":(9,17)}
SHIFT_BREAKS = {"A":(12,13),"H":(12,13),"C":(13,14),"D":(14,15),"Q":(15,16)}
STAFF_DEFAULT_SHIFT = {
    "主任リーダー":"A","派遣社員":"D","作業専門PA":"C",
    "所長":"D","ベテラン社員":"C",
    "接客専門PA":"Q","社員A":"H","学生PA":"D",
}
# 残業可能スタッフ（雇用形態・個別合意による）
# 派遣社員=派遣のため残業不可、接客専門PA/学生PA=アルバイトのため残業不可
STAFF_CAN_OVERTIME = {"所長", "ベテラン社員", "主任リーダー", "社員A", "作業専門PA"}
_PRO  = ["主任リーダー","派遣社員","作業専門PA"]
_VET  = ["所長","ベテラン社員"]
_KEEP = ["接客専門PA"]
_TIRE = ["社員A"]
MAX_PITS    = 1
MAX_LOANERS = 3
LOANER_CARS = ["マーチ","ティーダ","サクシードバン"]
WORK_MATRIX = {
    "タイヤ交換（4本）":           {"duration":60,  "pit":True,  "flex":False,"loaner":False,"qualified":_PRO+_VET,      "2p":True},
    "タイヤ交換見積もり":           {"duration":30,  "pit":False, "flex":False,"loaner":False,"qualified":_PRO+_VET+_TIRE,"2p":False},
    "車検見積もり":                 {"duration":90,  "pit":True,  "flex":False,"loaner":False,"qualified":_PRO,            "2p":False},
    "車検（当日お預かり）":          {"duration":480, "pit":False, "flex":False,"loaner":True, "qualified":_PRO,            "2p":False,"all_day":True},
    "オイル交換（軽・普通）":       {"duration":30,  "pit":True,  "flex":True, "loaner":False,"qualified":_PRO+_VET,      "2p":False},
    "オイル交換（大型等）":         {"duration":60,  "pit":True,  "flex":False,"loaner":False,"qualified":_PRO+_VET,      "2p":False},
    "バッテリー交換":               {"duration":20,  "pit":False, "flex":False,"loaner":False,"qualified":_PRO+_VET,      "2p":False},
    "タイヤ脱着（履き替え）":       {"duration":20,  "pit":True,  "flex":False,"loaner":False,"qualified":_PRO+_VET,      "2p":False},
    "ローテーション":               {"duration":20,  "pit":True,  "flex":False,"loaner":False,"qualified":_PRO+_VET,      "2p":False},
    "クリスタル/フレッシュキーパー":{"duration":120, "pit":True,  "flex":True, "loaner":False,"qualified":_PRO+_KEEP,     "2p":True},
    "ダイヤモンドキーパー":         {"duration":180, "pit":True,  "flex":True, "loaner":False,"qualified":_PRO+_KEEP,     "2p":True},
    "EXキーパー":                   {"duration":360, "pit":True,  "flex":True, "loaner":False,"qualified":_PRO+_KEEP,     "2p":True},
    "その他":                       {"duration":30,  "pit":False, "flex":False,"loaner":False,"qualified":_PRO+_VET+_TIRE+_KEEP,"2p":False},
}
SB_TIME_SLOTS = [(h, m) for h in range(9, 19) for m in (0, 30)]

# ── 車体サイズ選択肢 ──────────────────────────────────────────────────────────
SIZE_OPTIONS = ["(未選択)", "SS", "S", "M", "L", "LL", "XL", "軽トラ"]

# ── 車種→(メーカー, サイズ) 包括マップ ──────────────────────────────────────
_CAR_RAW = [
    # ─── レクサス ─────────────────────────────────────────────────────────────
    ("レクサス","SS","CT"),
    ("レクサス","S","IS/ES"),
    ("レクサス","M","HS/SC/UX"),
    ("レクサス","L","GS/LC/LF-A/NX/RC/RZ"),
    ("レクサス","LL","LS/RX"),
    ("レクサス","XL","GX/LM/LX"),
    # ─── トヨタ ───────────────────────────────────────────────────────────────
    ("トヨタ","SS","アクア/ヤリス/ルーミー/タンク/ポルテ/スペイド/ピクシス/ライズ/パッソ"),
    ("トヨタ","S","86/GR86/オーリス/コペン"),
    ("トヨタ","M","C-HR/シエンタ/カローラ/マークX/ウィッシュ/ラクティス/プリウス"),
    ("トヨタ","L","アルファード/ヴェルファイア/ハリアー/アイシス/カムリ/クラウン/エスティマ/ヴォクシー/ノア/エスクァイア/アルテッツァ/マークII/チェイサー/クレスタ/ブレイド"),
    ("トヨタ","LL","RAV4/SAI/ヴァンガード"),
    ("トヨタ","XL","ランドクルーザー/ランクル/プラド/FJクルーザー/ハイエース"),
    # ─── 日産 ─────────────────────────────────────────────────────────────────
    ("日産","SS","デイズ/ルークス/デイズルークス/DAYSルークス/DAYS/モコ/ピノ/オッティ"),
    ("日産","S","ノート/マーチ/キューブ/ティーダ/ラティオ"),
    ("日産","M","ジューク/リーフ/シルフィ/ティアナ/ラフェスタ/ウイングロード/プリメーラ/ブルーバード"),
    ("日産","L","スカイライン/フーガ/セレナ/エクストレイル/GT-R/ムラーノ/ラルゴ"),
    ("日産","LL","エルグランド"),
    ("日産","XL","アルマーダ/パトロール"),
    # ─── ホンダ ───────────────────────────────────────────────────────────────
    ("ホンダ","SS","N-BOX/NBOX/Nボックス/ライフ/Nワゴン/N-WGN/Nスラッシュ/N-ONE/ホビオ/バモス/Z"),
    ("ホンダ","S","フィット/CR-Z/Jazz"),
    ("ホンダ","M","ヴェゼル/フリード/シャトル/インサイト/シビック/エアウェイブ/グレイス/ジェイド"),
    ("ホンダ","L","ステップワゴン/オデッセイ/アコード/レジェンド/エリシオン"),
    ("ホンダ","LL","CR-V/CRV/MDX/パイロット"),
    # ─── 三菱 ─────────────────────────────────────────────────────────────────
    ("三菱","SS","ミニキャブ/アイ/i/タウンボックス"),
    ("三菱","S","ミラージュ/コルト"),
    ("三菱","M","RVR/ランサー/ギャラン/ディアマンテ/ガランフォルティス"),
    ("三菱","L","アウトランダー/エクリプスクロス/グランディス"),
    ("三菱","LL","デリカ"),
    ("三菱","XL","パジェロ"),
    # ─── マツダ ───────────────────────────────────────────────────────────────
    ("マツダ","SS","キャロル"),
    ("マツダ","S","デミオ/マツダ2/ロードスター/MX-5"),
    ("マツダ","M","アクセラ/マツダ3/CX-3/CX-30/RX-8/プレマシー"),
    ("マツダ","L","アテンザ/マツダ6/CX-5/CX-60/ビアンテ/MPV"),
    ("マツダ","LL","CX-8/CX-80"),
    ("マツダ","XL","CX-9"),
    # ─── スバル ───────────────────────────────────────────────────────────────
    ("スバル","SS","ステラ/シフォン/プレオ/R1/R2"),
    ("スバル","S","BRZ/ジャスティ"),
    ("スバル","M","インプレッサ/レヴォーグ/XV/クロストレック/レガシー/WRX/エクシーガ"),
    ("スバル","L","フォレスター/アウトバック/アウトバック"),
    ("スバル","軽トラ","サンバー"),
    # ─── スズキ ───────────────────────────────────────────────────────────────
    ("スズキ","SS","ワゴンR/スペーシア/ハスラー/ジムニー/アルト/ラパン/エブリイ/ツイン/MRワゴン/パレット/セルボ"),
    ("スズキ","S","ソリオ/スイフト/バレーノ/クロスビー/イグニス"),
    ("スズキ","M","エスクード/グランドビターラ"),
    ("スズキ","軽トラ","キャリイ/スーパーキャリイ"),
    # ─── ダイハツ ─────────────────────────────────────────────────────────────
    ("ダイハツ","SS","タント/ムーヴ/ミラ/コペン/キャスト/ウェイク/アトレー/ミライース/ネイキッド/エッセ/ソニカ/MAX/ムーヴコンテ/ムーヴキャンバス"),
    ("ダイハツ","S","ロッキー/ブーン/トール/ジャスティ"),
    ("ダイハツ","M","テリオス/ビーゴ"),
    ("ダイハツ","軽トラ","ハイゼット"),
    # ─── メルセデス ───────────────────────────────────────────────────────────
    ("メルセデス","S","Aクラス/ベンツ/Mercedes"),
    ("メルセデス","M","Bクラス/CLA/GLA/GLB"),
    ("メルセデス","L","Cクラス/Eクラス/CLS/GLC/AMG"),
    ("メルセデス","LL","Sクラス"),
    ("メルセデス","XL","GLE/GLS"),
    # ─── BMW ──────────────────────────────────────────────────────────────────
    ("BMW","S","1シリーズ/X2/Z4/i3"),
    ("BMW","M","2シリーズ/3シリーズ/4シリーズ/X1/i8/M3"),
    ("BMW","L","5シリーズ/6シリーズ/X3/X4/M5"),
    ("BMW","LL","7シリーズ"),
    ("BMW","XL","X5/X6/X7"),
    # ─── アウディ ─────────────────────────────────────────────────────────────
    ("アウディ","S","A1/TT"),
    ("アウディ","M","A3/A4/A5/Q2/R8"),
    ("アウディ","L","A6/A7/Q3/Q5/e-tron"),
    ("アウディ","LL","A8"),
    ("アウディ","XL","Q7/Q8"),
    # ─── VW ───────────────────────────────────────────────────────────────────
    ("VW","S","ポロ/Polo"),
    ("VW","M","ゴルフ/Golf/アルテオン/フォルクスワーゲン"),
    ("VW","L","パサート/ティグアン"),
    ("VW","LL","シャラン"),
    ("VW","XL","トゥアレグ/Touareg"),
    # ─── ボルボ ───────────────────────────────────────────────────────────────
    ("ボルボ","M","XC40/V40/V60/S60/C40"),
    ("ボルボ","L","XC60/V90/S90"),
    ("ボルボ","XL","XC90"),
    # ─── ジャガー ─────────────────────────────────────────────────────────────
    ("ジャガー","M","XE/F-Type/E-Pace"),
    ("ジャガー","L","XF/F-Pace/I-Pace"),
    ("ジャガー","LL","XJ"),
    # ─── ランドローバー ───────────────────────────────────────────────────────
    ("ランドローバー","L","フリーランダー/イヴォーク/Evoque/ヴェラール/Velar"),
    ("ランドローバー","XL","レンジローバー/ディスカバリー/ディフェンダー"),
]

CAR_MODEL_INFO_MAP: dict[str, tuple[str, str]] = {}
for _m, _s, _names in _CAR_RAW:
    for _n in _names.split("/"):
        _n = re.sub(r'\s*\([^)]*\)', '', _n).strip()
        if _n:
            CAR_MODEL_INFO_MAP[_n] = (_m, _s)
del _m, _s, _names, _n, _CAR_RAW

HISTORY_COLS = [
    "date","purpose","cust_type",
    "plate_area","plate_3digit","plate_kana","plate_num",
    "maker","car_model","car_size","color",
    "age","gender",
    "tire_size","tire_size_num","tire_year","tire_maker","tire_product",
    "staff","memo",
    "shaken_date","weather","air_check",
]
WEATHER_OPTIONS    = ["(未選択)", "晴", "曇", "雨"]
AIR_CHECK_OPTIONS  = ["(未選択)", "◎（客発信）", "○（スタッフ声掛けOK）", "×（断り）", "△（要相談・その他）"]
SCHEDULE_COLS    = ["id","date","time","title","detail","status","plate_num","cust_type","sb_duration","sb_use_pit","sb_want_loaner","cust_name","cust_contact","cust_car","loaner_car","sb_staff"]
TIRE_PRICES_CSV      = BASE_DIR / "tire_prices.csv"
TIRE_PRICE_COLS      = ["size","product_name","retail_price"]
CUSTOM_MAPPINGS_JSON = BASE_DIR / "custom_mappings.json"

PRESET_LABELS = [
    "① 標準（定価+工賃+廃タイヤ）",
    "② 税抜化（タイヤのみ税抜換算）",
    "③ 工賃サービス（工賃0円）",
    "④ 諸費用サービス（工賃+廃タイヤ0円）",
    "⑤ A表価格（定価70%+諸費用0円）",
]
STD_LABOR = 1650   # 標準工賃（税込/本）
STD_DISP  = 550    # 廃タイヤ料（税込/本）

DAYS_JP = ["月","火","水","木","金","土","日"]

# ── CSV I/O ───────────────────────────────────────────────────────────────────
def load_history() -> pd.DataFrame:
    if not HISTORY_CSV.exists():
        pd.DataFrame(columns=HISTORY_COLS).to_csv(HISTORY_CSV, index=False)
        return pd.DataFrame(columns=HISTORY_COLS)
    df = pd.read_csv(HISTORY_CSV, dtype=str).fillna("")
    if "plate" in df.columns and "plate_num" not in df.columns:
        df["plate_num"] = df["plate"]
    if "type" in df.columns and "purpose" not in df.columns:
        df["purpose"] = df["type"].str.replace(r"^[\S]+\s+", "", regex=True)
    if "note" in df.columns and "memo" not in df.columns:
        df["memo"] = df["note"]
    for c in HISTORY_COLS:
        if c not in df.columns: df[c] = ""
    return df[HISTORY_COLS]

def save_history(df: pd.DataFrame):
    df[HISTORY_COLS].to_csv(HISTORY_CSV, index=False)

def append_record(row: dict):
    save_history(pd.concat([pd.DataFrame([row]), load_history()], ignore_index=True))

def load_schedule() -> pd.DataFrame:
    if not SCHEDULE_CSV.exists():
        pd.DataFrame(columns=SCHEDULE_COLS).to_csv(SCHEDULE_CSV, index=False)
        return pd.DataFrame(columns=SCHEDULE_COLS)
    df = pd.read_csv(SCHEDULE_CSV, dtype=str).fillna("")
    for c in SCHEDULE_COLS:
        if c not in df.columns: df[c] = ""
    return df[SCHEDULE_COLS]

def save_schedule(df: pd.DataFrame):
    df[SCHEDULE_COLS].to_csv(SCHEDULE_CSV, index=False)

_CHANGE_LOG_COLS = ["timestamp", "action", "date", "time", "memo"]

def append_change_log(action: str, date: str, time: str, memo: str):
    """操作履歴を change_log.csv へ1行追記する。ファイルがなければヘッダー付きで新規作成。"""
    from datetime import datetime as _dt
    row = {
        "timestamp": _dt.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action":    action,
        "date":      date,
        "time":      time,
        "memo":      memo,
    }
    write_header = not CHANGE_LOG_CSV.exists()
    pd.DataFrame([row])[_CHANGE_LOG_COLS].to_csv(
        CHANGE_LOG_CSV, mode="a", index=False, header=write_header
    )

def load_tire_prices() -> pd.DataFrame:
    sample = [
        # 155/65R14
        ("155/65R14","ECOPIA EP150",12650),("155/65R14","NEWNO",11000),("155/65R14","セイバーリング SL201",8250),
        # 165/65R13
        ("165/65R13","ECOPIA EP150",11000),("165/65R13","セイバーリング SL201",7700),
        # 175/65R14
        ("175/65R14","ECOPIA EP300",14300),("175/65R14","NEWNO",12100),("175/65R14","セイバーリング SL201",8800),
        # 185/65R15
        ("185/65R15","REGNO GR-XIII",19800),("185/65R15","ECOPIA EP300",15400),("185/65R15","NEWNO",12650),("185/65R15","セイバーリング SL201",9350),
        # 195/65R15
        ("195/65R15","REGNO GR-XIII",21450),("195/65R15","ECOPIA EP300",17050),("195/65R15","NEWNO",14300),("195/65R15","セイバーリング SL201",9900),
        # 205/55R16
        ("205/55R16","REGNO GR-XIII",24750),("205/55R16","ECOPIA EP300",20350),("205/55R16","NEWNO",16500),("205/55R16","セイバーリング SL201",11550),
        # 205/60R16
        ("205/60R16","REGNO GR-XIII",23100),("205/60R16","ECOPIA EP300",18700),("205/60R16","NEWNO",15400),("205/60R16","セイバーリング SL201",10450),
        # 215/45R17
        ("215/45R17","REGNO GR-XIII",28600),("215/45R17","ECOPIA EP300",23100),("215/45R17","POTENZA Sport",39600),("215/45R17","セイバーリング SL501",13200),
        # 215/50R17
        ("215/50R17","REGNO GR-XIII",27500),("215/50R17","ECOPIA EP300",22000),("215/50R17","NEWNO",18150),("215/50R17","セイバーリング SL501",12650),
        # 215/55R17
        ("215/55R17","REGNO GR-XIII",26400),("215/55R17","ECOPIA EP300",21450),("215/55R17","NEWNO",17600),("215/55R17","セイバーリング SL201",12100),
        # 225/45R18
        ("225/45R18","REGNO GR-XIII",33000),("225/45R18","ECOPIA EP300",27500),("225/45R18","POTENZA Sport",44000),("225/45R18","セイバーリング SL501",15400),
        # 225/50R18
        ("225/50R18","REGNO GR-XIII",31900),("225/50R18","ECOPIA EP300",26400),("225/50R18","POTENZA Sport",42900),("225/50R18","セイバーリング SL501",14850),
        # 225/55R18
        ("225/55R18","REGNO GR-XIII",30800),("225/55R18","ECOPIA EP300",25300),("225/55R18","ALENZA 001",38500),("225/55R18","セイバーリング SL201",14300),
        # 235/50R18
        ("235/50R18","REGNO GR-XIII",34100),("235/50R18","POTENZA Sport",46200),("235/50R18","ALENZA 001",39600),("235/50R18","セイバーリング SL501",16500),
        # 245/40R19
        ("245/40R19","REGNO GR-XIII",39600),("245/40R19","POTENZA Sport",55000),("245/40R19","セイバーリング SL501",20900),
        # 165/60R15 (軽SUV)
        ("165/60R15","ECOPIA EP150",14850),("165/60R15","NEWNO",12650),("165/60R15","セイバーリング SL201",9900),
    ]
    if not TIRE_PRICES_CSV.exists():
        df = pd.DataFrame(sample, columns=TIRE_PRICE_COLS)
        df.to_csv(TIRE_PRICES_CSV, index=False)
        return df
    df = pd.read_csv(TIRE_PRICES_CSV, dtype=str).fillna("")
    for c in TIRE_PRICE_COLS:
        if c not in df.columns: df[c] = ""
    return df[TIRE_PRICE_COLS]

def load_custom_mappings() -> dict:
    """ユーザー学習済みカスタムマッピングを読み込む。"""
    if not CUSTOM_MAPPINGS_JSON.exists():
        return {"car_models": {}, "tire_products": {}}
    try:
        with open(CUSTOM_MAPPINGS_JSON, "r", encoding="utf-8") as _f:
            _data = json.load(_f)
        _data.setdefault("car_models", {})
        _data.setdefault("tire_products", {})
        return _data
    except Exception:
        return {"car_models": {}, "tire_products": {}}

def save_custom_mappings(data: dict):
    """カスタムマッピングをJSONに保存する。"""
    try:
        with open(CUSTOM_MAPPINGS_JSON, "w", encoding="utf-8") as _f:
            json.dump(data, _f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def tire_to_num(s: str) -> str:
    return re.sub(r"[^\d]", "", s)

def parse_tire_size(s: str) -> str:
    """数字のみ7桁入力 → 標準タイヤサイズ形式に自動変換。例: 2055517→205/55R17"""
    if not s:
        return s
    stripped = s.strip()
    if re.match(r'^\d{7}$', stripped):
        return f"{stripped[:3]}/{stripped[3:5]}R{stripped[5:]}"
    return s

def get_last_record_date():
    """直前に保存されたデータの日付を返す。なければ今日の日付。"""
    df = load_history()
    if df.empty:
        return datetime.now().date()
    df_copy = df.copy()
    df_copy["_dt"] = pd.to_datetime(df_copy["date"], errors="coerce")
    df_sorted = df_copy.dropna(subset=["_dt"]).sort_values("_dt", ascending=False)
    if df_sorted.empty:
        return datetime.now().date()
    return df_sorted["_dt"].iloc[0].date()

def _parse_dt(s: str):
    """'YYYY/MM/DD HH:mm' → (date, hour, min_rounded_to_1). Fallback to now."""
    try:
        dt = datetime.strptime(str(s)[:16], "%Y/%m/%d %H:%M")
        return dt.date(), dt.hour, dt.minute
    except Exception:
        n = datetime.now()
        return n.date(), n.hour, n.minute

def ai_parse_record(text: str, ref_date: str = None) -> tuple:
    """Parse free-form memo via Claude Code CLI (claude -p).
    Returns (result_dict, error_str). On success error_str is "".
    ref_date: 直前データの日付文字列（YYYY/MM/DD）。テキストに日付がない場合に使用。
    """
    today = datetime.now().strftime("%Y/%m/%d %H:%M")
    ref_date_str = ref_date if ref_date else datetime.now().strftime("%Y/%m/%d")
    prompt = f"""今日の日時: {today}
直前データの日付（テキストに日付がない場合はこれを使用）: {ref_date_str}

ガソリンスタンド・タイヤショップの接客メモを解析してJSON形式で返してください。

【抽出項目】
date: 日時（YYYY/MM/DD HH:mm形式。テキストに年月日が含まれない場合は「直前データの日付」を使用。時刻のみある場合は「直前データの日付」と時刻を組み合わせ。日時が全く不明なら今日の現在時刻）
purpose: 来店目的（給油/燃料券/洗車/オイル交換/バッテリー交換/タイヤ見積/タイヤ交換/車検見積/車検/その他）
cust_type: 種別（一般/業者/常連。不明なら""）
plate_area: ナンバー地名（香川/大阪など。不明なら""）
plate_3digit: ナンバー3桁数字（"333"など。不明なら""）
plate_kana: ナンバーかなひらがな1文字（あ/い/う...。不明なら""）
plate_num: ナンバー下4桁数字（"1234"など。不明なら""）
maker: メーカー（トヨタ/レクサス/ホンダ/日産/マツダ/スバル/スズキ/ダイハツ/三菱/メルセデス/BMW/アウディ/VW/ボルボ/ジャガー/ランドローバー/その他。不明なら""）
car_model: 車種名（略称は正式名に変換。例: EXE→エグゼ、プリα→プリウスα、ヴォク→ヴォクシー）
color: カラー（ホワイト/パールホワイト/シルバー/ガンメタ/ブラック/グレー/ネイビー/ブルー/レッド/ピンク/グリーン/ゴールド/ブラウン/ベージュ/オレンジ/その他。不明なら""）
age: 年齢層（10代/20代/30代/40代/50代/60代/70代/80代以上。不明なら""）
gender: 性別（男/女/無記名）
tire_size: タイヤサイズ（195/65R15形式。数字列から変換 例:1956515→195/65R15、1556514→155/65R14）
tire_year: タイヤ製造年下2桁の数字文字列のみ（例:"23"。不明なら""）
tire_maker: タイヤメーカー（ブリヂストン/ヨコハマ/ダンロップ/トーヨー/住友(ファルケン)/ミシュラン/コンチネンタル/ピレリ/グッドイヤー/ハンコック/ネクセン/その他。不明なら""）
tire_product: タイヤ商品名（REGNO/ENASAVE EC204など。不明なら""）
memo: 備考（上記以外の接客情報・特記事項をすべて記載）

【タイヤサイズ変換ルール】
数字7〜8桁: 先頭3桁=幅、次2桁=偏平比、末尾2桁=リム径で 幅/偏平比Rリム径 に変換
例: 1956515→195/65R15、1556514→155/65R14、2255518→225/55R18

【メモ】
{text}

JSONオブジェクトのみ返してください（コードブロック・説明文不要）:"""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return {}, result.stderr.strip() or "claude コマンドがエラーを返しました"
        raw = result.stdout.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw).strip()
        return json.loads(raw), ""
    except FileNotFoundError:
        return {}, "claude コマンドが見つかりません（Claude Code がインストールされているか確認してください）"
    except subprocess.TimeoutExpired:
        return {}, "タイムアウト（60秒）：再試行してください"
    except json.JSONDecodeError as e:
        return {}, f"JSON解析失敗: {e}"
    except Exception as e:
        return {}, str(e)


def opt(v: str) -> str:
    return "" if v == "(未選択)" else v

def norm_tyear(v: str) -> str:
    """製造年の生値（4桁・漢字混じり・空など）をTIRE_YEAR_OPTIONSに安全にマッピング。
    数字のみ抽出→下2桁を取り、リストになければ先頭の空文字を返す。"""
    digits = re.sub(r"[^\d]", "", str(v))
    candidate = digits[-2:] if len(digits) >= 2 else digits.zfill(2) if digits else ""
    return candidate if candidate in TIRE_YEAR_OPTIONS else ""

def sel_idx(options: list, val: str) -> int:
    return options.index(val) if val in options else 0

def infer_tire_maker(product: str) -> str:
    """タイヤ商品名からメーカーを部分一致で推定する。カスタム辞書→組み込み順で検索。"""
    if not product:
        return ""
    p = product.upper()
    # カスタム辞書を優先チェック（部分一致）
    for kw, v in load_custom_mappings().get("tire_products", {}).items():
        if kw.upper() in p:
            return v.get("maker", "")
    # 組み込み辞書
    for maker, keywords in TIRE_PRODUCT_MAKER_MAP.items():
        for kw in keywords:
            if kw.upper() in p:
                return maker
    return ""

def infer_car_info(model: str) -> tuple[str, str]:
    """車種名から(メーカー, サイズ)を部分一致で推定する。カスタム辞書→組み込み順で検索。"""
    if not model:
        return "", ""
    # カスタム辞書を優先チェック（部分一致）
    for kw, v in load_custom_mappings().get("car_models", {}).items():
        if kw in model or kw.upper() in model.upper():
            return v.get("maker", ""), v.get("size", "")
    # 組み込み辞書
    for kw, (maker, size) in CAR_MODEL_INFO_MAP.items():
        if kw in model or kw.upper() in model.upper():
            return maker, size
    return "", ""

def infer_car_maker(model: str) -> str:
    """車種名から自動車メーカーを部分一致で推定する。一致なしは空文字を返す。"""
    return infer_car_info(model)[0]

def learn_car_mapping(car_model: str, maker: str, size: str):
    """車種→(メーカー,サイズ)の未知組み合わせをカスタム辞書に学習する。
    既存の組み込み＋カスタム辞書で既に検出できる場合はスキップ。"""
    if not car_model or not maker or maker == "(未選択)":
        return
    if infer_car_info(car_model)[0]:  # 既知ならスキップ
        return
    data = load_custom_mappings()
    _sz = size if size and size not in ("(未選択)", "") else ""
    if data["car_models"].get(car_model) == {"maker": maker, "size": _sz}:
        return  # 同一内容なら上書きしない
    data["car_models"][car_model] = {"maker": maker, "size": _sz}
    save_custom_mappings(data)

def learn_tire_mapping(tire_product: str, tire_maker: str):
    """タイヤ商品名→メーカーの未知組み合わせをカスタム辞書に学習する。
    既存の組み込み＋カスタム辞書で既に検出できる場合はスキップ。"""
    if not tire_product or len(tire_product) < 3 or not tire_maker or tire_maker == "(未選択)":
        return
    if infer_tire_maker(tire_product):  # 既知ならスキップ
        return
    data = load_custom_mappings()
    if data["tire_products"].get(tire_product, {}).get("maker") == tire_maker:
        return
    data["tire_products"][tire_product] = {"maker": tire_maker}
    save_custom_mappings(data)

# ── 見積フォーム コールバック ────────────────────────────────────────────────
def _on_q_tp_change():
    detected = infer_tire_maker(st.session_state.get("q_tp", ""))
    if detected and detected in TIRE_MAKER_OPTIONS:
        st.session_state["q_tm"] = detected

def _on_q_tp_sel_change():
    detected = infer_tire_maker(st.session_state.get("q_tp", ""))
    if detected and detected in TIRE_MAKER_OPTIONS:
        st.session_state["q_tm"] = detected

def _make_q_tp_cb(idx: int):
    key = f"q_tp_{idx}"
    def _cb():
        detected = infer_tire_maker(st.session_state.get(key, ""))
        if detected and detected in TIRE_MAKER_OPTIONS:
            st.session_state[f"q_tm_{idx}"] = detected
    return _cb

_Q_TP_CBS = [_make_q_tp_cb(i) for i in range(3)]

def _make_size_cb(idx: int):
    key = f"q_size_{idx}"
    def _cb():
        raw = st.session_state.get(key, "")
        parsed = parse_tire_size(raw)
        if parsed != raw:
            st.session_state[key] = parsed
    return _cb

_Q_SIZE_CBS = [_make_size_cb(i) for i in range(3)]

# ── 新規来店フォーム コールバック ─────────────────────────────────────────────
def _on_nr_num_change():
    """車番下4桁が変わるたびに過去データを検索してマッチをキャッシュする。
    一意な (maker, car_model) 組み合わせを最大3件リストで保持する。"""
    num = st.session_state.get("nr_num", "").strip()
    if len(num) == 4 and num.isdigit():
        _df = load_history()
        _hits = _df[_df["plate_num"] == num]
        if not _hits.empty:
            _hc = _hits.copy()
            _hc["_dt"] = pd.to_datetime(_hc["date"], errors="coerce")
            _hc = _hc.sort_values("_dt", ascending=False)
            _seen, _matches = set(), []
            for _, _row in _hc.iterrows():
                _key = (_row.get("maker", ""), _row.get("car_model", ""))
                if _key not in _seen:
                    _seen.add(_key)
                    _matches.append(_row.to_dict())
                    if len(_matches) >= 3:
                        break
            st.session_state["nr_plate_matches"] = _matches
            st.session_state["nr_plate_match"]   = _matches[0]  # 後方互換
            return
    st.session_state["nr_plate_matches"] = []
    st.session_state["nr_plate_match"]   = None

def _nr_match_labels(matches: list) -> list:
    """引き継ぎ候補リストから表示ラベルを生成する。"""
    labels = []
    for m in matches:
        _car = " ".join(filter(None, [m.get("maker",""), m.get("car_model","")]))
        _date = m.get("date","")[:10]
        labels.append(f"{_date}　{_car}" if _car else _date)
    return labels

def _do_nr_inherit():
    """引き継ぎボタンの on_click コールバック。
    複数候補がある場合は nr_inherit_radio の選択値で対象を決定する。"""
    _matches = st.session_state.get("nr_plate_matches", [])
    if not _matches:
        return
    # ラジオ選択からインデックスを逆引き
    _labels = _nr_match_labels(_matches)
    _sel_label = st.session_state.get("nr_inherit_radio", _labels[0] if _labels else "")
    try:
        _idx = _labels.index(_sel_label)
    except ValueError:
        _idx = 0
    _pm = _matches[_idx] if _idx < len(_matches) else _matches[0]
    _c0 = _pm.get("cust_type", "")
    st.session_state["nr_ctype"]    = _c0 if _c0 in CUST_TYPE_OPTIONS else "一般"
    _mk  = _pm.get("maker", "")
    _car = _pm.get("car_model", "")
    _sz  = _pm.get("car_size", "")
    _inf_mk, _inf_sz = infer_car_info(_car)
    st.session_state["nr_maker"]    = _mk if _mk in MAKER_OPTIONS else _inf_mk or "(未選択)"
    st.session_state["nr_car"]      = _car
    st.session_state["nr_car_size"] = _sz if _sz in SIZE_OPTIONS else _inf_sz or "(未選択)"
    _cl = _pm.get("color", "")
    st.session_state["nr_color"]    = _cl if _cl in COLOR_OPTIONS else "(未選択)"
    _tp = _pm.get("tire_product", "")
    _tm = _pm.get("tire_maker", "")
    st.session_state["nr_tprod"]    = _tp
    st.session_state["nr_tmaker"]   = _tm if _tm in TIRE_MAKER_OPTIONS else infer_tire_maker(_tp) or "(未選択)"
    st.session_state["nr_tsize"]    = _pm.get("tire_size", "")
    st.session_state["nr_tyear"]    = norm_tyear(_pm.get("tire_year", ""))
    st.session_state["nr_plate_matches"] = []
    st.session_state["nr_plate_match"]   = None

def _on_nr_car_change():
    maker, size = infer_car_info(st.session_state.get("nr_car", ""))
    if maker and maker in MAKER_OPTIONS:
        st.session_state["nr_maker"] = maker
    if size and size in SIZE_OPTIONS:
        st.session_state["nr_car_size"] = size

def _on_nr_tprod_change():
    _tp = st.session_state.get("nr_tprod", "")
    if _tp.strip().upper() == "K370":
        st.session_state["nr_tmaker"] = "ブリヂストン"
        st.session_state["nr_tsize"]  = "145/80R12"
        return
    detected = infer_tire_maker(_tp)
    if detected and detected in TIRE_MAKER_OPTIONS:
        st.session_state["nr_tmaker"] = detected

# ── 編集フォーム コールバック ─────────────────────────────────────────────────
def _on_er_car_change():
    maker, size = infer_car_info(st.session_state.get("er_car", ""))
    if maker and maker in MAKER_OPTIONS:
        st.session_state["er_maker"] = maker
    if size and size in SIZE_OPTIONS:
        st.session_state["er_car_size"] = size

def _on_er_tprod_change():
    _tp = st.session_state.get("er_tprod", "")
    if _tp.strip().upper() == "K370":
        st.session_state["er_tmaker"] = "ブリヂストン"
        st.session_state["er_tsize"]  = "145/80R12"
        return
    detected = infer_tire_maker(_tp)
    if detected and detected in TIRE_MAKER_OPTIONS:
        st.session_state["er_tmaker"] = detected

# ── 作業内容の表示ラベルを生成 ────────────────────────────────────────────────────
def _fmt_title(title: str, detail: str = "") -> str:
    if title == "その他":
        memo = detail.strip()
        return f"その他（{memo[:7]}…）" if memo else "その他"
    return title

# ── ダイアログ widget state を直接注入するユーティリティ ──────────────────────────
def _inject_dialog_state_new(date_str, time_str, work, dur, use_pit, want_loaner, req_loaner_car):
    """新規予約用：ダイアログウィジェットの session_state を直接セット。
    Streamlit は widget key が session_state にある場合 value= を無視するため、
    ここで明示的に全フィールドを書き込むことで確実な初期値バインドを実現する。"""
    _wk_list = list(WORK_MATRIX.keys())
    st.session_state["uf_name"]          = ""
    st.session_state["uf_car_type"]      = ""
    st.session_state["uf_date"]          = date_str
    st.session_state["uf_time"]          = time_str
    st.session_state["uf_job_type"]      = work if work in WORK_MATRIX else _wk_list[0]
    st.session_state["uf_duration"]      = max(10, min(480, int(dur)))
    st.session_state["uf_pit_required"]  = bool(use_pit)
    st.session_state["uf_phone"]         = ""
    st.session_state["uf_memo"]          = ""
    st.session_state["uf_subcar_needed"] = "代車を希望する" if want_loaner else "代車不要"
    if req_loaner_car in LOANER_CARS:
        st.session_state["uf_subcar_type"] = req_loaner_car
    else:
        st.session_state.pop("uf_subcar_type", None)
    st.session_state["uf_staff"]         = "(未選択)"

def _inject_dialog_state_edit(pf: dict):
    """編集予約用：既存データをダイアログウィジェットの session_state へ直接注入。"""
    _wk_list    = list(WORK_MATRIX.keys())
    _dur_raw    = str(pf.get("sb_duration", ""))
    _pre_dur    = max(10, min(480, int(_dur_raw))) if _dur_raw.isdigit() else 30
    _pit_raw    = str(pf.get("sb_use_pit", ""))
    _pre_pit    = (_pit_raw == "1") if _pit_raw in ("0", "1") else False
    _want_lnr   = bool(pf.get("want_loaner", False))
    _loaner_car = str(pf.get("loaner_car", ""))
    _staff      = str(pf.get("sb_staff", ""))
    _title      = str(pf.get("title", ""))
    # title が空・未登録（簡易追加 or レガシーデータ）の場合は「その他」にフォールバック
    _job_type   = _title if _title in WORK_MATRIX else ("その他" if "その他" in WORK_MATRIX else _wk_list[0])
    st.session_state["uf_name"]          = str(pf.get("cust_name", ""))
    st.session_state["uf_car_type"]      = str(pf.get("cust_car", ""))
    st.session_state["uf_date"]          = str(pf.get("date", ""))
    st.session_state["uf_time"]          = str(pf.get("time", ""))
    st.session_state["uf_job_type"]      = _job_type
    st.session_state["uf_duration"]      = _pre_dur
    st.session_state["uf_pit_required"]  = _pre_pit
    st.session_state["uf_phone"]         = str(pf.get("cust_contact", ""))
    st.session_state["uf_memo"]          = str(pf.get("detail", ""))
    st.session_state["uf_subcar_needed"] = "代車を希望する" if _want_lnr else "代車不要"
    if _loaner_car in LOANER_CARS:
        st.session_state["uf_subcar_type"] = _loaner_car
    else:
        st.session_state.pop("uf_subcar_type", None)
    st.session_state["uf_staff"]         = _staff if _staff in STAFF_OPTIONS else "(未選択)"

def _on_cell_click(di, si, date_str, time_str, work, dur, use_pit, want_loaner, req_loaner_car, sym="", rsns=None):
    """グリッドセルクリック時コールバック — △は残業警告、それ以外は予約フォームを開く"""
    _inject_dialog_state_new(date_str, time_str, work, dur, use_pit, want_loaner, req_loaner_car)
    st.session_state["sb_sel_di"]  = di
    st.session_state["sb_sel_si"]  = si
    st.session_state["uf_mode"]    = "new"
    st.session_state["uf_prefill"] = {
        "date": date_str, "time": time_str, "title": work,
        "want_loaner": want_loaner, "loaner_car": req_loaner_car,
    }
    if sym == "△":
        st.session_state["overtime_warning_rsns"] = rsns or []
        st.session_state["show_overtime_warning"]  = True
    else:
        st.session_state["show_booking_dialog"] = True

def _on_open_form_btn_click(date_str, sh, sm_, work, dur, use_pit, want_loaner, req_loaner_car):
    """スロット詳細の「予約する」ボタンコールバック"""
    time_str = f"{sh:02d}:{sm_:02d}"
    _inject_dialog_state_new(date_str, time_str, work, dur, use_pit, want_loaner, req_loaner_car)
    st.session_state["uf_mode"]             = "new"
    st.session_state["uf_prefill"]          = {
        "date": date_str, "time": time_str, "title": work,
        "want_loaner": want_loaner, "loaner_car": req_loaner_car,
    }
    st.session_state["show_booking_dialog"] = True

def _on_wb_card_click(prefill_dict):
    """ホワイトボードカードクリック時コールバック（編集モード）。
    pandas Series から渡された値を確実に Python ネイティブ型へ変換して注入する。"""
    _inject_dialog_state_edit(prefill_dict)
    st.session_state["uf_mode"]    = "edit"
    st.session_state["uf_prefill"] = {
        k: (bool(v) if isinstance(v, bool) else str(v) if v is not None else "")
        for k, v in prefill_dict.items()
    }
    st.session_state["show_booking_dialog"] = True

def _on_archive_card_click(record_id: str):
    """アーカイブカードクリック時コールバック — ダイアログを開く。注入はダイアログ内で行う。"""
    st.session_state["archive_sel_id"]      = record_id
    st.session_state["_arc_needs_init"]     = True
    st.session_state["show_archive_dialog"] = True

def _on_loaner_cell_click(date_str, car):
    """代車貸出管理表の空きセルクリック時コールバック。
    代車有り・指定車種・作業=車検（当日お預かり）を初期値として統一フォームを開く。"""
    _LM_DEFAULT_WORK = "車検（当日お預かり）"
    _LM_DEFAULT_DUR  = WORK_MATRIX[_LM_DEFAULT_WORK]["duration"]
    _inject_dialog_state_new(date_str, "10:00", _LM_DEFAULT_WORK,
                              _LM_DEFAULT_DUR, False, True, car)
    st.session_state["uf_mode"]             = "new"
    st.session_state["uf_prefill"]          = {
        "date": date_str, "time": "10:00",
        "want_loaner": True, "loaner_car": car,
    }
    st.session_state["show_booking_dialog"] = True

def _on_sb_edit_booking_change():
    """既存予約選択時に編集フォームを自動入力するコールバック"""
    selected_id = st.session_state.get("sb_edit_booking_select", "__none__")
    if not selected_id or selected_id == "__none__":
        st.session_state["sb_edit_selected_id"] = None
        return
    sdf = load_schedule()
    rows = sdf[sdf["id"] == selected_id]
    if rows.empty:
        return
    r = rows.iloc[0]
    title = r.get("title", "")
    work_type = title if title in WORK_MATRIX else list(WORK_MATRIX.keys())[0]
    st.session_state["sb_edit_work_type"] = work_type
    _sb_dur = str(r.get("sb_duration", ""))
    duration = int(_sb_dur) if _sb_dur.isdigit() else _sb_estimate_dur(title)
    st.session_state["sb_edit_duration"] = max(10, min(480, duration))
    _sb_pit = str(r.get("sb_use_pit", ""))
    use_pit = (_sb_pit == "1") if _sb_pit in ("0", "1") else _sb_title_uses_pit(title)
    st.session_state["sb_edit_use_pit"] = use_pit
    _sb_loaner = str(r.get("sb_want_loaner", ""))
    want_loaner = (_sb_loaner == "1") if _sb_loaner in ("0", "1") else _sb_title_uses_loaner(title)
    st.session_state["sb_edit_want_loaner"] = "代車を希望する" if want_loaner else "代車不要"
    st.session_state["sb_edit_detail"] = r.get("detail", "")
    st.session_state["sb_edit_selected_id"] = selected_id

# ── 見積HTML生成（全額税込・定価 vs 提案価格 2列） ──────────────────────────
def generate_estimate_html(
    tire_maker: str, tire_product: str, tire_size: str,
    retail_unit: int,   # 定価/本（税込）
    offer_unit: int,    # 提示タイヤ単価/本（税込）
    offer_labor: int,   # 提示工賃/本（税込）
    offer_disp: int,    # 提示廃タイヤ/本（税込）
    qty: int,
    plate: str, customer: str, staff: str,
    maker: str, car_model: str, memo: str
) -> str:
    # 定価列（タイヤ定価 + 標準工賃 + 標準廃タイヤ、全て税込）
    r_tire  = retail_unit * qty
    r_labor = STD_LABOR   * qty
    r_disp  = STD_DISP    * qty
    r_total = r_tire + r_labor + r_disp
    # 提示価格列（全て税込）
    o_tire  = offer_unit  * qty
    o_labor = offer_labor * qty
    o_disp  = offer_disp  * qty
    o_total = o_tire + o_labor + o_disp
    # お得額
    savings  = r_total - o_total
    save_pct = round(savings / r_total * 100, 1) if r_total > 0 else 0
    date_str = datetime.now().strftime("%Y年%m月%d日")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<style>
/* ── 印刷背景色を確実に出力 ── */
* {{ -webkit-print-color-adjust:exact!important;
     print-color-adjust:exact!important;
     color-adjust:exact!important;
     box-sizing:border-box; margin:0; padding:0; }}
@page {{ size:A4 portrait; margin:10mm 12mm; }}
body {{ font-family:'Hiragino Kaku Gothic ProN','Yu Gothic','MS Gothic',sans-serif;
        font-size:10pt; color:#1a1a2e; background:#fff; }}
@media print {{ .noprint{{ display:none!important; }} }}

/* ── ヘッダー（緑） ── */
.est-header {{
  background:#1B5E20; color:#fff;
  padding:11px 16px; display:flex; justify-content:space-between; align-items:center;
  border-radius:4px 4px 0 0;
}}
.est-header-title {{ font-size:16pt; font-weight:800; letter-spacing:.05em; }}
.est-doc-title {{
  font-size:12.5pt; font-weight:700; color:#1B5E20;
  text-align:center; padding:9px 0 5px; border-bottom:2.5px solid #1B5E20;
  letter-spacing:.15em;
}}
.doc-no {{ font-size:8pt; color:#999; text-align:right; margin:3px 0 6px; }}

/* ── 顧客情報帯（緑枠） ── */
.cust-box {{
  display:grid; grid-template-columns:1fr 1fr 1fr 1fr;
  border:1.5px solid #1B5E20; border-radius:4px; margin:6px 0 8px;
}}
.cust-cell {{ padding:6px 10px; border-right:1px solid #1B5E20; }}
.cust-cell:last-child {{ border-right:none; }}
.cust-label {{ font-size:7.5pt; color:#666; margin-bottom:2px; }}
.cust-val   {{ font-size:10.5pt; font-weight:700; }}

/* ── 2列比較テーブル ── */
.compare-wrap {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; margin:8px 0; }}
.price-col {{ border-radius:6px; overflow:hidden; }}
.col-header {{ padding:7px 10px; font-size:9pt; font-weight:800; text-align:center; }}
.col-header-retail  {{ background:#607D8B; color:#fff; }}
.col-header-offer   {{ background:#1B5E20; color:#fff; }}
.col-body {{ padding:0; }}
.price-row {{ display:flex; justify-content:space-between; padding:6px 10px;
              border-bottom:1px solid rgba(0,0,0,.08); font-size:9.5pt; }}
.price-row:last-child {{ border-bottom:none; }}
.pr-label {{ color:#555; }}
.pr-val   {{ font-weight:600; }}
.col-retail-bg  {{ background:#ECEFF1; }}
.col-offer-bg   {{ background:#E8F5E9; }}
.col-retail-total {{ background:#B0BEC5; padding:8px 10px;
                     display:flex; justify-content:space-between;
                     font-size:12pt; font-weight:800; color:#263238; }}
.col-offer-total  {{ background:#1B5E20; padding:8px 10px;
                     display:flex; justify-content:space-between;
                     font-size:12pt; font-weight:800; color:#fff; }}

/* ── お得額ボックス（ピンク） ── */
.savings-box {{
  background:#FCE4EC; border:2px solid #E91E63; border-radius:6px;
  padding:10px 16px; margin:8px 0;
  display:flex; justify-content:space-between; align-items:center;
}}
.savings-label {{ font-size:10pt; font-weight:700; color:#880E4F; }}
.savings-amount {{ font-size:18pt; font-weight:800; color:#C62828; }}
.savings-pct    {{ font-size:11pt; font-weight:700; color:#E91E63; margin-left:8px; }}

/* ── 品目明細テーブル（緑枠） ── */
.detail-section {{ margin:8px 0; }}
.detail-title {{ font-size:8.5pt; font-weight:700; color:#1B5E20;
                 border-bottom:1.5px solid #1B5E20; padding-bottom:3px; margin-bottom:4px; }}
table {{ width:100%; border-collapse:collapse; }}
thead tr {{ background:#1B5E20; color:#fff; }}
th {{ padding:6px 8px; font-size:8.5pt; font-weight:700; }}
td {{ padding:6px 8px; border-bottom:1px solid #C8E6C9; font-size:9.5pt; vertical-align:middle; }}
.td-c {{ text-align:center; }}
.td-r {{ text-align:right; }}
.item-main {{ font-weight:600; }}
.item-sub  {{ font-size:7.5pt; color:#777; }}
tr.row-sub {{ background:#F1F8E9; }}
tr.row-tax {{ background:#F1F8E9; }}
tr.row-offer-total td {{
  background:#FCE4EC; border-top:2px solid #C62828;
  font-size:11.5pt; font-weight:800; color:#C62828;
}}

/* ── メモ（ピンク枠） ── */
.memo-section {{ border:1.5px solid #E91E63; border-radius:4px; padding:8px 12px; margin-top:8px; }}
.memo-title   {{ font-size:8pt; font-weight:700; color:#E91E63; margin-bottom:4px; }}
.memo-body    {{ font-size:9.5pt; line-height:1.75; min-height:44px; white-space:pre-wrap; }}

/* ── フッター ── */
.footer {{
  margin-top:14px; border-top:1px solid #ccc; padding-top:6px;
  font-size:8pt; color:#999; display:flex; justify-content:space-between;
}}
.stamp-area {{ border:1px solid #ccc; width:72px; height:44px;
               text-align:center; line-height:44px; font-size:7.5pt; color:#ccc; border-radius:4px; }}

/* ── 印刷ボタン ── */
.print-btn {{
  display:block; margin:10px auto 6px; padding:9px 34px;
  background:#1B5E20; color:#fff; border:none; border-radius:8px;
  font-size:12pt; font-weight:700; cursor:pointer;
}}
.print-btn:hover {{ background:#2E7D32; }}
</style>
</head>
<body>
<button class="print-btn noprint" onclick="window.print()">🖨️ 印刷する</button>

<!-- ヘッダー -->
<div class="est-header">
  <div>
    <div class="est-header-title">⛽ タイヤ御見積書</div>
    <div style="font-size:8.5pt;opacity:.85">GS 接客支援システム</div>
  </div>
  <div style="text-align:right;font-size:9pt">
    発行日：{date_str}<br>担当：{staff or '___________'}
  </div>
</div>
<div class="est-doc-title">タ イ ヤ 御 見 積 書</div>
<div class="doc-no">No.{datetime.now().strftime("%Y%m%d%H%M")}</div>

<!-- 顧客情報 -->
<div class="cust-box">
  <div class="cust-cell"><div class="cust-label">車番</div><div class="cust-val">{plate or '　　　'}</div></div>
  <div class="cust-cell"><div class="cust-label">お客様</div><div class="cust-val">{customer or '　　　'}</div></div>
  <div class="cust-cell"><div class="cust-label">担当者</div><div class="cust-val">{staff or '　　　'}</div></div>
  <div class="cust-cell"><div class="cust-label">タイヤ</div><div class="cust-val">{tire_maker} {tire_product} {tire_size}</div></div>
</div>

<!-- 定価 vs 提案価格 2列比較 -->
<div class="compare-wrap">
  <!-- 定価列 -->
  <div class="price-col">
    <div class="col-header col-header-retail">定価（メーカー希望小売価格）</div>
    <div class="col-body">
      <div class="price-row col-retail-bg"><span class="pr-label">🛞 タイヤ代 {qty}本</span><span class="pr-val">¥{r_tire:,}</span></div>
      <div class="price-row col-retail-bg"><span class="pr-label">🔧 工賃 {qty}本</span><span class="pr-val">¥{r_labor:,}</span></div>
      <div class="price-row col-retail-bg"><span class="pr-label">♻️ 廃タイヤ {qty}本</span><span class="pr-val">¥{r_disp:,}</span></div>
    </div>
    <div class="col-retail-total"><span>定価合計（税込）</span><span>¥{r_total:,}</span></div>
  </div>
  <!-- 提案価格列 -->
  <div class="price-col">
    <div class="col-header col-header-offer">★ 提案価格（今回のご提案）</div>
    <div class="col-body">
      <div class="price-row col-offer-bg"><span class="pr-label">🛞 タイヤ代 {qty}本</span><span class="pr-val">¥{o_tire:,}</span></div>
      <div class="price-row col-offer-bg"><span class="pr-label">🔧 工賃 {qty}本</span><span class="pr-val">¥{o_labor:,}</span></div>
      <div class="price-row col-offer-bg"><span class="pr-label">♻️ 廃タイヤ {qty}本</span><span class="pr-val">¥{o_disp:,}</span></div>
    </div>
    <div class="col-offer-total"><span>提示価格合計（税込）</span><span>¥{o_total:,}</span></div>
  </div>
</div>

<!-- お得額（ピンク枠） -->
<div class="savings-box">
  <div>
    <div class="savings-label">🎉 定価との差額（お得額）</div>
    <div style="font-size:8pt;color:#888;margin-top:2px">定価合計 ¥{r_total:,} → 提示価格合計 ¥{o_total:,}</div>
  </div>
  <div>
    <span class="savings-amount">¥{savings:,}</span>
    <span class="savings-pct">({save_pct}% OFF)</span>
  </div>
</div>

<!-- 品目明細（緑枠テーブル） -->
<div class="detail-section">
  <div class="detail-title">■ 品目明細（提案価格ベース）</div>
  <table>
    <thead><tr>
      <th style="width:40%;text-align:left">品名・内容</th>
      <th style="width:8%" class="td-c">数量</th>
      <th style="width:10%" class="td-c">単位</th>
      <th style="width:21%" class="td-r">単価（税込）</th>
      <th style="width:21%" class="td-r">金額（税込）</th>
    </tr></thead>
    <tbody>
      <tr>
        <td><div class="item-main">{tire_maker}</div><div class="item-sub">{tire_product}　{tire_size}</div></td>
        <td class="td-c">{qty}</td><td class="td-c">本</td>
        <td class="td-r">¥{offer_unit:,}</td><td class="td-r">¥{o_tire:,}</td>
      </tr>
      <tr>
        <td><div class="item-main">タイヤ取付工賃</div></td>
        <td class="td-c">{qty}</td><td class="td-c">本</td>
        <td class="td-r">¥{offer_labor:,}</td><td class="td-r">¥{o_labor:,}</td>
      </tr>
      <tr>
        <td><div class="item-main">廃タイヤ処理料</div></td>
        <td class="td-c">{qty}</td><td class="td-c">本</td>
        <td class="td-r">¥{offer_disp:,}</td><td class="td-r">¥{o_disp:,}</td>
      </tr>
      <tr class="row-offer-total">
        <td colspan="4" class="td-r">★ ご請求合計（税込）</td>
        <td class="td-r">¥{o_total:,}</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- 接客メモ（ピンク枠） -->
<div class="memo-section">
  <div class="memo-title">📝 接客メモ・特記事項</div>
  <div class="memo-body">{memo if memo else '　'}</div>
</div>

<!-- フッター -->
<div class="footer">
  <div>
    ※ 本見積の有効期限は発行日より30日間です。<br>
    ※ 定価はメーカー希望小売価格（税込）を参考としています。
  </div>
  <div style="text-align:right"><div class="stamp-area">確認印</div></div>
</div>
</body>
</html>"""


# ── 複数商品対応見積HTML生成 ──────────────────────────────────────────────────
def generate_estimate_html_multi(
    products: list,
    labels: list,
    plate: str, customer: str, staff: str,
    maker: str, car_model: str, memo: str
) -> str:
    """1〜3商品の見積書HTML。productsは入力済みのdictリスト、labelsは商品ラベルリスト。"""
    n = len(products)
    grid_cols = f"repeat({n},1fr)"
    date_str = datetime.now().strftime("%Y年%m月%d日")

    def fmt_product_col(p: dict, lbl: str) -> str:
        r_tire  = p["retail_price"] * p["q_qty"]
        r_labor = STD_LABOR         * p["q_qty"]
        r_disp  = STD_DISP          * p["q_qty"]
        r_total = r_tire + r_labor + r_disp
        o_tire  = p["offer_unit"]  * p["q_qty"]
        o_labor = p["offer_labor"] * p["q_qty"]
        o_disp  = p["offer_disp"]  * p["q_qty"]
        o_total = p["o_total"]
        savings = p["savings"]
        save_pct = round(savings / r_total * 100, 1) if r_total > 0 else 0
        size_str = p.get("size_p", "")
        maker_s  = opt(p.get("q_tm", ""))
        prod_s   = p.get("q_tp", "")
        qty      = p["q_qty"]
        savings_color = "#c62828" if savings > 0 else "#888"
        savings_html = ""
        if savings > 0:
            savings_html = f'<div style="background:#FCE4EC;border:1.5px solid #E91E63;border-radius:6px;padding:6px 10px;margin-top:6px;text-align:center"><div style="font-size:7.5pt;color:#880E4F;font-weight:700">🎉 お得額</div><div style="font-size:14pt;font-weight:800;color:{savings_color}">¥{savings:,}</div><div style="font-size:7.5pt;color:#E91E63">({save_pct}% OFF)</div></div>'
        return f"""
        <div style="border:1.5px solid #1B5E20;border-radius:8px;overflow:hidden">
          <div style="background:#1B5E20;color:#fff;padding:8px 10px;font-size:9.5pt;font-weight:800;text-align:center">{lbl}</div>
          <div style="padding:8px 10px">
            <div style="font-size:9pt;font-weight:700;color:#1B5E20;margin-bottom:2px">{maker_s}</div>
            <div style="font-size:8.5pt;font-weight:600">{prod_s}</div>
            <div style="font-size:8pt;color:#555;margin-bottom:6px">{size_str} × {qty}本</div>
            <table style="width:100%;border-collapse:collapse;font-size:8pt;margin:6px 0">
              <tr style="background:#ECEFF1">
                <td colspan="2" style="padding:3px 6px;font-weight:700;color:#607D8B">定価（税込）</td>
              </tr>
              <tr><td style="padding:2px 6px;color:#555">🛞 タイヤ代 {qty}本</td><td style="padding:2px 6px;text-align:right">¥{r_tire:,}</td></tr>
              <tr><td style="padding:2px 6px;color:#555">🔧 工賃 {qty}本</td><td style="padding:2px 6px;text-align:right">¥{r_labor:,}</td></tr>
              <tr><td style="padding:2px 6px;color:#555">♻️ 廃タイヤ {qty}本</td><td style="padding:2px 6px;text-align:right">¥{r_disp:,}</td></tr>
              <tr style="background:#B0BEC5;font-weight:700">
                <td style="padding:4px 6px">定価合計</td><td style="padding:4px 6px;text-align:right">¥{r_total:,}</td>
              </tr>
              <tr style="background:#E8F5E9;margin-top:4px">
                <td colspan="2" style="padding:3px 6px;font-weight:700;color:#1B5E20">★ 提案価格（税込）</td>
              </tr>
              <tr><td style="padding:2px 6px;color:#555">🛞 タイヤ代 {qty}本</td><td style="padding:2px 6px;text-align:right">¥{o_tire:,}</td></tr>
              <tr><td style="padding:2px 6px;color:#555">🔧 工賃 {qty}本</td><td style="padding:2px 6px;text-align:right">¥{o_labor:,}</td></tr>
              <tr><td style="padding:2px 6px;color:#555">♻️ 廃タイヤ {qty}本</td><td style="padding:2px 6px;text-align:right">¥{o_disp:,}</td></tr>
              <tr style="background:#1B5E20;color:#fff;font-size:10pt;font-weight:800">
                <td style="padding:6px 6px">★ 提示合計</td><td style="padding:6px 6px;text-align:right">¥{o_total:,}</td>
              </tr>
            </table>
            {savings_html}
          </div>
        </div>"""

    product_cols_html = "\n".join(
        fmt_product_col(p, lbl) for p, lbl in zip(products, labels)
    )

    car_str = " ".join(filter(None, [maker, car_model]))

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<style>
*{{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important;color-adjust:exact!important;box-sizing:border-box;margin:0;padding:0;}}
@page{{size:A4 portrait;margin:10mm 12mm;}}
body{{font-family:'Hiragino Kaku Gothic ProN','Yu Gothic','MS Gothic',sans-serif;font-size:10pt;color:#1a1a2e;background:#fff;}}
@media print{{.noprint{{display:none!important;}}}}
.est-header{{background:#1B5E20;color:#fff;padding:11px 16px;display:flex;justify-content:space-between;align-items:center;border-radius:4px 4px 0 0;}}
.est-header-title{{font-size:16pt;font-weight:800;letter-spacing:.05em;}}
.est-doc-title{{font-size:12.5pt;font-weight:700;color:#1B5E20;text-align:center;padding:9px 0 5px;border-bottom:2.5px solid #1B5E20;letter-spacing:.15em;}}
.doc-no{{font-size:8pt;color:#999;text-align:right;margin:3px 0 6px;}}
.cust-box{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;border:1.5px solid #1B5E20;border-radius:4px;margin:6px 0 8px;}}
.cust-cell{{padding:6px 10px;border-right:1px solid #1B5E20;}}
.cust-cell:last-child{{border-right:none;}}
.cust-label{{font-size:7.5pt;color:#666;margin-bottom:2px;}}
.cust-val{{font-size:10.5pt;font-weight:700;}}
.memo-section{{border:1.5px solid #E91E63;border-radius:4px;padding:8px 12px;margin-top:8px;}}
.memo-title{{font-size:8pt;font-weight:700;color:#E91E63;margin-bottom:4px;}}
.memo-body{{font-size:9.5pt;line-height:1.75;min-height:44px;white-space:pre-wrap;}}
.footer{{margin-top:14px;border-top:1px solid #ccc;padding-top:6px;font-size:8pt;color:#999;display:flex;justify-content:space-between;}}
.stamp-area{{border:1px solid #ccc;width:72px;height:44px;text-align:center;line-height:44px;font-size:7.5pt;color:#ccc;border-radius:4px;}}
.print-btn{{display:block;margin:10px auto 6px;padding:9px 34px;background:#1B5E20;color:#fff;border:none;border-radius:8px;font-size:12pt;font-weight:700;cursor:pointer;}}
.print-btn:hover{{background:#2E7D32;}}
</style>
</head>
<body>
<button class="print-btn noprint" onclick="window.print()">🖨️ 印刷する</button>
<div class="est-header">
  <div>
    <div class="est-header-title">⛽ タイヤ御見積書</div>
    <div style="font-size:8.5pt;opacity:.85">GS 接客支援システム</div>
  </div>
  <div style="text-align:right;font-size:9pt">発行日：{date_str}<br>担当：{staff or '___________'}</div>
</div>
<div class="est-doc-title">タ イ ヤ 御 見 積 書</div>
<div class="doc-no">No.{datetime.now().strftime("%Y%m%d%H%M")}</div>
<div class="cust-box">
  <div class="cust-cell"><div class="cust-label">車番</div><div class="cust-val">{plate or '　　　'}</div></div>
  <div class="cust-cell"><div class="cust-label">お客様</div><div class="cust-val">{customer or '　　　'}</div></div>
  <div class="cust-cell"><div class="cust-label">車両</div><div class="cust-val">{car_str or '　　　'}</div></div>
  <div class="cust-cell"><div class="cust-label">担当者</div><div class="cust-val">{staff or '　　　'}</div></div>
</div>
<div style="display:grid;grid-template-columns:{grid_cols};gap:8px;margin:10px 0">
{product_cols_html}
</div>
<div class="memo-section">
  <div class="memo-title">📝 接客メモ・特記事項</div>
  <div class="memo-body">{memo if memo else '　'}</div>
</div>
<div class="footer">
  <div>※ 本見積の有効期限は発行日より30日間です。<br>※ 定価はメーカー希望小売価格（税込）を参考としています。</div>
  <div style="text-align:right"><div class="stamp-area">確認印</div></div>
</div>
</body>
</html>"""


# ── スマート予約 ヘルパー関数 ─────────────────────────────────────────────────
def _sb_title_uses_pit(title: str) -> bool:
    return any(k in title for k in ["タイヤ交換","車検見積","オイル交換","タイヤ脱着","ローテーション","キーパー","コーティング"])

def _sb_title_uses_loaner(title: str) -> bool:
    return "車検" in title and "見積" not in title

def _sb_estimate_dur(title: str) -> int:
    if "EXキーパー" in title:              return 360
    if "ダイヤモンドキーパー" in title:    return 180
    if "キーパー" in title or "コーティング" in title: return 120
    if "車検見積" in title:                return 90
    if "車検" in title:                    return 480
    if "オイル交換（大型" in title:        return 60
    if "タイヤ交換（4本）" in title:       return 60
    if "タイヤ交換" in title and "見積" not in title: return 60
    if "タイヤ交換見積" in title or "タイヤ見積" in title: return 30
    if "オイル交換" in title:              return 30
    if "バッテリー" in title:              return 20
    if "タイヤ脱着" in title or "履き替え" in title: return 20
    if "ローテーション" in title:          return 20
    return 30

def _sb_compute_slot(date_d, slot_h, slot_m, work_type, duration, work, active_df,
                     want_loaner=False, requested_loaner_car=""):
    """◎/◯/△/× と理由リストを返す（休憩時間考慮版）"""
    qualified  = work["qualified"]
    pit_req    = work.get("pit", False)
    pit_flex   = work.get("flex", False)
    loaner_req = want_loaner or work.get("loaner", False)
    date_str   = date_d.strftime("%Y/%m/%d")
    s_start    = slot_h * 60 + slot_m
    s_end      = s_start + duration

    # ── スタッフ在籍チェック（シフト範囲 + 有給/会議/休 + 休憩時間 + 残業を区別）
    avail_active   = []   # 通常勤務中（休憩なし）
    avail_break    = []   # 在籍中だが休憩時間と重複
    avail_overtime = []   # 作業開始はシフト内だが終了が定時超え（残業が必要）

    for nm in qualified:
        shift = STAFF_DEFAULT_SHIFT.get(nm)
        if not shift:
            continue
        sh_t, eh_t = SHIFT_HOURS[shift]
        sh_m, eh_m = sh_t * 60, eh_t * 60

        in_shift    = (sh_m <= s_start and s_end <= eh_m)
        is_overtime = (sh_m <= s_start < eh_m and s_end > eh_m)

        if not in_shift and not is_overtime:
            continue

        # 有給・会議・休 ブロックチェック（残業候補にも適用）
        blocked = False
        if not active_df.empty:
            for _, row in active_df[active_df["date"] == date_str].iterrows():
                t = row.get("title",""); d = row.get("detail","")
                if any(kw in t for kw in ["有給","会議","休"]):
                    if nm in t or nm in d:
                        blocked = True; break
        if blocked:
            continue

        if is_overtime:
            if nm in STAFF_CAN_OVERTIME:   # 残業不可スタッフ（派遣・アルバイト等）は除外
                avail_overtime.append(nm)
            continue   # avail_active/break には加えない

        # 休憩時間との重複チェック（in_shift の場合のみ）
        brk = SHIFT_BREAKS.get(shift)
        on_break = False
        if brk:
            b_start, b_end = brk[0] * 60, brk[1] * 60
            if b_start < s_end and s_start < b_end:
                on_break = True
        if on_break:
            avail_break.append(nm)
        else:
            avail_active.append(nm)

    n_active = len(avail_active)
    n_total  = n_active + len(avail_break)

    # ── ピット/代車 使用数チェック
    pits_used = 0
    _loaner_cars_set    = set()   # 代車車種が指定されている予約
    _unspecified_loaners = 0      # 代車車種未指定の予約数

    if not active_df.empty:
        for _, row in active_df[active_df["date"] == date_str].iterrows():
            t = row.get("title",""); ts = row.get("time","")
            _sb_loaner_v = str(row.get("sb_want_loaner", ""))
            _uses_loaner = (_sb_loaner_v == "1") if _sb_loaner_v in ("0","1") else _sb_title_uses_loaner(t)
            if _uses_loaner:
                _lc = str(row.get("loaner_car", "")).strip()
                if _lc in LOANER_CARS:
                    _loaner_cars_set.add(_lc)
                else:
                    _unspecified_loaners += 1
            # ピット：時間帯ベース
            try:
                eh2, em2 = map(int, ts.split(":"))
            except Exception:
                continue
            e_start = eh2 * 60 + em2
            _sb_dur_v = str(row.get("sb_duration", ""))
            _dur_v = int(_sb_dur_v) if _sb_dur_v.isdigit() else _sb_estimate_dur(t)
            e_end = e_start + _dur_v
            _sb_pit_v = str(row.get("sb_use_pit", ""))
            _uses_pit = (_sb_pit_v == "1") if _sb_pit_v in ("0","1") else _sb_title_uses_pit(t)
            if _uses_pit and s_start < e_end and s_end > e_start:
                pits_used += 1

    # 代車空き台数を算出
    if requested_loaner_car and requested_loaner_car in LOANER_CARS:
        # 特定の車種を指定：その車種が使用中かのみチェック
        loaners_used = MAX_LOANERS if requested_loaner_car in _loaner_cars_set else 0
    else:
        loaners_used = len(_loaner_cars_set) + _unspecified_loaners

    pit_ok       = pits_used < MAX_PITS
    loaners_left = MAX_LOANERS - loaners_used

    all_on_break = (n_active == 0 and len(avail_break) > 0)

    # ── × 判定（全員休憩中の場合は × にせず △ へ）
    if n_total == 0:
        # 通常スタッフは不在だが、残業なら対応できるスタッフがいる場合 → △（残業）
        if avail_overtime:
            _ot_resource_ok = (
                pit_ok or not pit_req or pit_flex
            ) and (
                not loaner_req or loaners_left > 0
            )
            if _ot_resource_ok:
                _ot_names = "・".join(avail_overtime[:3])
                _ot_mins  = s_end - min(
                    SHIFT_HOURS[STAFF_DEFAULT_SHIFT[nm]][1] * 60
                    for nm in avail_overtime
                )
                return "△", [
                    f"⚠️ 残業対応: この時間はスタッフの残業が発生する可能性があります。"
                    f"対応可能スタッフ：{_ot_names}（定時を最大{_ot_mins}分超える見込み）。"
                    "予約を受け付ける場合は現場スタッフへ確認の上、判断してください。"
                ]
        return "×", ["対応できるスタッフが0名です（全員休み・スキル不一致）"]
    if not all_on_break:
        if pit_req and not pit_flex and not pit_ok:
            return "×", ["ピット（リフト）が満車です。この作業にはピットが必須です。"]
        if loaner_req and loaners_left <= 0:
            return "×", [f"代車が全台（{MAX_LOANERS}台）出払っています。車検には代車が必須です。"]

    # ── △ 判定
    reasons = []

    # 全員休憩中 → 調整可能な △
    if all_on_break:
        names_str = "・".join(avail_break[:3])
        reasons.append(
            f"※ この時間帯はスタッフの予定休憩時間と重複しています（{names_str}）。"
            "予約を受け付ける場合は、休憩時間を前後にシフトできるか、"
            "現場スタッフと調整を行ってください。"
        )
        if pit_req and not pit_flex and not pit_ok:
            reasons.append("※ さらにピット（リフト）も満車のため、2重の制約があります。")
        if loaner_req and loaners_left <= 0:
            reasons.append(f"※ さらに代車も全台（{MAX_LOANERS}台）出払っています。")
        return "△", reasons

    if pit_req and pit_flex and not pit_ok:
        if "オイル" in work_type:
            reasons.append(
                "※ この時間帯はピット満車のため、屋外でのオイル交換となります。"
                "お客様に了承をいただいてください。"
            )
        else:
            reasons.append(
                "※ この時間帯はピット満車のため、屋外でのキーパーコーティング施工となります。"
                "天候・状況を確認の上、お客様にご了承いただいてください。"
            )
    if work_type == "車検見積もり":
        pro_on = [s for s in _PRO
                  if STAFF_DEFAULT_SHIFT.get(s) and
                  SHIFT_HOURS[STAFF_DEFAULT_SHIFT[s]][0]*60 <= s_start and
                  s_end <= SHIFT_HOURS[STAFF_DEFAULT_SHIFT[s]][1]*60]
        if len(pro_on) == 1:
            reasons.append(
                f"※ {pro_on[0]}の1人体制です（熟練枠）。突発的な対応で時間が前後する"
                "可能性があります。お客様にご了承いただいてください。"
            )
    if loaner_req and loaners_left == 1:
        reasons.append(
            f"※ 代車が残り1台となっています（本日 {loaners_used}台使用中）。"
            "代車確保の確認をしてから予約を確定してください。"
        )
    if reasons:
        return "△", reasons

    return ("◎" if n_active >= 2 else "◯"), []


# ── ホワイトボード風予定ボード（既存機能） ─────────────────────────────────────
def render_schedule_board_tab():
    today     = datetime.now().date()
    week_off  = st.session_state.week_offset
    monday    = today - timedelta(days=today.weekday()) + timedelta(weeks=week_off)
    week_days = [monday + timedelta(days=d) for d in range(7)]
    sched_df  = load_schedule()

    hc1, hc2, hc3, hc4, hc5, hc6 = st.columns([2, 0.7, 0.7, 1.2, 1.2, 1.2])
    with hc1:
        st.markdown(f"<div style='font-size:.98rem;font-weight:800;color:#f5f5f5'>"
                    f"📅 予定ボード　<span style='font-size:.78rem;color:#aaa;font-weight:400'>"
                    f"{monday.strftime('%Y/%m/%d')} 週</span></div>", unsafe_allow_html=True)
    with hc2:
        if st.button("◀ 前週", use_container_width=True, key="week_prev"):
            st.session_state.week_offset -= 1; st.rerun()
    with hc3:
        if st.button("次週 ▶", use_container_width=True, key="week_next"):
            st.session_state.week_offset += 1; st.rerun()
    with hc4:
        if st.button("今週に戻る", use_container_width=True, key="week_reset"):
            st.session_state.week_offset = 0; st.rerun()
    with hc5:
        if st.button("➕ 予定を追加", use_container_width=True, key="sched_add"):
            st.session_state["show_wb_quick_add"]  = True
            st.session_state["show_sched_history"] = False
    with hc6:
        _hist_label = "📂 カレンダーへ" if st.session_state.get("show_sched_history") else "📋 履歴"
        if st.button(_hist_label, use_container_width=True, key="sched_hist"):
            st.session_state.show_sched_history = not st.session_state.get("show_sched_history", False)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    if st.session_state.get("show_sched_history"):
        # ══════════════════════════════════════════════════════════════════════
        #  🏪 店舗アクティビティ・センター
        # ══════════════════════════════════════════════════════════════════════
        st.markdown(
            "<div style='font-size:1.05rem;font-weight:800;color:#f0f0f0;"
            "letter-spacing:.04em;margin-bottom:14px'>🏪 店舗アクティビティ・センター</div>",
            unsafe_allow_html=True,
        )

        _ac_left, _ac_right = st.columns([1, 1], gap="large")

        # ── セクション①：操作ログ タイムライン ─────────────────────────────
        with _ac_left:
            st.markdown(
                "<div style='font-size:.82rem;font-weight:700;color:#90caf9;"
                "text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px'>"
                "📋 最近の操作ログ</div>",
                unsafe_allow_html=True,
            )
            _ACTION_ICON = {
                "新規登録": ("📌", "#4caf50", "#0d1f0d"),
                "更新":     ("✏️",  "#29b6f6", "#0a1a22"),
                "削除":     ("🗑️", "#ef5350", "#1f0a0a"),
                "復元":     ("♻️", "#66bb6a", "#0d1a0d"),
                "完全削除": ("💥", "#ff7043", "#1f100a"),
            }
            if CHANGE_LOG_CSV.exists():
                _log_df = pd.read_csv(CHANGE_LOG_CSV, dtype=str).fillna("")
                _log_df = _log_df.tail(50).iloc[::-1].reset_index(drop=True)
                if _log_df.empty:
                    st.caption("操作履歴はまだありません。")
                else:
                    for _, _lr in _log_df.iterrows():
                        _act  = str(_lr.get("action", ""))
                        _ico, _col, _bg = _ACTION_ICON.get(_act, ("🔹", "#aaa", "#1a1a2e"))
                        _ts   = str(_lr.get("timestamp", ""))[:16].replace("-", "/")
                        _d    = str(_lr.get("date", ""))
                        _t    = str(_lr.get("time", ""))
                        _m    = str(_lr.get("memo", ""))
                        _m15  = (_m[:20] + "…") if len(_m) > 20 else _m
                        st.markdown(
                            f"<div style='background:{_bg};border-left:3px solid {_col};"
                            f"border-radius:6px;padding:7px 10px;margin-bottom:5px;"
                            f"font-size:.78rem;line-height:1.55'>"
                            f"<span style='color:#aaa;font-size:.72rem'>🕒 {_ts}</span><br>"
                            f"<span style='color:{_col};font-weight:700'>{_ico} 【{_act}】</span>"
                            f"<span style='color:#ddd'>&nbsp;{_d} {_t}</span><br>"
                            f"<span style='color:#bbb'>{_m15}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
            else:
                st.caption("操作履歴はまだありません。")

        # ── セクション②：アーカイブ・ゴミ箱 ────────────────────────────────
        with _ac_right:
            st.markdown(
                "<div style='font-size:.82rem;font-weight:700;color:#ffb74d;"
                "text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px'>"
                "📦 アーカイブ・ごみ箱</div>",
                unsafe_allow_html=True,
            )
            trash_df = (sched_df[sched_df["status"].isin(["ゴミ箱", "完了"])].copy()
                        if not sched_df.empty else pd.DataFrame())
            trash_df = (trash_df.sort_values("date", ascending=False)
                        if not trash_df.empty else trash_df)
            if trash_df.empty:
                st.caption("ゴミ箱は空です。")
            else:
                for _, tr in trash_df.iterrows():
                    _tr_memo = str(tr.get("detail", ""))
                    _tr_name = str(tr.get("cust_name", ""))
                    _tr_m18  = (_tr_memo[:18] + "…") if len(_tr_memo) > 18 else _tr_memo
                    _primary = _tr_name if _tr_name else (_tr_m18 if _tr_m18 else "─")
                    _sub     = _tr_m18 if (_tr_name and _tr_m18) else ""
                    _card_lbl = (
                        f"🗓 {tr['date']} {tr['time']}\n"
                        f"{_primary}"
                        + (f"\n📝 {_sub}" if _sub else "")
                    )
                    st.button(
                        _card_lbl,
                        key=f"arc_card_{tr['id']}",
                        use_container_width=True,
                        on_click=_on_archive_card_click,
                        args=(str(tr["id"]),),
                    )
    else:
        day_cols = st.columns(7, gap="small")
        for dc, day in zip(day_cols, week_days):
            is_today = (day == today)
            is_past  = (day < today)
            dow_jp   = DAYS_JP[day.weekday()]
            hdr_cls  = "sched-col-today" if is_today else ("sched-col-past" if is_past else "sched-col-normal")
            day_str  = day.strftime("%Y/%m/%d")
            day_items = (sched_df[(sched_df["date"] == day_str) & (sched_df["status"] == "予定")]
                         if not sched_df.empty else pd.DataFrame())
            with dc:
                st.markdown(
                    f"<div class='sched-col-header {hdr_cls}'>{dow_jp}<br>"
                    f"<span style='font-size:.75rem'>{day.strftime('%m/%d')}</span></div>",
                    unsafe_allow_html=True)
                if day_items.empty:
                    st.markdown("<div style='font-size:.7rem;color:#ddd;text-align:center;padding:6px 0'>─</div>",
                                unsafe_allow_html=True)
                else:
                    for _, si in day_items.iterrows():
                        plate_s  = f"#{si['plate_num']}" if si["plate_num"] else ""
                        _name_s  = si.get("cust_name", "")
                        _car_s   = si.get("cust_car", "")
                        _staff_s = si.get("sb_staff", "")
                        _memo_s  = str(si.get("detail", ""))
                        _title_s = str(si.get("title", ""))
                        # カードボタンのラベル（複数行）
                        # title が空 or「その他」の場合は備考の冒頭15文字を主情報として浮き出す
                        if _title_s and _title_s != "その他":
                            _first_info = _fmt_title(_title_s, _memo_s)
                        else:
                            _first_info = (_memo_s[:15] + "…") if len(_memo_s) > 15 else _memo_s
                        _lns = [f"📌 {si['time']}　{_first_info}"] if _first_info else [f"📌 {si['time']}"]
                        _l2  = " ".join(filter(None, [_name_s, plate_s]))
                        if _l2:      _lns.append(f"  {_l2}")
                        if _car_s:   _lns.append(f"  🚗 {_car_s}")
                        if _staff_s: _lns.append(f"  👔 {_staff_s}")
                        _pre_loaner_v = str(si.get("sb_want_loaner", ""))
                        _pre_want_v   = (_pre_loaner_v == "1") if _pre_loaner_v in ("0","1") else False
                        st.button(
                            "\n".join(_lns), key=f"wb_card_{si['id']}",
                            use_container_width=True,
                            on_click=_on_wb_card_click,
                            args=({
                                "id":          si["id"],
                                "date":        si["date"],
                                "time":        si["time"],
                                "title":       si["title"],
                                "detail":      si.get("detail", ""),
                                "plate_num":   si.get("plate_num", ""),
                                "cust_type":   si.get("cust_type", ""),
                                "cust_name":   si.get("cust_name", ""),
                                "cust_contact":si.get("cust_contact", ""),
                                "cust_car":    si.get("cust_car", ""),
                                "loaner_car":  si.get("loaner_car", ""),
                                "sb_staff":    si.get("sb_staff", ""),
                                "want_loaner": _pre_want_v,
                                "sb_duration": si.get("sb_duration", ""),
                                "sb_use_pit":  si.get("sb_use_pit", ""),
                            },),
                        )

    # ── ホワイトボードカードボタンのスタイリング + グリッド横スクロール（JS確実版）
    components.html(
        "<script>"
        "(function(){"
        # parent document access（same-origin iframe または inline）
        "  var pd=document;"
        "  try{if(window.parent&&window.parent!==window)pd=window.parent.document;}catch(e){}"
        "  function paintWB(){"
        # カードボタンをスタイリング
        "    pd.querySelectorAll('button').forEach(function(btn){"
        "      var t=btn.textContent.trim();"
        "      if(t.startsWith('\U0001F4CC')){"
        "        btn.style.setProperty('background','#1a2535','important');"
        "        btn.style.setProperty('border','1px solid #2e4a6a','important');"
        "        btn.style.setProperty('border-radius','8px','important');"
        "        btn.style.setProperty('text-align','left','important');"
        "        btn.style.setProperty('white-space','pre-line','important');"
        "        btn.style.setProperty('color','#e8eaf0','important');"
        "        btn.style.setProperty('font-size','.79rem','important');"
        "        btn.style.setProperty('line-height','1.65','important');"
        "        btn.style.setProperty('padding','8px 10px','important');"
        "        btn.style.setProperty('height','auto','important');"
        "        btn.style.setProperty('min-height','44px','important');"
        "      }"
        "    });"
        # ホワイトボード7列: 単一行HBをそのままスクロール容器にする（行が1本なのでズレなし）
        "    pd.querySelectorAll('[data-testid=\"stHorizontalBlock\"]').forEach(function(hb){"
        "      var cols=Array.from(hb.children).filter(function(c){return c.getAttribute('data-testid')==='column';});"
        "      if(cols.length===7){"
        "        var p=hb.parentElement;"
        "        while(p&&p!==pd.body){"
        "          var ptid=p.getAttribute('data-testid');"
        "          if(ptid==='stVerticalBlock'||ptid==='stMain'||"
        "             ptid==='stAppViewContainer'||ptid==='stMainBlockContainer'){"
        "            p.style.setProperty('overflow-x','visible','important');"
        "          }"
        "          p=p.parentElement;"
        "        }"
        "        hb.style.setProperty('display','flex','important');"
        "        hb.style.setProperty('flex-wrap','nowrap','important');"
        "        hb.style.setProperty('overflow-x','scroll','important');"
        "        hb.style.setProperty('-webkit-overflow-scrolling','touch','important');"
        "        hb.style.setProperty('gap','2px','important');"
        "        hb.style.setProperty('width','100%','important');"
        "        hb.style.setProperty('min-width','0','important');"
        "        cols.forEach(function(col){"
        "          col.style.setProperty('flex','0 0 260px','important');"
        "          col.style.setProperty('min-width','260px','important');"
        "          col.style.setProperty('width','260px','important');"
        "          col.style.setProperty('flex-shrink','0','important');"
        "        });"
        "      }"
        "    });"
        "  }"
        "  paintWB();"
        "  new MutationObserver(paintWB).observe(pd.body||document.body,{childList:true,subtree:true});"
        "})();"
        "</script>",
        height=0,
    )


# ── グリッドテーブルビルダー（<a href> リンク方式） ─────────────────────────────
def _build_sb_html_table(grid, week_days, today_date, work, dur, use_pit, want_loaner, req_loaner_car, week_off=0):
    import html as _h
    _CLS = {"◎": "sym-ok2", "○": "sym-ok1", "△": "sym-warn", "×": "sym-ng"}
    rows = ['<div class="scrollable-wrapper"><table class="grid-table-standard"><thead><tr>',
            '<th class="label-col">時刻</th>']
    for di, day in enumerate(week_days):
        dow = DAYS_JP[day.weekday()]
        cls = ' class="today-col"' if day == today_date else ""
        rows.append(f'<th{cls}>{_h.escape(dow)}<br><small>{day.strftime("%m/%d")}</small></th>')
    rows.append("</tr></thead><tbody>")
    for si, (hh, mm) in enumerate(SB_TIME_SLOTS):
        rows.append("<tr>")
        rows.append(f'<td class="label-col">{hh:02d}:{mm:02d}</td>')
        for di in range(7):
            sym, rsns = grid[di][si]
            cls = _CLS.get(sym, "")
            rows.append(f'<td class="{cls}">{_h.escape(sym)}</td>')
        rows.append("</tr>")
    rows.append("</tbody></table></div>")
    return "".join(rows)


def _build_lm_html_table(lm_rows):
    import html as _h
    parts = ['<div class="scrollable-wrapper"><table class="grid-table-standard"><thead><tr>',
             '<th class="label-col">日付</th>']
    for car in LOANER_CARS:
        parts.append(f"<th>🚗 {_h.escape(car)}</th>")
    parts.append("</tr></thead><tbody>")
    for rd in lm_rows:
        parts.append("<tr>")
        td_cls = "label-col today-row" if rd["is_today"] else "label-col"
        parts.append(f'<td class="{td_cls}">{_h.escape(rd["day_label"])}</td>')
        for car in LOANER_CARS:
            cell = rd[car]
            if cell == "◯":
                parts.append('<td class="sym-loaner-ok">◯</td>')
            else:
                safe = _h.escape(cell).replace("\n", "<br>")
                parts.append(f'<td class="sym-loaner-booked">{safe}</td>')
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


# ── 代車貸出管理表タブ ────────────────────────────────────────────────────────
def render_loaner_board_tab():
    import calendar
    today     = datetime.now().date()
    month_off = st.session_state.get("lm_month_off", 0)

    # 表示月の計算
    _y = today.year + (today.month - 1 + month_off) // 12
    _m = (today.month - 1 + month_off) % 12 + 1
    _num_days = calendar.monthrange(_y, _m)[1]

    st.markdown(
        f"<div style='font-size:.98rem;font-weight:800;color:#f5f5f5;margin-bottom:6px'>"
        f"🚙 代車貸出管理表　<span style='font-size:.78rem;color:#aaa'>{_y}年{_m}月</span></div>",
        unsafe_allow_html=True)
    hm2, hm3, hm4 = st.columns(3)
    with hm2:
        if st.button("◀ 前月", use_container_width=True, key="lm_prev"):
            st.session_state["lm_month_off"] = month_off - 1; st.rerun()
    with hm3:
        if st.button("次月 ▶", use_container_width=True, key="lm_next"):
            st.session_state["lm_month_off"] = month_off + 1; st.rerun()
    with hm4:
        if st.button("今月に戻る", use_container_width=True, key="lm_reset"):
            st.session_state["lm_month_off"] = 0; st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    sdf    = load_schedule()
    active = (sdf[~sdf["status"].isin(["ゴミ箱","完了"])].copy()
              if not sdf.empty else pd.DataFrame())

    # マトリクスデータ構築
    rows = []
    for day in range(1, _num_days + 1):
        date_obj = datetime(_y, _m, day).date()
        date_str = date_obj.strftime("%Y/%m/%d")
        dow      = DAYS_JP[date_obj.weekday()]
        is_today = (date_obj == today)
        day_label = f"{'★' if is_today else ''}{_m}/{day:02d}({dow})"

        row_data = {"date_str": date_str, "day_label": day_label, "is_today": is_today, "day": day}
        for car in LOANER_CARS:
            cell = "◯"
            if not active.empty:
                car_rows = active[
                    (active["date"] == date_str) &
                    (active["sb_want_loaner"] == "1") &
                    (active["loaner_car"] == car)
                ]
                if not car_rows.empty:
                    b       = car_rows.iloc[0]
                    _cn     = str(b.get("cust_name", "")).strip()
                    _detail = str(b.get("detail", "")).strip()
                    _memo7  = (_detail[:7] + "…") if len(_detail) > 7 else _detail
                    _time   = str(b.get("time", "")).strip()
                    _label  = _cn + "様" if _cn else (_memo7 if _memo7 else "予約")
                    _sub    = _memo7 if (_cn and _memo7) else ""
                    cell    = f"{_label}\n{_sub}" if _sub else _label
                    if _time:
                        cell = f"{_time}\n" + cell
            row_data[car] = cell
        rows.append(row_data)

    # ── グリッド（クリック → リロードなし即時 st.dialog）
    _lm_hdr = st.columns([2] + [3] * len(LOANER_CARS))
    _lm_hdr[0].markdown(
        "<div style='font-size:.7rem;color:#555;padding:2px 0'>日付</div>",
        unsafe_allow_html=True,
    )
    for _ci, _car in enumerate(LOANER_CARS):
        _lm_hdr[_ci + 1].markdown(
            f"<div style='font-size:.72rem;color:#ccc;text-align:center;"
            f"font-weight:700'>🚗 {_car}</div>",
            unsafe_allow_html=True,
        )
    for rd in rows:
        _lm_rc = st.columns([2] + [3] * len(LOANER_CARS))
        _dc = "#60a5fa" if rd["is_today"] else "#888"
        _lm_rc[0].markdown(
            f"<div style='font-size:.7rem;color:{_dc};"
            f"text-align:right;padding-top:4px;padding-right:4px'>{rd['day_label']}</div>",
            unsafe_allow_html=True,
        )
        for _ci, _car in enumerate(LOANER_CARS):
            cell = rd[_car]
            if cell == "◯":
                _lm_rc[_ci + 1].button(
                    "◯",
                    key=f"lm_{rd['date_str']}_{_car}",
                    use_container_width=True,
                    type="primary",
                    on_click=_on_loaner_cell_click,
                    args=(rd["date_str"], _car),
                )
            else:
                _lm_rc[_ci + 1].markdown(
                    f"<div style='font-size:.7rem;color:#f59e0b;background:#2d1800;"
                    f"border-radius:6px;padding:3px 5px;text-align:center;"
                    f"white-space:pre-line;line-height:1.4'>{cell}</div>",
                    unsafe_allow_html=True,
                )


# ── スマート予約タブ（ホットペッパー風） ───────────────────────────────────────
def render_smart_booking_tab():
    today = datetime.now().date()

    # ── 既存予約の変更・キャンセル ──────────────────────────────────────────────
    with st.expander("✏️ 既存予約を修正・キャンセル", expanded=False):
        _sdf_edit = load_schedule()
        _active_edit = (
            _sdf_edit[_sdf_edit["status"] == "予定"].copy()
            if not _sdf_edit.empty else pd.DataFrame(columns=SCHEDULE_COLS)
        )

        _ec1, _ec2 = st.columns([1, 2])
        with _ec1:
            _edit_date = st.date_input("📅 日付", value=today, key="sb_edit_date_picker")
        _edit_date_str = _edit_date.strftime("%Y/%m/%d")

        _day_bookings = (
            _active_edit[_active_edit["date"] == _edit_date_str]
            if not _active_edit.empty else pd.DataFrame()
        )

        if _day_bookings.empty:
            st.info(f"📭 {_edit_date_str} に予約はありません")
        else:
            _bid_list = ["__none__"] + _day_bookings["id"].tolist()
            _bid_labels: dict[str, str] = {"__none__": "（予約を選択してください）"}
            for _, _br in _day_bookings.sort_values("time").iterrows():
                _lbl = f"{_br['time']} {_br['title']}"
                if _br.get("plate_num"):
                    _lbl += f" #{_br['plate_num']}"
                _bid_labels[_br["id"]] = _lbl

            # 日付が変わったら選択リセット（pop は widget 描画前後どちらでも許可されている）
            _cur_sel = st.session_state.get("sb_edit_booking_select", "__none__")
            if _cur_sel not in _bid_list:
                st.session_state.pop("sb_edit_booking_select", None)
                st.session_state["sb_edit_selected_id"] = None

            st.selectbox(
                "📋 変更する予約を選択",
                _bid_list,
                format_func=lambda x: _bid_labels.get(x, x),
                key="sb_edit_booking_select",
                on_change=_on_sb_edit_booking_change,
            )

            _edit_id = st.session_state.get("sb_edit_selected_id")

            if _edit_id and _edit_id != "__none__":
                _erows = _sdf_edit[_sdf_edit["id"] == _edit_id]
                if not _erows.empty:
                    _er = _erows.iloc[0]

                    st.markdown(f"""
<div style="background:#1c2a3a;border:1px solid #2e4a6a;border-radius:10px;
            padding:10px 14px;margin:8px 0;font-size:.83rem">
  <span style="color:#888">日時：</span>
  <span style="color:#f0f0f0;font-weight:700">{_er['date']} {_er['time']}</span>
  　<span style="color:#888">作業：</span>
  <span style="color:#f0f0f0;font-weight:700">{_er['title']}</span>
  {'　<span style="color:#888">車番：</span><span style="color:#f0f0f0;font-weight:700">#' + _er["plate_num"] + '</span>' if _er.get("plate_num") else ''}
</div>""", unsafe_allow_html=True)

                    # 編集フォーム（各ウィジェットは sb_edit_* キーを持つ）
                    _e_work = st.selectbox(
                        "🔧 作業種類",
                        list(WORK_MATRIX.keys()),
                        key="sb_edit_work_type",
                    )
                    _e_dur = st.slider(
                        "⏱ 所要時間（10分刻み）",
                        min_value=10, max_value=480, step=10,
                        key="sb_edit_duration",
                    )
                    _e_pit = st.checkbox(
                        "🏗 ピット（リフト）を使用する",
                        key="sb_edit_use_pit",
                    )
                    _e_loaner_raw = st.radio(
                        "🚗 代車希望",
                        ["代車不要", "代車を希望する"],
                        horizontal=True,
                        key="sb_edit_want_loaner",
                    )
                    _e_want_loaner = (_e_loaner_raw == "代車を希望する")
                    _e_detail = st.text_area(
                        "💬 詳細メモ",
                        key="sb_edit_detail",
                        height=55,
                    )

                    _btn1, _btn2 = st.columns(2)
                    with _btn1:
                        if st.button("✅ 変更を確定", type="primary",
                                     use_container_width=True, key="sb_edit_confirm"):
                            _idx_e = _sdf_edit.index[_sdf_edit["id"] == _edit_id][0]
                            _sdf_edit.at[_idx_e, "title"]          = _e_work
                            _sdf_edit.at[_idx_e, "sb_duration"]    = str(_e_dur)
                            _sdf_edit.at[_idx_e, "sb_use_pit"]     = "1" if _e_pit else "0"
                            _sdf_edit.at[_idx_e, "sb_want_loaner"] = "1" if _e_want_loaner else "0"
                            _sdf_edit.at[_idx_e, "detail"]         = _e_detail
                            save_schedule(_sdf_edit)
                            st.session_state["sb_edit_selected_id"]  = None
                            st.session_state.pop("sb_edit_booking_select", None)
                            st.session_state["sb_cancel_confirm_id"] = None
                            st.success("✅ 予約を更新しました。グリッドに即時反映されます。")
                            st.rerun()
                    with _btn2:
                        if st.button("🗑️ この予約をキャンセルする",
                                     use_container_width=True, key="sb_cancel_btn"):
                            st.session_state["sb_cancel_confirm_id"] = _edit_id

                    # キャンセル確認UI
                    if st.session_state.get("sb_cancel_confirm_id") == _edit_id:
                        st.markdown("""
<div style="background:#2d0d0d;border:2px solid #ef4444;border-radius:10px;
            padding:12px 14px;margin:8px 0">
  <div style="font-size:.9rem;font-weight:800;color:#f87171;margin-bottom:4px">
    🗑️ 予約キャンセルの確認
  </div>
  <div style="font-size:.82rem;color:#ccc">
    この予約を削除します。代車・ピットのリソースは即座に解放されます。この操作は取り消せません。
  </div>
</div>""", unsafe_allow_html=True)
                        _cc1, _cc2 = st.columns(2)
                        with _cc1:
                            if st.button("🗑️ はい、キャンセルする", type="primary",
                                         use_container_width=True, key="sb_cancel_yes"):
                                _sdf_edit = _sdf_edit[_sdf_edit["id"] != _edit_id].copy()
                                save_schedule(_sdf_edit)
                                st.session_state["sb_edit_selected_id"]  = None
                                st.session_state.pop("sb_edit_booking_select", None)
                                st.session_state["sb_cancel_confirm_id"] = None
                                st.success("✅ 予約をキャンセルしました。リソースが解放されグリッドに反映されます。")
                                st.rerun()
                        with _cc2:
                            if st.button("戻る", use_container_width=True, key="sb_cancel_no"):
                                st.session_state["sb_cancel_confirm_id"] = None
                                st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── コントロール行 1：作業種類 / 2人体制 / 代車希望
    ca, cb, cc = st.columns([3, 2, 3])
    with ca:
        selected_work = st.selectbox("🔧 作業種類", list(WORK_MATRIX.keys()), key="sb_work_type")
    work = WORK_MATRIX[selected_work]
    with cb:
        two_person = False
        if work.get("2p"):
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            two_person = st.checkbox("👥 2人体制（時間1/2）", key="sb_two_person")
    with cc:
        want_loaner_raw = st.radio(
            "🚗 代車希望",
            ["代車不要", "代車を希望する"],
            horizontal=True,
            key="sb_want_loaner",
        )
        want_loaner = (want_loaner_raw == "代車を希望する")

    req_loaner_car = ""
    if want_loaner:
        _lcar_opts = ["(指定なし)"] + LOANER_CARS
        _sel_lcar  = st.selectbox(
            "🚙 代車車種（指定する場合）", _lcar_opts, key="sb_req_loaner_car"
        )
        req_loaner_car = "" if _sel_lcar == "(指定なし)" else _sel_lcar

    # ── コントロール行 2：所要時間スライダー
    base_dur  = work["duration"] // 2 if two_person else work["duration"]
    slider_key = f"sb_dur_{selected_work}_{'2p' if two_person else '1p'}"
    duration = st.slider(
        f"⏱ 所要時間（10分刻み・デフォルト {base_dur}分）",
        min_value=10, max_value=480, value=base_dur, step=10,
        key=slider_key,
    )
    # ── ピット使用チェックボックス（全作業種類共通・デフォルトは作業種類に連動）
    use_pit = st.checkbox(
        "🏗 ピット（リフト）を使用する",
        value=work["pit"],
        key=f"sb_pit_{selected_work}",
    )
    work = dict(work, pit=use_pit, flex=work.get("flex", False) if use_pit else False)

    _orig_pit = WORK_MATRIX[selected_work]["pit"]
    if work["pit"]:
        pit_info = "🏗 ピット" + ("（屋外可）" if work["flex"] else "必須")
    elif _orig_pit:
        pit_info = "🏗 ピット不使用に変更（屋外 / 店頭対応）"
    else:
        pit_info = ""
    loaner_info = "🚗 代車必要" if (want_loaner or work.get("loaner")) else ""
    info_parts = [x for x in [f"✅ {duration}分でグリッド計算中", pit_info, loaner_info] if x]
    st.markdown(
        f"<div style='font-size:.74rem;color:#888;margin-top:-6px'>{'　'.join(info_parts)}</div>",
        unsafe_allow_html=True,
    )

    # ── 週ナビ
    wk1, wk2, wk3 = st.columns(3)
    with wk1:
        if st.button("◀ 前週", key="sb_prev"):
            st.session_state["sb_week_off"] = st.session_state.get("sb_week_off", 0) - 1
            st.session_state.pop("sb_sel_di", None)
            st.session_state.pop("sb_sel_si", None)
    with wk2:
        if st.button("次週 ▶", key="sb_next"):
            st.session_state["sb_week_off"] = st.session_state.get("sb_week_off", 0) + 1
            st.session_state.pop("sb_sel_di", None)
            st.session_state.pop("sb_sel_si", None)
    with wk3:
        if st.button("今週", key="sb_today"):
            st.session_state["sb_week_off"] = 0
            st.session_state.pop("sb_sel_di", None)
            st.session_state.pop("sb_sel_si", None)

    week_off  = st.session_state.get("sb_week_off", 0)
    monday    = today - timedelta(days=today.weekday()) + timedelta(weeks=week_off)
    week_days = [monday + timedelta(days=d) for d in range(7)]

    sched_df  = load_schedule()
    active_df = sched_df[~sched_df["status"].isin(["ゴミ箱","完了"])].copy() if not sched_df.empty else pd.DataFrame()

    # ── グリッド計算
    grid = []
    for day in week_days:
        row = []
        for h, m in SB_TIME_SLOTS:
            sym, rsns = _sb_compute_slot(
                day, h, m, selected_work, duration, work, active_df,
                want_loaner=want_loaner,
                requested_loaner_car=req_loaner_car,
            )
            row.append((sym, rsns))
        grid.append(row)

    # ── グリッド（クリック → リロードなし即時 st.dialog）
    _sb_hdr = st.columns([1] + [2] * 7)
    _sb_hdr[0].markdown(
        "<div style='font-size:.7rem;color:#555;text-align:center;padding:2px 0'>時刻</div>",
        unsafe_allow_html=True,
    )
    for _di, _day in enumerate(week_days):
        _hc = "#60a5fa" if _day == today else "#999"
        _sb_hdr[_di + 1].markdown(
            f"<div style='font-size:.72rem;color:{_hc};text-align:center;"
            f"font-weight:700;line-height:1.4'>"
            f"{DAYS_JP[_day.weekday()]}<br>"
            f"<span style='font-size:.65rem'>{_day.strftime('%m/%d')}</span></div>",
            unsafe_allow_html=True,
        )
    for si, (hh, mm) in enumerate(SB_TIME_SLOTS):
        _tstr = f"{hh:02d}:{mm:02d}"
        if all(grid[_d][si][0] == "×" for _d in range(7)):
            continue
        _rc = st.columns([1] + [2] * 7)
        _rc[0].markdown(
            f"<div style='font-size:.7rem;color:#888;text-align:right;"
            f"padding:8px 4px 0 0'>{_tstr}</div>",
            unsafe_allow_html=True,
        )
        for _di, _day in enumerate(week_days):
            _sym, _rsns = grid[_di][si]
            if _sym == "×":
                _rc[_di + 1].markdown(
                    "<div style='text-align:center;color:#aaa;"
                    "background:#222;border-radius:6px;"
                    "padding:4px 0;font-size:.85rem'>×</div>",
                    unsafe_allow_html=True,
                )
            else:
                _rc[_di + 1].button(
                    _sym,
                    key=f"sb_{_di}_{si}",
                    use_container_width=True,
                    type=("primary" if _sym in ("◎", "○") else "secondary"),
                    on_click=_on_cell_click,
                    args=(_di, si, _day.strftime("%Y/%m/%d"), _tstr,
                          selected_work, duration, use_pit, want_loaner,
                          req_loaner_car, _sym, _rsns or []),
                )


# ── 予定編集ダイアログ ────────────────────────────────────────────────────────
@st.dialog("📅 予定を編集")
def _edit_sched_dialog():
    sid = st.session_state.get("edit_sched_id", "")
    if not sid:
        return
    sdf = load_schedule()
    rows = sdf[sdf["id"] == sid]
    if rows.empty:
        st.warning("予定データが見つかりません。")
        if st.button("閉じる", key="dlg_notfound_close"):
            st.session_state["edit_sched_id"] = None
            st.rerun()
        return
    si = rows.iloc[0]

    # ── 編集フォーム ───────────────────────────────────────────────────────
    ef1, ef2 = st.columns(2)
    with ef1: ef_date  = st.text_input("📅 日付", value=si["date"])
    with ef2: ef_time  = st.text_input("⏰ 時間", value=si["time"])
    ef3, ef4 = st.columns(2)
    with ef3: ef_title = st.text_input("📝 タイトル", value=si["title"])
    with ef4: ef_plate = st.text_input("🚗 車番（任意）", value=si["plate_num"], max_chars=4)
    _ct_idx = CUST_TYPE_OPTIONS.index(si["cust_type"]) if si["cust_type"] in CUST_TYPE_OPTIONS else 0
    ef_ctype  = st.selectbox("👤 種別", CUST_TYPE_OPTIONS, index=_ct_idx)
    ef_detail = st.text_area("💬 詳細メモ", value=si["detail"], height=70)

    st.markdown("<hr style='border:none;border-top:1px solid #333;margin:10px 0'>",
                unsafe_allow_html=True)

    # ── アクションボタン行1: 保存 + 来店記録反映 ──────────────────────────
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💾 変更を保存", type="primary",
                     use_container_width=True, key="dlg_save"):
            idx = sdf.index[sdf["id"] == sid][0]
            sdf.at[idx, "date"]      = ef_date
            sdf.at[idx, "time"]      = ef_time
            sdf.at[idx, "plate_num"] = ef_plate
            sdf.at[idx, "title"]     = ef_title
            sdf.at[idx, "cust_type"] = ef_ctype if ef_ctype != "なし" else ""
            sdf.at[idx, "detail"]    = ef_detail
            save_schedule(sdf)
            st.session_state["edit_sched_id"] = None
            st.rerun()
    with b2:
        if st.button("🧾 来店記録に反映", use_container_width=True, key="dlg_to_record"):
            _pur = ef_title if ef_title in PURPOSE_OPTIONS else PURPOSE_OPTIONS[0]
            st.session_state["is_duplicate"]   = True
            st.session_state["duplicate_data"] = {
                "purpose":     _pur,
                "cust_type":   ef_ctype if ef_ctype in CUST_TYPE_OPTIONS else "一般",
                "plate_area":  "", "plate_3digit": "", "plate_kana": "",
                "plate_num":   ef_plate,
                "maker":       "", "car_model":   "", "car_size": "", "color": "",
                "age":         "", "gender":      "",
                "tire_size":   "", "tire_size_num": "", "tire_year": "",
                "tire_maker":  "", "tire_product": "",
                "memo":        ef_detail,
            }
            st.session_state["nr_initialized"]  = False
            st.session_state["edit_sched_id"]   = None
            st.session_state["mode"] = "new_record"
            st.rerun()

    # ── アクションボタン行2: ゴミ箱（全幅）────────────────────────────────
    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)
    if st.button("🗑️ 予定をゴミ箱へ（非表示・アーカイブ）",
                 use_container_width=True, key="dlg_trash"):
        idx = sdf.index[sdf["id"] == sid][0]
        sdf.at[idx, "status"] = "ゴミ箱"
        save_schedule(sdf)
        st.session_state["edit_sched_id"] = None
        st.rerun()


# ── アーカイブ詳細ダイアログ（復元・完全削除） ─────────────────────────────────
@st.dialog("📦 アーカイブ詳細", width="large")
def _archive_detail_dialog():
    """ゴミ箱内の予約をフル形式で表示し、清書して復元するか完全削除するか選べるダイアログ。"""
    sel_id = st.session_state.get("archive_sel_id", "")

    # 初回レンダリング時にCSVから注入する（コールバックタイミング問題を回避）
    if st.session_state.get("_arc_needs_init", False):
        sdf = load_schedule()
        mask = sdf["id"] == sel_id
        if mask.any():
            row = sdf.loc[mask].iloc[0]
            import math as _math
            pf_init = {
                k: ("" if isinstance(v, float) and _math.isnan(v) else str(v))
                for k, v in row.to_dict().items()
            }
            pf_init["want_loaner"] = (pf_init.get("sb_want_loaner", "0") == "1")
            _inject_dialog_state_edit(pf_init)
            st.session_state["uf_prefill"] = pf_init
        st.session_state["_arc_needs_init"] = False

    pf     = st.session_state.get("uf_prefill", {})

    # ─ ステータスバッジ ───────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:#2a1f0a;border:1px solid #5a3e10;border-radius:6px;"
        "padding:5px 12px;margin-bottom:14px;font-size:.78rem;color:#f5c842'>"
        "📦 このデータはゴミ箱に入っています。内容を確認・清書して復元するか、完全に削除してください。"
        "</div>",
        unsafe_allow_html=True,
    )

    # ─ 氏名 ────────────────────────────────────────────────────────────────
    st.markdown("<div style='font-size:.72rem;color:#aaa;margin-bottom:2px'>👤 お名前</div>",
                unsafe_allow_html=True)
    uf_name = st.text_input("お名前", placeholder="山田 太郎",
                             label_visibility="collapsed", key="uf_name")
    st.markdown(
        f"<div style='font-size:1.4rem;font-weight:900;color:#f0f0f0;"
        f"min-height:1.8rem;margin:-4px 0 10px'>{uf_name or '─'}</div>",
        unsafe_allow_html=True)

    # ─ 車種 ────────────────────────────────────────────────────────────────
    uf_car_type = st.text_input("🚗 車種", placeholder="プリウス / N-BOX など",
                                 key="uf_car_type")

    # ─ 日時 ────────────────────────────────────────────────────────────────
    _dc1, _dc2 = st.columns(2)
    with _dc1: uf_date = st.text_input("📅 日付", key="uf_date")
    with _dc2: uf_time = st.text_input("⏰ 時間", placeholder="10:00", key="uf_time")

    # ─ 作業内容 ─────────────────────────────────────────────────────────────
    _wk = list(WORK_MATRIX.keys())
    uf_job_type = st.selectbox("🔧 作業内容", _wk, key="uf_job_type")

    # ─ 所要時間・ピット ─────────────────────────────────────────────────────
    _ud1, _ud2 = st.columns([3, 1])
    with _ud1:
        uf_duration = st.slider("⏱ 所要時間（分）", min_value=10, max_value=480,
                                 step=10, key="uf_duration")
    with _ud2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        uf_pit_required = st.checkbox("🏗 ピット", key="uf_pit_required")

    # ─ 連絡先 ──────────────────────────────────────────────────────────────
    uf_phone = st.text_input("📞 連絡先", placeholder="090-XXXX-XXXX", key="uf_phone")

    # ─ 備考 ────────────────────────────────────────────────────────────────
    uf_memo = st.text_area(
        "📝 備考（お客様メモ・特記事項）",
        height=180, key="uf_memo",
        placeholder="ETCセットアップあり\n次回タイヤ交換も検討中",
    )

    # ─ 代車有無 ─────────────────────────────────────────────────────────────
    uf_subcar_needed_raw = st.radio(
        "🚙 代車", ["代車不要", "代車を希望する"],
        horizontal=True, key="uf_subcar_needed",
    )
    uf_want_subcar = (uf_subcar_needed_raw == "代車を希望する")
    uf_subcar_type = ""
    if uf_want_subcar:
        _lcars = ["(未選択)"] + LOANER_CARS
        _sel_lc = st.selectbox("🚙 代車車種", _lcars, key="uf_subcar_type")
        uf_subcar_type = "" if _sel_lc == "(未選択)" else _sel_lc

    # ─ 担当スタッフ ─────────────────────────────────────────────────────────
    _sel_staff = st.selectbox("👔 担当スタッフ", STAFF_OPTIONS, key="uf_staff")
    uf_staff = "" if _sel_staff == "(未選択)" else _sel_staff

    st.markdown("<hr style='border:none;border-top:1px solid #333;margin:14px 0'>",
                unsafe_allow_html=True)

    # ─ 復元ボタン ────────────────────────────────────────────────────────────
    if st.button("♻️ カレンダーに復元する（清書して復元）", type="primary",
                 use_container_width=True, key="arc_restore"):
        sdf = load_schedule()
        mask = sdf["id"] == sel_id
        if sel_id and mask.any():
            idx = sdf.index[mask][0]
            sdf.at[idx, "title"]          = uf_job_type
            sdf.at[idx, "date"]           = uf_date
            sdf.at[idx, "time"]           = uf_time
            sdf.at[idx, "detail"]         = uf_memo
            sdf.at[idx, "cust_name"]      = uf_name
            sdf.at[idx, "cust_contact"]   = uf_phone
            sdf.at[idx, "cust_car"]       = uf_car_type
            sdf.at[idx, "loaner_car"]     = uf_subcar_type
            sdf.at[idx, "sb_staff"]       = uf_staff
            sdf.at[idx, "sb_want_loaner"] = "1" if uf_want_subcar else "0"
            sdf.at[idx, "sb_duration"]    = str(uf_duration)
            sdf.at[idx, "sb_use_pit"]     = "1" if uf_pit_required else "0"
            sdf.at[idx, "status"]         = "予定"
            save_schedule(sdf)
            append_change_log("復元", uf_date, uf_time, uf_memo)
        st.session_state["show_sched_history"] = False
        st.session_state["uf_prefill"] = {}
        st.rerun()

    # ─ 完全削除ボタン ─────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
    if st.button("❌ このデータを完全に削除する", type="primary",
                 use_container_width=True, key="arc_perm_del"):
        sdf = load_schedule()
        mask = sdf["id"] == sel_id
        if sel_id and mask.any():
            _del = sdf.loc[mask].iloc[0]
            append_change_log(
                "完全削除",
                str(_del.get("date", "")), str(_del.get("time", "")),
                str(_del.get("detail", "")),
            )
            sdf = sdf[sdf["id"] != sel_id]
            save_schedule(sdf)
        st.session_state["uf_prefill"] = {}
        st.rerun()


# ── ホワイトボード専用・簡易追加フォーム ─────────────────────────────────────
@st.dialog("✏️ 予定を追加", width="small")
def _wb_quick_add_form():
    """日付・時間・備考の3項目だけで素早く予定を追加するメモ帳感覚フォーム。"""
    import datetime as _dt
    _today = _dt.date.today()
    wb_date = st.date_input("📅 日付", value=_today, key="wq_date",
                             format="YYYY/MM/DD")

    # 時間は selectbox で 30 分刻み（リアルタイム重複チェックと相性が良い）
    _time_opts = [f"{h:02d}:{m:02d}" for h in range(7, 20) for m in (0, 30)]
    _default_ti = _time_opts.index("10:00") if "10:00" in _time_opts else 0
    wb_time_str = st.selectbox("⏰ 時間", _time_opts, index=_default_ti, key="wq_time")

    # ── リアルタイム重複チェック ──────────────────────────────────────────────
    _date_str  = wb_date.strftime("%Y/%m/%d")
    _sdf       = load_schedule()
    _active    = _sdf[_sdf["status"] == "予定"]
    _dup       = _active[(_active["date"] == _date_str) & (_active["time"] == wb_time_str)]
    _has_dup   = not _dup.empty
    if _has_dup:
        st.error("⚠️ その日時はすでに予約が入っています。時間を変更してください。")

    wb_memo = st.text_area(
        "📝 メモ（氏名・作業内容・車種など自由記入）",
        height=160, key="wq_memo",
        placeholder="山田様\nタイヤ交換4本\nプリウス\n10:30〜",
    )
    st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
    if st.button("📌 追加する", type="primary", use_container_width=True,
                 key="wq_save", disabled=_has_dup):
        new_s = {
            "id":             str(uuid.uuid4()),
            "date":           _date_str,
            "time":           wb_time_str,
            "title":          "",
            "detail":         wb_memo,
            "status":         "予定",
            "plate_num":      "",
            "cust_type":      "",
            "sb_duration":    "30",
            "sb_use_pit":     "0",
            "sb_want_loaner": "0",
            "cust_name":      "",
            "cust_contact":   "",
            "cust_car":       "",
            "loaner_car":     "",
            "sb_staff":       "",
        }
        save_schedule(pd.concat([_sdf, pd.DataFrame([new_s])], ignore_index=True))
        append_change_log("新規登録", _date_str, wb_time_str, wb_memo)
        st.session_state["booking_saved_success"] = True
        st.rerun()
    if st.button("キャンセル", use_container_width=True, key="wq_cancel"):
        st.rerun()


# ── 残業警告ダイアログ ────────────────────────────────────────────────────────
@st.dialog("⚠️ 残業対応の確認", width="small")
def _overtime_warning_dialog():
    """△セルタップ時の2ステップ確認: 警告 → [はい]で予約フォームへ"""
    st.markdown(
        "<div style='font-size:.95rem;font-weight:700;color:#f59e0b;margin-bottom:10px'>"
        "⚠️ この時間帯の作業はスタッフの残業が発生します。<br>対応を進めますか？"
        "</div>",
        unsafe_allow_html=True,
    )
    rsns = st.session_state.get("overtime_warning_rsns", [])
    if rsns:
        for r in rsns:
            st.markdown(
                f"<div style='font-size:.8rem;color:#aaa;margin-left:8px'>• {r}</div>",
                unsafe_allow_html=True,
            )
    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
    _ow1, _ow2 = st.columns(2)
    with _ow1:
        if st.button("はい", type="primary", use_container_width=True, key="ow_yes"):
            st.session_state["show_booking_dialog"] = True
            st.rerun()
    with _ow2:
        if st.button("キャンセル", use_container_width=True, key="ow_cancel"):
            st.rerun()


# ── 統一予約フォーム（物理の予約用紙を再現） ─────────────────────────────────
@st.dialog("📋 予約フォーム", width="large")
def _unified_booking_form():
    mode = st.session_state.get("uf_mode", "new")
    pf   = st.session_state.get("uf_prefill", {})

    # ─ Row 1: 名前（左） ／ 車種（右） ─────────────────────────────────────
    _r1a, _r1b = st.columns(2)
    with _r1a:
        st.markdown("<div style='font-size:.72rem;color:#aaa;margin-bottom:2px'>👤 お名前</div>",
                    unsafe_allow_html=True)
        uf_name = st.text_input("お名前", placeholder="山田 太郎", label_visibility="collapsed",
                                 key="uf_name")
    with _r1b:
        uf_car_type = st.text_input("🚗 車種", placeholder="プリウス / N-BOX など", key="uf_car_type")

    # 名前プレビュー（全幅）
    st.markdown(
        f"<div style='font-size:1.55rem;font-weight:900;color:#f0f0f0;"
        f"min-height:2rem;margin:-4px 0 10px;letter-spacing:.03em'>"
        f"{uf_name or '─'}</div>",
        unsafe_allow_html=True)

    # ─ Row 2: 日付（左） ／ 時間（右） ─────────────────────────────────────
    _dc1, _dc2 = st.columns(2)
    with _dc1: uf_date = st.text_input("📅 日付", key="uf_date")
    with _dc2: uf_time = st.text_input("⏰ 時間", placeholder="10:00", key="uf_time")

    # ─ Row 3: 作業内容（左） ／ 所要時間＋ピット（右） ──────────────────────
    _wk = list(WORK_MATRIX.keys())
    _r3a, _r3b = st.columns(2)
    with _r3a:
        uf_job_type = st.selectbox("🔧 作業内容", _wk, key="uf_job_type")
    with _r3b:
        uf_duration = st.slider("⏱ 所要時間（分）", min_value=10, max_value=480, step=10,
                                 key="uf_duration")
        uf_pit_required = st.checkbox("🏗 ピット使用", key="uf_pit_required")

    # ─ Row 4: 連絡先（左） ／ 担当スタッフ（右） ────────────────────────────
    _r4a, _r4b = st.columns(2)
    with _r4a:
        uf_phone = st.text_input("📞 連絡先", placeholder="090-XXXX-XXXX", key="uf_phone")
    with _r4b:
        _sel_staff = st.selectbox("👔 担当スタッフ", STAFF_OPTIONS, key="uf_staff")
        uf_staff = "" if _sel_staff == "(未選択)" else _sel_staff

    # ─ 備考（全幅） ──────────────────────────────────────────────────────────
    uf_memo = st.text_area(
        "📝 備考（お客様メモ・特記事項）",
        height=195, key="uf_memo",
        placeholder=(
            "ETCセットアップあり\n"
            "次回タイヤ交換も検討中\n"
            "ホイールキャップ外す必要あり\n"
            "（自由にメモを書いてください）"
        ),
    )

    # ─ 代車有無 ──────────────────────────────────────────────────────────────
    uf_subcar_needed_raw = st.radio(
        "🚙 代車",
        ["代車不要", "代車を希望する"],
        horizontal=True, key="uf_subcar_needed",
    )
    uf_want_subcar = (uf_subcar_needed_raw == "代車を希望する")

    # ─ 代車車種（希望時のみ） ────────────────────────────────────────────────
    uf_subcar_type = ""
    if uf_want_subcar:
        _lcars = ["(未選択)"] + LOANER_CARS
        _sel_lc = st.selectbox("🚙 代車車種", _lcars, key="uf_subcar_type")
        uf_subcar_type = "" if _sel_lc == "(未選択)" else _sel_lc

    st.markdown("<hr style='border:none;border-top:1px solid #333;margin:12px 0'>",
                unsafe_allow_html=True)

    # ─ 保存 / キャンセル ─────────────────────────────────────────────────────
    _ub1, _ub2 = st.columns(2)
    _save_lbl = "💾 更新する" if mode == "edit" else "📅 予約を確定する"
    with _ub1:
        if st.button(_save_lbl, type="primary", use_container_width=True, key="uf_save"):
            sdf = load_schedule()
            if mode == "edit":
                sid = pf.get("id", "")
                mask = sdf["id"] == sid
                if sid and mask.any():
                    idx = sdf.index[mask][0]
                    sdf.at[idx, "title"]          = uf_job_type
                    sdf.at[idx, "date"]           = uf_date
                    sdf.at[idx, "time"]           = uf_time
                    sdf.at[idx, "detail"]         = uf_memo
                    sdf.at[idx, "cust_name"]      = uf_name
                    sdf.at[idx, "cust_contact"]   = uf_phone
                    sdf.at[idx, "cust_car"]       = uf_car_type
                    sdf.at[idx, "loaner_car"]     = uf_subcar_type
                    sdf.at[idx, "sb_staff"]       = uf_staff
                    sdf.at[idx, "sb_want_loaner"] = "1" if uf_want_subcar else "0"
                    sdf.at[idx, "sb_duration"]    = str(uf_duration)
                    sdf.at[idx, "sb_use_pit"]     = "1" if uf_pit_required else "0"
                    save_schedule(sdf)
                    append_change_log("更新", uf_date, uf_time, uf_memo)
                st.session_state["uf_prefill"] = {}
                st.rerun()
            else:
                new_entry = {
                    "id":             str(uuid.uuid4()),
                    "date":           uf_date,
                    "time":           uf_time,
                    "title":          uf_job_type,
                    "detail":         uf_memo,
                    "status":         "予定",
                    "plate_num":      pf.get("plate_num", ""),
                    "cust_type":      pf.get("cust_type", ""),
                    "sb_duration":    str(uf_duration),
                    "sb_use_pit":     "1" if uf_pit_required else "0",
                    "sb_want_loaner": "1" if uf_want_subcar else "0",
                    "cust_name":      uf_name,
                    "cust_contact":   uf_phone,
                    "cust_car":       uf_car_type,
                    "loaner_car":     uf_subcar_type,
                    "sb_staff":       uf_staff,
                }
                save_schedule(pd.concat([sdf, pd.DataFrame([new_entry])], ignore_index=True))
                append_change_log("新規登録", uf_date, uf_time, uf_memo)
                st.session_state["uf_prefill"]          = {}
                st.session_state["booking_saved_success"] = True
                st.session_state.pop("sb_sel_di", None)
                st.session_state.pop("sb_sel_si", None)
                st.rerun()
    with _ub2:
        if st.button("キャンセル", use_container_width=True, key="uf_cancel"):
            st.session_state["uf_prefill"] = {}
            st.rerun()

    # ─ 編集モード専用アクション ──────────────────────────────────────────────
    if mode == "edit":
        st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
        if st.button("🧾 来店記録に反映", use_container_width=True, key="uf_to_record"):
            _pur = uf_job_type if uf_job_type in PURPOSE_OPTIONS else PURPOSE_OPTIONS[0]
            st.session_state["is_duplicate"]   = True
            st.session_state["duplicate_data"] = {
                "purpose":    _pur,
                "cust_type":  pf.get("cust_type", "一般"),
                "plate_area": "", "plate_3digit": "", "plate_kana": "",
                "plate_num":  pf.get("plate_num", ""),
                "maker": "", "car_model": uf_car_type, "car_size": "", "color": "",
                "age": "", "gender": "",
                "tire_size": "", "tire_size_num": "", "tire_year": "",
                "tire_maker": "", "tire_product": "",
                "memo":       uf_memo,
            }
            st.session_state["nr_initialized"] = False
            st.session_state["uf_prefill"]     = {}
            st.session_state["mode"]           = "new_record"
            st.rerun()
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
        if st.button("🗑️ この予約を削除する", use_container_width=True, type="primary",
                     key="uf_trash"):
            sdf = load_schedule()
            sid = pf.get("id", "")
            if sid:
                mask = sdf["id"] == sid
                if mask.any():
                    _del_row = sdf.loc[mask].iloc[0]
                    append_change_log(
                        "削除",
                        str(_del_row.get("date", "")),
                        str(_del_row.get("time", "")),
                        str(_del_row.get("detail", "")),
                    )
                    sdf.loc[mask, "status"] = "ゴミ箱"
                    save_schedule(sdf)
            st.session_state["uf_prefill"] = {}
            st.rerun()


# ── ページ設定 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GS接客支援システム",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 電卓グリッドCSS最優先注入（set_page_config直後・最初のst呼び出し）──────────
# .mobile-calc-grid クラスはJSが電卓コンテナに付与する。PC版は付与しないため干渉なし。
st.markdown("""
<style>
.mobile-calc-grid [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: stretch !important;
    gap: 5px !important;
}
.mobile-calc-grid [data-testid="column"] {
    width: 23% !important;
    min-width: 0 !important;
    flex: 1 1 auto !important;
    box-sizing: border-box !important;
    padding: 2px !important;
}
.mobile-calc-grid button {
    height: calc(25vw - 15px) !important;
    min-height: 55px !important;
    max-height: 90px !important;
    width: 100% !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 20px !important;
    font-weight: 700 !important;
    white-space: pre-line !important;
}
</style>
""", unsafe_allow_html=True)

defaults = {
    "digits": "",
    "searched_plate": None,
    "mode": "list",
    # "list"|"new_record"|"edit_record"|"view_record"|"quote"|"schedule"
    "view_idx": None,    # original CSV index for view/edit
    "edit_idx": None,
    "week_offset": 0,    # schedule: 0=今週, ±N週
    "show_sched_form": False,
    "edit_sched_id": None,       # schedule: 編集中の予定ID
    "dlg_del_confirm": False,    # schedule dialog: 削除確認フラグ（後方互換のため残存）
    "show_sched_history": False, # schedule: ゴミ箱履歴パネル表示
    "sched_prefill": {},         # schedule: 見積→予定の事前入力データ
    "print_plan": "A",
    # quote 2-step flow
    "quote_step": "hearing",
    "q_hearing_plate": "",
    "q_hearing_maker": "",
    "q_hearing_model": "",
    "q_hearing_customer": "",
    "q_hearing_staff": "",
    "q_hearing_size": "",
    "q_preset_idx": 0,
    "q_num_products": 1,  # 見積: 提案商品数 (1-3)
    # duplicate flow
    "is_duplicate": False,
    "duplicate_data": {},
    # delete flow
    "confirm_delete_idx": None,
    "deleted_message": "",
    # date/time picker state
    "nr_initialized": False,   # new_record: reset to now when entering fresh
    "er_last_idx": None,       # edit_record: which idx was last initialized
    # AI bulk input
    "ai_memo_text": "",
    "ai_parse_result": None,
    "is_ai_input": False,
    # mobile calculator
    "mob_ai_overlay": False,
    # スマート予約 既存予約編集
    "sb_edit_selected_id": None,
    "sb_cancel_confirm_id": None,
    "sb_edit_work_type": list(WORK_MATRIX.keys())[0],
    "sb_edit_duration": 30,
    "sb_edit_use_pit": False,
    "sb_edit_want_loaner": "代車不要",
    "sb_edit_detail": "",
    # 統一フォーム（uf_）
    "show_booking_dialog":  False,  # ダイアログ開閉の唯一のフラグ
    "show_overtime_warning": False,  # 残業確認ダイアログフラグ
    "show_wb_quick_add":    False,  # ホワイトボード簡易追加ダイアログ
    "show_archive_dialog":  False,  # アーカイブ詳細ダイアログ
    "archive_sel_id":       "",     # アーカイブ詳細で表示中のレコードID
    "_arc_needs_init":      False,  # アーカイブダイアログの初回注入フラグ
    "uf_mode": "new",
    "uf_prefill": {},
    # 代車貸出管理表
    "lm_month_off": 0,
    # サクセスアラート
    "booking_saved_success": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── ダークモード ベース ───────────────────────────────────────────────────── */
.stApp,[data-testid="stAppViewContainer"],section[data-testid="stMain"]{background:#121212!important;}
[data-testid="stHeader"]{background:#121212!important;border-bottom:1px solid #2a2a2a!important;}
[data-testid="stSidebar"]{display:none;}
html,body,[class*="css"]{font-family:'Inter','Helvetica Neue',Arial,'Hiragino Kaku Gothic ProN','Yu Gothic',sans-serif;}

/* PC（769px以上）: 横並び完全維持 — モバイルCSSを上書きして元に戻す */
@media(min-width:769px){
  [data-testid="stHorizontalBlock"]{display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;}
  [data-testid="column"]{
    width:auto!important;flex-basis:auto!important;flex-grow:1!important;
    max-width:none!important;min-width:0!important;box-sizing:border-box!important;
    margin-bottom:0!important;
  }
  .stSelectbox,.stTextInput,.stDateInput,.stNumberInput,.stTextArea,.stSlider,.stCheckbox,.stRadio{
    width:auto!important;
  }
  [data-testid="stVerticalBlock"]>div{width:auto!important;}
}

/* ── ダイアログ：全体幅を 95vw に広げる ＋ 横並みを画面幅に依存させない ── */
/* Streamlit "large" ダイアログのコンテンツ域が 768px 以下になると
   @media(max-width:768px) のカラム縦積みが誤作動するため、
   ダイアログ内では @media を使わずに直接横並びを強制する。          */

/* 外側ポジショニングラッパー（Streamlit が生成する stModal 直下の div） */
[data-testid="stModal"]>div{
  max-width:95vw!important;
  width:95vw!important;
}
/* BaseWeb dialog 本体 */
[data-baseweb="dialog"]{
  max-width:95vw!important;
  width:95vw!important;
}
/* スクロール可能なコンテンツ域 */
[data-testid="stDialogScrollableContent"]{
  max-width:100%!important;
  width:100%!important;
}
[data-baseweb="dialog"] [data-testid="stHorizontalBlock"]{
  display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;
  width:100%!important;box-sizing:border-box!important;
}
[data-baseweb="dialog"] div[data-testid="column"]{
  width:auto!important;flex-basis:auto!important;flex-grow:1!important;
  min-width:0!important;max-width:none!important;
  box-sizing:border-box!important;margin-bottom:12px!important;
}
[data-baseweb="dialog"] .stSelectbox,
[data-baseweb="dialog"] .stTextInput,
[data-baseweb="dialog"] .stDateInput,
[data-baseweb="dialog"] .stNumberInput,
[data-baseweb="dialog"] .stTextArea,
[data-baseweb="dialog"] .stSlider{
  width:100%!important;
}

/* ── 全ボタン ベースライン（ダークグレー） */
[data-testid="stButton"]>button{
  width:100%!important;box-sizing:border-box!important;
  background:#1e1e1e!important;border:1.5px solid #383838!important;
  color:#c8c8c8!important;border-radius:10px!important;
  transition:background .1s,border-color .1s,color .1s!important;
}
[data-testid="stButton"]>button:hover{
  background:#272727!important;border-color:#545454!important;color:#f0f0f0!important;
}

/* ── スマホ共通 ─────────────────────────────────────────────────────────── */
@media(max-width:768px){
  html,body{overflow-x:hidden!important;max-width:100vw!important;}

  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],
  .main,
  .main .block-container,
  [data-testid="stMainBlockContainer"]{
    max-width:100vw!important;width:100%!important;
    overflow-x:hidden!important;overflow-y:auto!important;
    box-sizing:border-box!important;
  }
  .main .block-container,[data-testid="stMainBlockContainer"]{padding:0.3rem!important;}

  /* ── フォーム列はモバイルで縦並びに（wrap）、ボタンは44px確保 ──────────── */
  body:not(.mob-calc-active) [data-testid="stHorizontalBlock"]{
    display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;
    width:100%!important;box-sizing:border-box!important;
  }
  div[data-testid="column"]{
    width:100%!important;flex-basis:100%!important;flex-grow:1!important;
    min-width:0!important;max-width:100%!important;
    overflow:hidden!important;box-sizing:border-box!important;
    margin-bottom:12px!important;
  }
  body:not(.mob-calc-active) [data-testid="stButton"]>button{
    min-height:44px!important;height:auto!important;
    white-space:normal!important;padding:6px 4px!important;font-size:.82rem!important;
  }

  /* ── カレンダー(7列)・予約グリッド(8列): 横スクロール・横並み維持 ──────── */
  body:not(.mob-calc-active) [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(7):last-child),
  body:not(.mob-calc-active) [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(8):last-child){
    flex-wrap:nowrap!important;overflow-x:scroll!important;-webkit-overflow-scrolling:touch!important;
  }
  body:not(.mob-calc-active) [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(8):last-child)>[data-testid="column"]{
    flex:0 0 auto!important;min-width:70px!important;width:auto!important;max-width:none!important;
  }

  /* ── ホワイトボード(7列): JS が paintWB() で overflow を解放済み ──────── */
  [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(7):last-child){
    overflow-x:scroll!important;-webkit-overflow-scrolling:touch!important;
    scrollbar-width:thin!important;
  }
  [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(7):last-child)>[data-testid="column"]{
    flex:0 0 260px!important;min-width:260px!important;width:260px!important;flex-shrink:0!important;
  }

  /* ── 全来店記録テーブル: 横スクロール確保（外枠は固定）────────────────── */
  [data-testid="stDataFrame"]{
    overflow-x:auto!important;-webkit-overflow-scrolling:touch!important;
    width:100%!important;max-width:100%!important;
  }
  [data-testid="stDataFrame"] > div,[data-testid="stDataFrame"] iframe{
    overflow-x:auto!important;-webkit-overflow-scrolling:touch!important;
    width:100%!important;
  }

  /* ── フォーム内ウィジェットの幅100%強制（use_container_width非対応版対応） */
  .stSelectbox, .stTextInput, .stDateInput, .stNumberInput,
  .stTextArea, .stSlider, .stCheckbox, .stRadio {
    width:100%!important;
  }
  [data-testid="stVerticalBlock"] > div {
    width:100%!important;
  }
}

/* ── スマート予約 / 代車貸出 グリッドテーブル ──────────────────────────────── */
.scrollable-wrapper{
  overflow-x:auto!important;
  -webkit-overflow-scrolling:touch!important;
  width:100%!important;
  margin:0 0 8px!important;
}
table.grid-table-standard{
  display:table!important;
  min-width:800px!important;
  table-layout:fixed!important;
  border-collapse:collapse!important;
}
table.grid-table-standard th,table.grid-table-standard td{
  padding:5px 4px!important;font-size:.8rem!important;text-align:center!important;
  border:1px solid #2a2a2a!important;white-space:nowrap!important;line-height:1.3!important;
}
table.grid-table-standard th{background:#1a1a1a!important;color:#aaa!important;font-weight:700!important;}
table.grid-table-standard th.label-col,table.grid-table-standard td.label-col{
  width:52px!important;position:sticky!important;left:0!important;
  background:#121212!important;z-index:10!important;
}
table.grid-table-standard th.label-col{background:#1a1a1a!important;}
table.grid-table-standard th.today-col{color:#60a5fa!important;font-weight:800!important;}
table.grid-table-standard td.sym-ok2{background:#0d3324!important;color:#4ade80!important;font-weight:800!important;}
table.grid-table-standard td.sym-ok1{background:#0f2a16!important;color:#86efac!important;font-weight:700!important;}
table.grid-table-standard td.sym-warn{background:#2a2000!important;color:#f59e0b!important;font-weight:700!important;}
table.grid-table-standard td.sym-ng{background:#1e1e1e!important;color:#3a3a3a!important;}
table.grid-table-standard td.sym-loaner-ok{background:#0d3324!important;color:#4ade80!important;font-size:1.05rem!important;font-weight:700!important;}
table.grid-table-standard td.sym-loaner-booked{background:#2d1800!important;color:#f59e0b!important;font-size:.72rem!important;line-height:1.4!important;white-space:pre-line!important;}
table.grid-table-standard td.sym-ok2 a:active,
table.grid-table-standard td.sym-ok1 a:active,
table.grid-table-standard td.sym-warn a:active,
table.grid-table-standard td.sym-loaner-ok a:active{opacity:.55!important;transition:opacity .1s!important;}
.grid-link{display:block;width:100%;height:100%;color:inherit;text-decoration:none;padding:4px 0;-webkit-tap-highlight-color:transparent;}

/* デスクトップ3列テンキー */
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(3):last-child) [data-testid="column"]{flex:1 1 0!important;}
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(3):last-child) [data-testid="stButton"]>button{height:60px!important;font-size:1.35rem!important;font-weight:700!important;background:#2a2a2a!important;border:1.5px solid #3a3a3a!important;border-radius:12px!important;color:#f5f5f5!important;box-shadow:0 1px 4px rgba(0,0,0,.4)!important;padding:0!important;transition:background .08s,transform .08s!important;}
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(3):last-child) [data-testid="stButton"]>button:hover{background:#3a3a3a!important;}
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(3):last-child) [data-testid="stButton"]>button:active{background:#4a4a4a!important;transform:scale(.94)!important;}

/* ── SB予約グリッド(8列): ◎/○ 明緑 ── */
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(8):last-child)
[data-testid="stButton"]>button[kind="primary"],
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(8):last-child)
[data-testid="stButton"]>button[data-testid="baseButton-primary"]{
  background:#0a2e12!important;border:1.5px solid #2ea44f!important;
  color:#23c55e!important;font-weight:800!important;
}
/* ── SB予約グリッド(8列): △ アンバー ── */
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(8):last-child)
[data-testid="stButton"]>button:not([kind="primary"]):not([data-testid="baseButton-primary"]){
  background:#2d1800!important;border:1.5px solid #f59e0b!important;
  color:#ffb020!important;font-weight:700!important;
}

/* ── プライマリ（検索・保存・実行）→ ディープグリーン  詳細度(0,2,1)でベースルール(0,1,1)に確実に勝つ */
[data-testid="stButton"]>button[data-testid="baseButton-primary"],
[data-testid="stButton"]>button[kind="primary"],
[data-testid="stFormSubmitButton"]>button[data-testid="baseButton-primaryFormSubmit"],
[data-testid="stFormSubmitButton"]>button{
  background:#1b5e20!important;border:1.5px solid #2e7d32!important;
  color:#e8f5e9!important;font-weight:700!important;
  height:44px!important;border-radius:12px!important;padding:0 12px!important;
  box-shadow:none!important;transition:background .12s,border-color .12s!important;
}
[data-testid="stButton"]>button[data-testid="baseButton-primary"]:hover,
[data-testid="stButton"]>button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"]>button[data-testid="baseButton-primaryFormSubmit"]:hover,
[data-testid="stFormSubmitButton"]>button:hover{
  background:#2e7d32!important;border-color:#43a047!important;color:#fff!important;
  box-shadow:0 2px 10px rgba(46,125,50,.3)!important;
}
@media(max-width:600px){
  [data-testid="stButton"]>button[data-testid="baseButton-primary"],
  [data-testid="stButton"]>button[kind="primary"],
  [data-testid="stFormSubmitButton"]>button{height:40px!important;}
}

/* ディスプレイ（電卓） */
.numpad-display{background:linear-gradient(135deg,#1e1e1e,#181818);border:1.5px solid #333;border-radius:16px;height:64px;display:flex;align-items:center;justify-content:center;margin-bottom:10px;}
.d-val{font-size:2.1rem;font-weight:800;letter-spacing:.5rem;color:#f5f5f5;font-variant-numeric:tabular-nums;}
.d-ph{font-size:1rem;color:#555;letter-spacing:.4rem;}

/* フィールド（入力欄） */
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stNumberInput"] input{background:#1c1c1c!important;border:1.5px solid #333!important;border-radius:10px!important;font-size:.92rem!important;color:#f5f5f5!important;transition:border-color .15s!important;}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus{border-color:#deff9a!important;box-shadow:0 0 0 3px rgba(222,255,154,.15)!important;}
[data-testid="stSelectbox"]>div>div{border:1.5px solid #333!important;border-radius:10px!important;background:#1c1c1c!important;color:#f5f5f5!important;}

/* バッジ */
.badge{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.73rem;font-weight:600;}
.bp{background:#1e3a5f;color:#7ec8f5;}
.bt-一般{background:#2a2a2a;color:#aaa;}
.bt-業者{background:#3a2800;color:#f9c74f;}
.bt-常連{background:#0d3324;color:#6ee7b7;}
.bg-男{background:#1e2f5f;color:#93c5fd;}
.bg-女{background:#3d1a2e;color:#f0abca;}
.bg-無記名{background:#2a2a2a;color:#888;}

/* 見積カード共通 */
.q-row{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.07);font-size:.84rem;}
.q-row:last-child{border-bottom:none;}
.q-label{color:#aaa;}
.q-val{font-weight:600;color:#f5f5f5;}

/* A表チェック */
.acheck-ok{background:#0d2d1a;border:1px solid #4ade80;border-radius:12px;padding:10px 12px;text-align:center;color:#4ade80;}
.acheck-ng{background:#2d0d0d;border:1px solid #f87171;border-radius:12px;padding:10px 12px;text-align:center;color:#f87171;}

/* 予定ボード */
.sched-col-header{text-align:center;font-weight:700;font-size:.82rem;padding:6px 0;border-radius:8px 8px 0 0;margin-bottom:4px;}
.sched-col-today{background:#1d4ed8;color:#fff;}
.sched-col-normal{background:#1c1c1c;color:#aaa;}
.sched-col-past{background:#181818;color:#555;}
.sched-item{background:#2a2200;border:1.5px solid #f59e0b;border-left:4px solid #f59e0b;border-radius:8px;padding:8px 10px;margin-bottom:6px;font-size:.8rem;}
.sched-item-done{background:#1c1c1c;border:1.5px solid #333;border-left:4px solid #555;border-radius:8px;padding:8px 10px;margin-bottom:6px;font-size:.8rem;opacity:.55;}

/* ── カレンダー7列グリッド内のアクションボタン（絵文字のみ・小型正方形） */
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(7):last-child)
>[data-testid="column"]
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(2):last-child)
[data-testid="stButton"]>button{
  height:28px!important;min-height:28px!important;max-height:28px!important;
  padding:0!important;font-size:1rem!important;line-height:1!important;
  border-radius:7px!important;width:100%!important;
}
.sched-pin{font-size:.95rem;margin-right:4px;}
.sched-title{font-weight:700;color:#f5f5f5;margin-bottom:2px;}
.sched-detail{color:#aaa;font-size:.76rem;}

/* 詳細カード */
.detail-card{background:#1c1c1c;border:1px solid #2a2a2a;border-radius:16px;padding:20px 22px;margin-bottom:12px;}
.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 28px;font-size:.88rem;margin-top:12px;}
.detail-label{color:#888;font-size:.74rem;display:block;margin-bottom:2px;}
.detail-val{color:#f0f0f0;font-weight:500;}
.memo-box{margin-top:14px;padding:10px 14px;background:#1e1800;border-left:4px solid #f0a500;border-radius:0 8px 8px 0;font-size:.86rem;color:#f0c060;line-height:1.75;}

.divider{border:none;border-top:1px solid #2a2a2a;margin:10px 0;}
.sec-title{font-size:.72rem;font-weight:700;color:#888;letter-spacing:.08em;text-transform:uppercase;margin:14px 0 5px;}

/* 削除ボタン（選択行アクション4列目） */
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(4):last-child) [data-testid="column"]:nth-child(4) [data-testid="stButton"]>button{background:#2d0d0d!important;border:1.5px solid #f87171!important;color:#f87171!important;font-weight:700!important;}
[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(4):last-child) [data-testid="column"]:nth-child(4) [data-testid="stButton"]>button:hover{background:#ef4444!important;border-color:#dc2626!important;color:#fff!important;}


/* ── インラインスタイルの黒文字 → 白文字に強制変換（ダークモード対応） ── */
[style*="color:#1a1a2e"],[style*="color: #1a1a2e"]{color:#f0f0f0!important;}
[style*="color:#374151"],[style*="color: #374151"]{color:#ccc!important;}
[style*="color:#555"],[style*="color: #555"]{color:#aaa!important;}
[style*="color:#666"],[style*="color: #666"]{color:#aaa!important;}
[style*="color:#6b4c00"],[style*="color: #6b4c00"]{color:#f0c060!important;}
[style*="color:#856404"],[style*="color: #856404"]{color:#fcd34d!important;}
[style*="color:#a07000"],[style*="color: #a07000"]{color:#f9c74f!important;}
[style*="background:#fff0f0"],[style*="background: #fff0f0"]{background:#2d0d0d!important;}
[style*="background:#eff6ff"],[style*="background: #eff6ff"]{background:#0f1f3d!important;}
[style*="background:#fff8e1"],[style*="background: #fff8e1"]{background:#2a2000!important;}
[style*="background:#fafafa"],[style*="background: #fafafa"]{background:#1c1c1c!important;}
[style*="color:#1e40af"],[style*="color: #1e40af"]{color:#93c5fd!important;}
[style*="color:#3b82f6"],[style*="color: #3b82f6"]{color:#93c5fd!important;}
[style*="color:#b91c1c"],[style*="color: #b91c1c"]{color:#f87171!important;}
[style*="color:#aaa"]{color:#888!important;}
[style*="background:#fff;"]{ background:#1c1c1c!important;}
[style*="background:#fff "]{ background:#1c1c1c!important;}
[style*="background-color:#fff"]{background-color:#1c1c1c!important;}

/* ── iPhone電卓CSS: .mob-calc-css クラスがある時のみ適用 ── */
/* (Pythonが .mob-calc-active を body に付与したタイミングで発動) */
body.mob-calc-active{background:#000!important;}
body.mob-calc-active [data-testid="stAppViewContainer"],
body.mob-calc-active section[data-testid="stMain"],
body.mob-calc-active [data-testid="stMainBlockContainer"]{background:#000!important;}
body.mob-calc-active [data-testid="stHeader"]{background:#000!important;border-color:#222!important;}
.mob-display{color:#fff;font-size:3.2rem;font-weight:200;text-align:right;padding:8px 20px 14px;letter-spacing:4px;min-height:90px;font-family:-apple-system,'SF Pro Display','Helvetica Neue',sans-serif;}
.mob-sub{color:#636366;font-size:.78rem;text-align:right;padding:0 22px 8px;}
/* ── 電卓ボタン共通スタイル ── */
body.mob-calc-active [data-testid="stHorizontalBlock"]{
  display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;gap:5px!important;
}
body.mob-calc-active [data-testid="column"]{
  width:23%!important;min-width:0!important;flex:1 1 auto!important;
  padding:2px!important;box-sizing:border-box!important;
}

/* calc-wrapper セレクタ（JSによる確実なレイアウト保証の補助） */
div.calc-wrapper [data-testid="stHorizontalBlock"]{
  display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;gap:5px!important;
}
div.calc-wrapper [data-testid="column"]{
  width:23%!important;min-width:0!important;flex:1 1 auto!important;
  padding:2px!important;box-sizing:border-box!important;
}

/* 全電卓ボタンの共通形状 */
body.mob-calc-active [data-testid="stButton"]>button,
div.calc-wrapper [data-testid="stButton"]>button{
  height:calc(25vw - 15px)!important;
  min-height:55px!important;
  max-height:90px!important;
  width:100%!important;
  border-radius:20px!important;
  border:none!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  font-size:clamp(1.1rem,5vw,1.6rem)!important;
  font-weight:700!important;
  line-height:1!important;
  padding:0!important;
  min-height:0!important;
  box-shadow:0 3px 8px rgba(0,0,0,.5)!important;
  white-space:pre-line!important;
  transition:transform .08s,opacity .08s!important;
}
body.mob-calc-active [data-testid="stButton"]>button:active{
  transform:scale(.92)!important;opacity:.8!important;
}

/* 3列ファンクション行 (C / ⌫ / 🤖AI) */
body.mob-calc-active [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(3):last-child) [data-testid="column"]{
  flex:1 1 0!important;min-width:0!important;
}
body.mob-calc-active [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(3):last-child) [data-testid="stButton"]>button{
  background:#a5a5a5!important;color:#000!important;font-size:1.35rem!important;
}
/* AI ボタン (3列の3番目) → オレンジ */
body.mob-calc-active [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(3):last-child) [data-testid="column"]:nth-child(3) [data-testid="stButton"]>button{
  background:#ff9f0a!important;color:#fff!important;
}

/* 4列数字行 */
body.mob-calc-active [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(4):last-child) [data-testid="column"]{
  flex:1 1 0!important;min-width:0!important;
}
body.mob-calc-active [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(4):last-child) [data-testid="stButton"]>button{
  background:#333!important;color:#fff!important;
}
/* Primary (新規 / 見積 / 予定 / 検索) → ブルー */
body.mob-calc-active [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(4):last-child) [data-testid="stButton"]>button[data-testid="baseButton-primary"]{
  background:#2563eb!important;color:#fff!important;
}
body.mob-calc-active [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(4):last-child) [data-testid="stButton"]>button[data-testid="baseButton-primary"]:hover{
  background:#1d4ed8!important;
}
body.mob-calc-active [data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(4):last-child) [data-testid="stButton"]>button:hover:not([data-testid="baseButton-primary"]){
  background:#4a4a4a!important;
}
/* Streamlitボタンを不可視化（DOMには残しJS clickのために必要） */
body.mob-calc-active .mob-btn-hidden{
  position:absolute!important;
  left:-9999px!important;
  top:-9999px!important;
  opacity:0!important;
  pointer-events:none!important;
}

</style>
""", unsafe_allow_html=True)

# ── キャッシュクリア（セッション初回のみ） ───────────────────────────────────
if "cache_cleared" not in st.session_state:
    st.cache_data.clear()
    st.session_state["cache_cleared"] = True

# ── モバイル検出（JS → query param → Python） ────────────────────────────────
# ?_m=1 または ?m=1 どちらでも受け付ける（ngrok URL対応）
_is_mobile = st.query_params.get("_m", "0") == "1" or st.query_params.get("m", "0") == "1"

# ── モバイル電卓専用CSS（@mediaで明示 + .calc-wrapper + body.mob-calc-active）──
if _is_mobile:
    st.markdown("""
<style>
/* _is_mobile=True 確定時：@media不要・無条件適用（ngrok含む全ドメイン対応） */
div.calc-wrapper [data-testid="stHorizontalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  gap: 5px !important;
}
div.calc-wrapper [data-testid="column"] {
  width: 23% !important;
  min-width: 0 !important;
  flex: 1 1 auto !important;
  box-sizing: border-box !important;
  padding: 2px !important;
}
body.mob-calc-active [data-testid="stHorizontalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  gap: 5px !important;
}
body.mob-calc-active [data-testid="column"] {
  width: 23% !important;
  min-width: 0 !important;
  flex: 1 1 auto !important;
  box-sizing: border-box !important;
  padding: 2px !important;
}
body.mob-calc-active [data-testid="stButton"] > button {
  height: calc(25vw - 15px) !important;
  min-height: 55px !important;
  max-height: 90px !important;
  width: 100% !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 20px !important;
  font-size: clamp(1rem, 5vw, 1.5rem) !important;
  font-weight: 700 !important;
  white-space: pre-line !important;
}
</style>
""", unsafe_allow_html=True)

components.html("""<script>
(function(){
  try{
    var p=window.parent||window;
    var s=p.location.search;
    var host=p.location.hostname||'';
    /* 画面幅：親ドキュメント優先、フォールバックはscreenWidth */
    var w=(p.innerWidth||p.document.documentElement.clientWidth||window.innerWidth||screen.width);
    var isNgrok=host.indexOf('ngrok')>=0;
    var isMob=w<768||isNgrok; /* ngrokドメインは無条件でスマホ扱い */
    /* ?_m=1 または ?m=1 どちらでも有効 */
    var hasParam=s.indexOf('_m=1')>=0||s.indexOf('m=1')>=0;
    if(isMob&&!hasParam){ p.location.href=p.location.pathname+'?_m=1'; }
    else if(!isMob&&hasParam){ p.location.href=p.location.pathname; }
  }catch(e){/* cross-origin blocked: 手動で ?m=1 を付加してください */}
})();
</script>""", height=0, scrolling=False)

# pq / mode はモバイル・デスクトップ両方で参照するため事前に定義
pq   = st.session_state.searched_plate
mode = st.session_state.mode

# ════════════════════════════════════════════════════════════════════════════
#  📱 モバイル専用 iPhone電卓UI
# ════════════════════════════════════════════════════════════════════════════
if _is_mobile:
    # ── ?_m=1 判定済み：モバイル強制整列JS（0.1/0.5/1/2秒 + setInterval） ──
    components.html("""<script>
    (function(){
      var doc=window.parent.document;

      function forceRow(){
        var vw=doc.documentElement.clientWidth||window.innerWidth||375;
        if(vw>=768) return; /* PC保護 */
        if(!doc.body.classList.contains('mob-calc-active')) return;

        doc.querySelectorAll('[data-testid="stHorizontalBlock"]').forEach(function(bl){
          bl.style.setProperty('display','flex','important');
          bl.style.setProperty('flex-direction','row','important');
          bl.style.setProperty('flex-wrap','nowrap','important');
          bl.style.setProperty('align-items','stretch','important');
          bl.style.setProperty('gap','5px','important');
          var cols=bl.querySelectorAll(':scope>[data-testid="column"]');
          var n=cols.length; if(n<2) return;
          var w=(100/n).toFixed(2)+'%';
          cols.forEach(function(c){
            c.style.setProperty('width',w,'important');
            c.style.setProperty('min-width','0','important');
            c.style.setProperty('max-width',w,'important');
            c.style.setProperty('flex','1 1 auto','important');
            c.style.setProperty('box-sizing','border-box','important');
            c.style.setProperty('padding','2px','important');
          });
        });
      }

      /* 0.1秒・0.5秒・1秒・2秒後に実行（Streamlit非同期描画後をカバー） */
      [100,500,1000,2000].forEach(function(d){ setTimeout(forceRow,d); });

      /* 400ms間隔で継続監視（再描画のたびに上書きされるstyleを維持） */
      if(!window.parent._mobForceInterval){
        window.parent._mobForceInterval=setInterval(forceRow,400);
      }
    })();
    </script>""", height=0, scrolling=False)

    if mode == "list":
        # ── 検索結果ビュー: searched_plate がセット済みなら電卓を隠す ──────
        if st.session_state.searched_plate is not None:
            components.html("""<script>
            (function(){
              var doc=window.parent.document;
              var b=doc.body;
              if(b) b.classList.remove('mob-calc-active');
              if(window.parent._mobForceInterval){ clearInterval(window.parent._mobForceInterval); window.parent._mobForceInterval=null; }
              if(window.parent._calcGridInterval){ clearInterval(window.parent._calcGridInterval); window.parent._calcGridInterval=null; }
              if(window.parent._calcGridObserver){ window.parent._calcGridObserver.disconnect(); window.parent._calcGridObserver=null; }
              doc.querySelectorAll('.mobile-calc-grid').forEach(function(el){ el.classList.remove('mobile-calc-grid'); });
              doc.querySelectorAll('.mob-btn-hidden').forEach(function(el){ el.classList.remove('mob-btn-hidden'); });
              doc.querySelectorAll('[data-testid="stHorizontalBlock"]').forEach(function(bl){
                ['display','flex-direction','flex-wrap','gap'].forEach(function(p){ bl.style.removeProperty(p); });
              });
              doc.querySelectorAll('[data-testid="column"]').forEach(function(c){
                ['flex','min-width','max-width','width','padding','box-sizing'].forEach(function(p){ c.style.removeProperty(p); });
              });
              doc.querySelectorAll('[data-testid="stButton"]>button').forEach(function(btn){
                ['height','padding','display','align-items','justify-content'].forEach(function(p){ btn.style.removeProperty(p); });
              });
            })();
            </script>""", height=0, scrolling=False)
            _sp = st.session_state.searched_plate
            _mob_title = f"🔎 「{_sp}」の検索結果" if _sp else "🔎 来店履歴（全件）"
            st.markdown(
                f"<div style='font-size:.95rem;font-weight:800;color:#f5f5f5;padding:4px 0'>"
                f"{_mob_title}</div>",
                unsafe_allow_html=True)
            if st.button("← 戻る", key="mob_srch_back", use_container_width=True):
                st.session_state.searched_plate = None
                st.session_state.digits = ""
                st.rerun()

        else:
            # ── 電卓CSS を body クラスで有効化 + グリッド強制 ────────────────
            components.html("""<script>
            (function(){
              var doc=window.parent.document;
              var b=doc.body;
              if(b&&!b.classList.contains('mob-calc-active')){
                b.classList.add('mob-calc-active');
              }

              function fixCalcGrid(){
                if(!doc.body.classList.contains('mob-calc-active')) return;
                var vw=doc.documentElement.clientWidth||window.parent.innerWidth||375;
                if(vw>=768) return; /* PC保護：768px以上では絶対に触らない */
                var btnH=Math.min(Math.max(Math.round(vw*0.25-15),55),90)+'px';

                /* マーカーから電卓コンテナ(stVerticalBlock)を特定 */
                var marker=doc.getElementById('calc-marker');
                var calcContainer=null;
                if(marker){
                  var el=marker.parentElement;
                  while(el){
                    if(el.getAttribute('data-testid')==='stVerticalBlock'){ calcContainer=el; break; }
                    el=el.parentElement;
                  }
                }
                if(calcContainer){ calcContainer.classList.add('mobile-calc-grid'); }

                /* ボタンコンテナ(calc-btn-marker)を不可視化 — DOMには残す */
                var btnMarker=doc.getElementById('calc-btn-marker');
                var btnCont=null;
                if(btnMarker){
                  var bel=btnMarker.parentElement;
                  while(bel){
                    if(bel.getAttribute('data-testid')==='stVerticalBlock'){ btnCont=bel; break; }
                    bel=bel.parentElement;
                  }
                }
                if(btnCont){ btnCont.classList.add('mob-btn-hidden'); }

                /* 電卓コンテナ内のstHorizontalBlockのみ対象（見つからない場合は全体） */
                var scope=calcContainer||doc;
                var blocks=scope.querySelectorAll('[data-testid="stHorizontalBlock"]');
                blocks.forEach(function(bl){
                  bl.style.setProperty('display','flex','important');
                  bl.style.setProperty('flex-direction','row','important');
                  bl.style.setProperty('flex-wrap','nowrap','important');
                  bl.style.setProperty('gap','5px','important');
                  var cols=bl.querySelectorAll(':scope>[data-testid="column"]');
                  var n=cols.length;
                  if(n<2) return;
                  var w=(100/n).toFixed(2)+'%';
                  cols.forEach(function(c){
                    c.style.setProperty('flex','1 1 auto','important');
                    c.style.setProperty('min-width','0','important');
                    c.style.setProperty('max-width',w,'important');
                    c.style.setProperty('width',w,'important');
                    c.style.setProperty('padding','2px','important');
                    c.style.setProperty('box-sizing','border-box','important');
                  });
                  bl.querySelectorAll('[data-testid="stButton"]>button').forEach(function(btn){
                    btn.style.setProperty('height',btnH,'important');
                    btn.style.setProperty('min-height','0','important');
                    btn.style.setProperty('width','100%','important');
                    btn.style.setProperty('padding','0','important');
                    btn.style.setProperty('display','flex','important');
                    btn.style.setProperty('align-items','center','important');
                    btn.style.setProperty('justify-content','center','important');
                  });
                });
              }

              /* 即時実行 + 遅延リトライ（Reactの非同期コミット後に確実に適用） */
              fixCalcGrid();
              setTimeout(fixCalcGrid,80);
              setTimeout(fixCalcGrid,250);
              setTimeout(fixCalcGrid,600);
              setTimeout(fixCalcGrid,1200);

              /* setInterval: Streamlit再描画のたびに上書きされるstyleを強制維持 */
              if(!window.parent._calcGridInterval){
                window.parent._calcGridInterval=setInterval(function(){
                  if(doc.body.classList.contains('mob-calc-active')){
                    fixCalcGrid();
                  } else {
                    clearInterval(window.parent._calcGridInterval);
                    window.parent._calcGridInterval=null;
                  }
                },400);
              }

              /* MutationObserver: DOM変更を即座に検知して再適用 */
              if(!window.parent._calcGridObserver){
                var _t=null;
                window.parent._calcGridObserver=new MutationObserver(function(){
                  clearTimeout(_t);
                  _t=setTimeout(fixCalcGrid,50);
                });
                window.parent._calcGridObserver.observe(doc.body,{
                  childList:true, subtree:true,
                  attributes:true, attributeFilter:['style','class']
                });
              }
            })();
            </script>""", height=0, scrolling=False)

            # ── [外側] ディスプレイ + AIオーバーレイ（calc-marker付き） ──────
            with st.container():
                st.markdown('<span id="calc-marker" style="display:none"></span>', unsafe_allow_html=True)

                # AIオーバーレイ
                if st.session_state.get("mob_ai_overlay", False):
                    st.markdown("""
                    <div style="background:#1c1c1e;border:1.5px solid #ff9f0a;border-radius:14px;
                                padding:10px 14px;margin:6px 0 4px">
                      <div style="font-size:.8rem;font-weight:700;color:#ff9f0a;margin-bottom:6px">
                        🤖 接客メモを入力してください
                      </div>
                    </div>""", unsafe_allow_html=True)
                    mob_ai_text = st.text_area(
                        "接客メモ", height=110,
                        placeholder="例: 10:21 香川 333 あ 3666 ダイハツ EXE 黒\nタイヤ 1956515 製造23年",
                        key="mob_ai_text_input",
                        label_visibility="collapsed",
                    )
                    oa1, oa2 = st.columns(2)
                    with oa1:
                        if st.button("🔍 AI解析", key="mob_ai_parse", type="primary",
                                     use_container_width=True, disabled=not mob_ai_text.strip()):
                            with st.spinner("解析中..."):
                                _ref = get_last_record_date().strftime("%Y/%m/%d")
                                _res, _err = ai_parse_record(mob_ai_text, ref_date=_ref)
                            if _err:
                                _now = datetime.now()
                                _res = {"date": f"{_ref} {_now.strftime('%H:%M')}", "memo": mob_ai_text}
                            _d0, _h0, _m0 = _parse_dt(_res.get("date", ""))
                            st.session_state["nr_date"] = _d0
                            st.session_state["nr_hour"] = _h0
                            st.session_state["nr_min"]  = _m0
                            st.session_state.nr_initialized = True
                            st.session_state.is_duplicate   = True
                            st.session_state.is_ai_input    = True
                            st.session_state.duplicate_data = _res
                            st.session_state.mob_ai_overlay = False
                            st.session_state.mode = "new_record"
                            st.rerun()
                    with oa2:
                        if st.button("✕ 閉じる", key="mob_ai_close", use_container_width=True):
                            st.session_state.mob_ai_overlay = False
                            st.rerun()

                # 数字ディスプレイ
                _d  = st.session_state.digits
                _pq = st.session_state.searched_plate or ""
                _disp = _d if _d else (_pq if _pq else "- - - -")
                _sub  = f"検索: {_pq}" if _pq and not _d else ("4桁入力で自動検索" if not _d else "")
                st.markdown(
                    f'<div class="mob-display">{_disp}</div>'
                    f'<div class="mob-sub">{_sub}</div>',
                    unsafe_allow_html=True)

            # ── [内側] Streamlitボタン群（DOM上に存在、CSS+JSで不可視化） ────
            # JSが calc-btn-marker を探して親stVerticalBlockに mob-btn-hidden クラスを付与
            # CSS .mob-btn-hidden { position:absolute; left:-9999px; } で画面外へ
            # HTML電卓ボタンが window.parent.document からこれを見つけて .click() する
            with st.container():
                st.markdown('<span id="calc-btn-marker" style="display:none"></span>', unsafe_allow_html=True)

                # ファンクション行: [C] [⌫] [🤖AI]
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    if st.button("C", key="mc_c", use_container_width=True):
                        st.session_state.digits = ""
                        st.session_state.searched_plate = None
                        st.session_state.mob_ai_overlay = False
                        st.rerun()
                with fc2:
                    if st.button("⌫", key="mc_del", use_container_width=True):
                        st.session_state.digits = st.session_state.digits[:-1]
                        st.rerun()
                with fc3:
                    if st.button("🤖  AI", key="mc_ai", use_container_width=True, type="primary"):
                        st.session_state.mob_ai_overlay = not st.session_state.get("mob_ai_overlay", False)
                        st.session_state.ai_parse_result = None
                        st.rerun()

                # 数字グリッド（4列 × 4行）
                MOB_ROWS = [
                    [("7","mc7"),("8","mc8"),("9","mc9"),("➕\n新規","mc_new",True)],
                    [("4","mc4"),("5","mc5"),("6","mc6"),("🛞\n見積","mc_quote",True)],
                    [("1","mc1"),("2","mc2"),("3","mc3"),("📅\n予定","mc_sched",True)],
                    [("0","mc0"),("📋\n複製","mc_dup",True),(None,None,False),("🔍\n検索/履歴","mc_srch",True)],
                ]
                for row_def in MOB_ROWS:
                    rcols = st.columns(4)
                    for ci, item in enumerate(row_def):
                        with rcols[ci]:
                            if item[0] is None:
                                continue
                            lbl, kk = item[0], item[1]
                            is_prim  = item[2] if len(item) > 2 else False
                            btn_type = "primary" if is_prim else "secondary"
                            if st.button(lbl, key=kk, use_container_width=True, type=btn_type):
                                if lbl.isdigit():
                                    if len(st.session_state.digits) < 4:
                                        st.session_state.digits += lbl
                                        if len(st.session_state.digits) == 4:
                                            st.session_state.searched_plate = st.session_state.digits
                                            st.session_state.digits = ""
                                            st.session_state.view_idx = None
                                elif "新規" in lbl:
                                    st.session_state.nr_initialized = False
                                    st.session_state.mode = "new_record"
                                    st.session_state.view_idx = None
                                elif "見積" in lbl:
                                    st.session_state.mode = "quote"
                                elif "予定" in lbl:
                                    st.session_state.mode = "schedule"
                                elif "検索" in lbl:
                                    _q = st.session_state.digits  # "" = 全件表示, "1234" = 絞り込み
                                    st.session_state.searched_plate = _q
                                    st.session_state.digits = ""
                                    st.session_state.view_idx = None
                                    st.session_state.mode = "list"
                                elif "複製" in lbl:
                                    _pn = st.session_state.digits or st.session_state.searched_plate or ""
                                    if _pn:
                                        _hdf = load_history()
                                        _m2 = _hdf[_hdf["plate_num"] == _pn].copy()
                                        if not _m2.empty:
                                            _m2["_dt"] = pd.to_datetime(_m2["date"], errors="coerce")
                                            _latest = _m2.sort_values("_dt", ascending=False).iloc[0]
                                            _now = datetime.now()
                                            st.session_state["nr_date"] = _now.date()
                                            st.session_state["nr_hour"] = _now.hour
                                            st.session_state["nr_min"]  = _now.minute
                                            st.session_state.nr_initialized = True
                                            st.session_state.is_duplicate   = True
                                            st.session_state.is_ai_input    = False
                                            st.session_state.duplicate_data = _latest.to_dict()
                                            st.session_state.mode = "new_record"
                                            st.session_state.view_idx = None
                                            st.session_state.digits = ""
                                st.rerun()

            # ── [HTML電卓] 純粋なHTML/CSS gridで100%4列保証 ─────────────────
            # Streamlitのレスポンシブ制御を完全にバイパス
            # ボタン押下 → window.parent.document内の不可視Streamlitボタンを.click()
            components.html("""
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#000;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Helvetica,sans-serif;overflow:hidden;}
.calc{padding:6px 6px 12px;}
.fn-row{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-bottom:7px;}
.num-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;}
.btn{border:none;cursor:pointer;font-weight:700;
  display:flex;align-items:center;justify-content:center;
  text-align:center;line-height:1.2;white-space:pre-line;
  -webkit-tap-highlight-color:transparent;touch-action:manipulation;
  transition:opacity .07s,transform .07s;}
.btn:active{opacity:.55;transform:scale(.91);}
.fn-btn{height:58px;border-radius:14px;font-size:1.25rem;}
.num-btn{aspect-ratio:1/1;border-radius:50%;font-size:1.6rem;}
.act-btn{aspect-ratio:1/1;border-radius:22px;font-size:1rem;}
.empty{background:transparent;aspect-ratio:1/1;pointer-events:none;}
.c-gray{background:#a5a5a5;color:#1c1c1e;}
.c-dark{background:#333;color:#fff;}
.c-prim{background:#ff9f0a;color:#1c1c1e;}
</style>
<div class="calc">
  <div class="fn-row">
    <button class="btn fn-btn c-gray" ontouchstart="" onclick="cb('C')">C</button>
    <button class="btn fn-btn c-gray" ontouchstart="" onclick="cb('⌫')">⌫</button>
    <button class="btn fn-btn c-prim" ontouchstart="" onclick="cb('AI')">&#129302; AI</button>
  </div>
  <div class="num-grid">
    <button class="btn num-btn c-dark" ontouchstart="" onclick="cb('7')">7</button>
    <button class="btn num-btn c-dark" ontouchstart="" onclick="cb('8')">8</button>
    <button class="btn num-btn c-dark" ontouchstart="" onclick="cb('9')">9</button>
    <button class="btn act-btn c-prim" ontouchstart="" onclick="cb('新規')">&#10133;<br>新規</button>
    <button class="btn num-btn c-dark" ontouchstart="" onclick="cb('4')">4</button>
    <button class="btn num-btn c-dark" ontouchstart="" onclick="cb('5')">5</button>
    <button class="btn num-btn c-dark" ontouchstart="" onclick="cb('6')">6</button>
    <button class="btn act-btn c-prim" ontouchstart="" onclick="cb('見積')">&#x1F6DE;<br>見積</button>
    <button class="btn num-btn c-dark" ontouchstart="" onclick="cb('1')">1</button>
    <button class="btn num-btn c-dark" ontouchstart="" onclick="cb('2')">2</button>
    <button class="btn num-btn c-dark" ontouchstart="" onclick="cb('3')">3</button>
    <button class="btn act-btn c-prim" ontouchstart="" onclick="cb('予定')">&#128197;<br>予定</button>
    <button class="btn num-btn c-dark" ontouchstart="" onclick="cb('0')">0</button>
    <button class="btn act-btn c-prim" ontouchstart="" onclick="cb('複製')">&#128203;<br>複製</button>
    <div class="empty"></div>
    <button class="btn act-btn c-prim" ontouchstart="" onclick="cb('検索')">&#128269;<br>検索/履歴</button>
  </div>
</div>
<script>
function cb(lbl){
  var doc=window.parent.document;
  var btns=doc.querySelectorAll('[data-testid="stButton"] button');
  for(var i=0;i<btns.length;i++){
    var t=(btns[i].innerText||btns[i].textContent||'').replace(/[\\s\\n]+/g,' ').trim();
    /* 1文字（C/数字）は完全一致、それ以外は部分一致 */
    var hit=lbl.length<=1 ? t===lbl : t.indexOf(lbl)>=0;
    if(hit){btns[i].click();return;}
  }
}
</script>
""", height=480, scrolling=False)

    else:
        # 電卓以外のモード → bodyクラス・Observer・インラインスタイルをすべて除去
        components.html("""<script>
        (function(){
          var doc=window.parent.document;
          var b=doc.body;
          if(b) b.classList.remove('mob-calc-active');
          if(window.parent._mobForceInterval){ clearInterval(window.parent._mobForceInterval); window.parent._mobForceInterval=null; }
          if(window.parent._calcGridInterval){ clearInterval(window.parent._calcGridInterval); window.parent._calcGridInterval=null; }
          if(window.parent._calcGridObserver){ window.parent._calcGridObserver.disconnect(); window.parent._calcGridObserver=null; }
          doc.querySelectorAll('.mobile-calc-grid').forEach(function(el){ el.classList.remove('mobile-calc-grid'); });
          doc.querySelectorAll('[data-testid="stHorizontalBlock"]').forEach(function(bl){
            ['display','flex-direction','flex-wrap','gap'].forEach(function(p){ bl.style.removeProperty(p); });
          });
          doc.querySelectorAll('[data-testid="column"]').forEach(function(c){
            ['flex','min-width','max-width','width','padding','box-sizing'].forEach(function(p){ c.style.removeProperty(p); });
          });
          doc.querySelectorAll('[data-testid="stButton"]>button').forEach(function(btn){
            ['height','padding','display','align-items','justify-content'].forEach(function(p){ btn.style.removeProperty(p); });
          });
        })();
        </script>""", height=0, scrolling=False)
        # コンパクトヘッダー＋戻るボタン
        st.markdown("<div style='font-size:1rem;font-weight:800;color:#f5f5f5;padding:4px 0'>⛽ GS 接客支援</div>",
                    unsafe_allow_html=True)
        # 右パネルに専用の戻るボタンがあるモードでは表示しない（重複防止）
        _right_has_back = {"quote", "new_record", "edit_record", "view_record", "ai_input"}
        if st.session_state.mode not in _right_has_back:
            if st.button("← 戻る", key="mob_back", use_container_width=True):
                st.session_state.mode = "list"
                st.session_state.searched_plate = None
                st.rerun()
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    right = st.container()

# ════════════════════════════════════════════════════════════════════════════
#  🖥️ デスクトップ通常レイアウト
# ════════════════════════════════════════════════════════════════════════════
else:
    # ── タイトル ────────────────────────────────────────────────────────────
    st.markdown(
        "<h1 style='font-size:1.4rem;font-weight:800;color:#f5f5f5;margin-bottom:0'>⛽ GS 接客支援システム</h1>",
        unsafe_allow_html=True)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    left, right = st.columns([1, 2.4], gap="large")

    # ── LEFT ── テンキー ─────────────────────────────────────────────────────
    with left:
        st.markdown("<p style='font-size:.86rem;font-weight:700;color:#aaa;margin:0 0 8px 0'>🔢 車番下4桁で検索</p>", unsafe_allow_html=True)
        _slot = st.empty()

        KEYS = [("7","n7"),("8","n8"),("9","n9"),
                ("4","n4"),("5","n5"),("6","n6"),
                ("1","n1"),("2","n2"),("3","n3"),
                ("C","nc"),("⌫","nd"),("0","n0")]
        for i in range(0, 12, 3):
            c3 = st.columns(3)
            for col, (label, key) in zip(c3, KEYS[i:i+3]):
                with col:
                    if st.button(label, key=key, use_container_width=True):
                        if label == "C":   st.session_state.digits = ""
                        elif label == "⌫": st.session_state.digits = st.session_state.digits[:-1]
                        elif label.isdigit() and len(st.session_state.digits) < 4:
                            st.session_state.digits += label
                        if len(st.session_state.digits) == 4:
                            st.session_state.searched_plate = st.session_state.digits
                            st.session_state.digits = ""
                            st.session_state.mode = "list"
                            st.session_state.view_idx = None

        if st.button("🔍  検索", key="nsearch", type="primary", use_container_width=True):
            st.session_state.searched_plate = st.session_state.digits
            st.session_state.digits = ""
            st.session_state.mode = "list"
            st.session_state.view_idx = None

        _d = st.session_state.digits
        _slot.markdown(
            f'<div class="numpad-display"><span class="d-val">{_d}</span></div>' if _d else
            '<div class="numpad-display"><span class="d-ph">_ &nbsp;_ &nbsp;_ &nbsp;_</span></div>',
            unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        if st.button("➕ 新規来店記録", use_container_width=True, key="btn_new"):
            st.session_state.nr_initialized = False
            st.session_state.mode = "new_record"; st.session_state.view_idx = None
        if st.button("🤖 AI一括入力", use_container_width=True, key="btn_ai"):
            st.session_state.ai_parse_result = None
            st.session_state.mode = "ai_input"; st.session_state.view_idx = None
        if st.button("🛞 タイヤ見積作成", use_container_width=True, key="btn_quote"):
            st.session_state.mode = "quote";      st.session_state.view_idx = None
        if st.button("📅 予定ボード", use_container_width=True, key="btn_sched"):
            st.session_state.mode = "schedule";   st.session_state.view_idx = None

# ═══════════════════════════════════════════════════════════════════════════════
#  RIGHT
# ═══════════════════════════════════════════════════════════════════════════════
with right:
    # pq / mode はレイアウト前に定義済み（再取得で最新値を反映）
    pq   = st.session_state.searched_plate
    mode = st.session_state.mode

    # ── 初期画面 ──────────────────────────────────────────────────────────────
    if pq is None and mode not in ("new_record","edit_record","view_record","quote","schedule","ai_input"):
        if not _is_mobile:
            st.markdown("""<div style="padding:60px 32px;text-align:center;">
                <div style="font-size:3rem;margin-bottom:14px">🔍</div>
                <div style="font-size:.9rem;color:#bbb;line-height:2.4">
                    左のテンキーで車番下4桁を入力<br>
                    <span style='color:#ccc;font-size:.78rem'>空のまま「検索」→ 全記録を表示</span>
                </div></div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════════
    #  🛞 見積作成
    # ════════════════════════════════════════════════════════════════════════════
    elif mode == "quote":
        quote_step = st.session_state.get("quote_step", "hearing")

        if st.button("← 戻る", key="quote_back", use_container_width=True):
            if quote_step == "detail":
                st.session_state.quote_step = "hearing"; st.rerun()
            else:
                st.session_state.mode = "list"; st.session_state.quote_step = "hearing"; st.rerun()

        # ── STEP 1: ヒアリング ────────────────────────────────────────────────
        if quote_step == "hearing":
            st.markdown("<div style='font-size:1rem;font-weight:800;color:#f5f5f5;margin:6px 0 2px'>🛞 タイヤ見積 STEP 1 — ヒアリング</div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:.8rem;color:#aaa;margin-bottom:14px'>お客様情報とタイヤサイズを入力してください</div>", unsafe_allow_html=True)

            with st.form("hearing_form"):
                _qa, _qb = st.columns(2)
                with _qa: hf_plate    = st.text_input("🚗 車番下4桁（任意）", placeholder="1234", max_chars=4)
                with _qb: hf_staff    = st.selectbox("👷 担当者名（必須）", STAFF_OPTIONS)
                _qc, _qd = st.columns(2)
                with _qc: hf_size     = st.text_input("🛞 タイヤサイズ（必須）", placeholder="195/65R15")
                with _qd: hf_customer = st.text_input("👤 お客様名（任意）", placeholder="山田 太郎 様")
                _qe, _qf = st.columns(2)
                with _qe: hf_maker    = st.text_input("🏭 メーカー（任意）", placeholder="トヨタ")
                with _qf: hf_model    = st.text_input("🚙 車種（任意）", placeholder="プリウス")
                next_btn = st.form_submit_button("見積を作成する →", type="primary", use_container_width=True)

            if next_btn:
                if hf_staff == "(未選択)" or not hf_size:
                    st.error("担当者名とタイヤサイズは必須です")
                else:
                    st.session_state.q_hearing_plate    = hf_plate
                    st.session_state.q_hearing_maker    = hf_maker
                    st.session_state.q_hearing_model    = hf_model
                    st.session_state.q_hearing_customer = hf_customer
                    st.session_state.q_hearing_staff    = hf_staff
                    _parsed_sz = parse_tire_size(hf_size)
                    st.session_state.q_hearing_size     = _parsed_sz
                    st.session_state.q_num_products     = 3
                    # 各商品のタイヤサイズをデフォルト値でリセット
                    for _pi in range(3):
                        st.session_state[f"q_size_{_pi}"] = _parsed_sz
                    st.session_state.quote_step = "detail"
                    st.session_state.q_preset_idx = 0
                    st.rerun()

        # ── STEP 2: 見積詳細 ──────────────────────────────────────────────────
        else:
            hs_plate    = st.session_state.get("q_hearing_plate", "")
            hs_maker    = st.session_state.get("q_hearing_maker", "")
            hs_model    = st.session_state.get("q_hearing_model", "")
            hs_customer = st.session_state.get("q_hearing_customer", "")
            hs_staff    = st.session_state.get("q_hearing_staff", "")
            hs_size     = st.session_state.get("q_hearing_size", "")
            num_products = st.session_state.get("q_num_products", 1)

            # ヒアリング情報帯
            st.markdown(f"""
            <div style="background:#0d2818;border:1.5px solid #2e7d32;
                        border-radius:14px;padding:12px 16px;margin-bottom:14px;
                        display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr;gap:8px">
                <div><div style="font-size:.68rem;color:#999;margin-bottom:2px">車番</div>
                     <div style="font-weight:700;color:#f0f0f0">{hs_plate or '－'}</div></div>
                <div><div style="font-size:.68rem;color:#999;margin-bottom:2px">車両</div>
                     <div style="font-weight:700;color:#f0f0f0">{(hs_maker+' '+hs_model).strip() or '－'}</div></div>
                <div><div style="font-size:.68rem;color:#999;margin-bottom:2px">お客様</div>
                     <div style="font-weight:700;color:#f0f0f0">{hs_customer or '－'}</div></div>
                <div><div style="font-size:.68rem;color:#999;margin-bottom:2px">担当</div>
                     <div style="font-weight:700;color:#f0f0f0">{hs_staff}</div></div>
                <div><div style="font-size:.68rem;color:#999;margin-bottom:2px">デフォルトサイズ</div>
                     <div style="font-weight:700;color:#2563eb">{hs_size}</div></div>
            </div>""", unsafe_allow_html=True)

            st.markdown("<div style='font-size:1rem;font-weight:800;color:#f5f5f5;margin:0 0 8px 0'>🛞 STEP 2 — 見積詳細</div>", unsafe_allow_html=True)

            # タイヤ価格マスタ
            tire_df = load_tire_prices()
            tire_df["retail_price"] = pd.to_numeric(tire_df["retail_price"], errors="coerce").fillna(0).astype(int)

            # ── 商品入力関数 ─────────────────────────────────────────────────────
            def _render_product_inputs(pidx: int) -> dict:
                """pidx=0/1/2 の各商品入力UIを描画し、計算結果dictを返す。"""
                qs_key       = f"q_size_{pidx}"
                tm_key       = f"q_tm_{pidx}"
                tp_key       = f"q_tp_{pidx}"
                ret_key      = f"q_retail_manual_{pidx}"
                qty_key      = f"q_qty_{pidx}"
                preset_key_r = f"q_preset_radio_{pidx}"
                ou_key_pfx   = f"ou_{pidx}"
                ol_key_pfx   = f"ol_{pidx}"
                od_key_pfx   = f"od_{pidx}"

                # ── 個別クリアボタン（上部） ─────────────────────────────────────────
                def _do_clear():
                    # del ではなく明示的に空値をセット（del するとStreamlit内部キャッシュが
                    # 残り、他商品クリア後の再レンダリングで旧値が復活するゾンビ問題を防止）
                    st.session_state[qs_key] = hs_size
                    st.session_state[tm_key] = "(未選択)"
                    st.session_state[tp_key] = "" if matched_p.empty else "(選択なし)"
                    st.session_state[ret_key] = 0
                    st.session_state[qty_key] = 4
                    st.session_state[preset_key_r] = 0
                    for _k in list(st.session_state.keys()):
                        if any(_k.startswith(_p) for _p in [ou_key_pfx, ol_key_pfx, od_key_pfx]):
                            del st.session_state[_k]

                _hdr_l, _hdr_r = st.columns([3, 1])
                with _hdr_l:
                    st.markdown(
                        f"<div style='font-size:.78rem;color:#aaa;padding-top:6px'>"
                        f"🛞 各フィールドを独立入力できます</div>",
                        unsafe_allow_html=True)
                with _hdr_r:
                    st.button("🔄 クリア", key=f"clear_slot_{pidx}",
                              on_click=_do_clear, use_container_width=True)

                # ── タイヤサイズ入力（数字7桁→自動フォーマット） ───────────────────
                if qs_key not in st.session_state:
                    st.session_state[qs_key] = hs_size
                st.text_input(
                    "🛞 タイヤサイズ（7桁入力可: 2055517→205/55R17）",
                    key=qs_key,
                    placeholder="205/55R17 または 2055517",
                    on_change=_Q_SIZE_CBS[pidx],
                )
                size_p = st.session_state.get(qs_key, hs_size) or hs_size
                matched_p = tire_df[tire_df["size"] == size_p]

                td1, td2, td3 = st.columns([2, 2, 1])
                with td1:
                    q_tm_p = st.selectbox("タイヤメーカー", TIRE_MAKER_OPTIONS, key=tm_key)
                if matched_p.empty:
                    with td2:
                        st.warning(f"「{size_p}」に一致する商品がありません。手動入力してください。")
                        q_tp_p = st.text_input("商品名", placeholder="ECOPIA EP300", key=tp_key,
                                               on_change=_Q_TP_CBS[pidx])
                    with td3:
                        retail_price_p = st.number_input("定価/本（税込）", min_value=0, value=0, step=500,
                                                         key=ret_key, format="%d")
                else:
                    # "(選択なし)" を先頭に追加 → 未選択 = 未入力として正確に判定
                    products_p = ["(選択なし)"] + matched_p["product_name"].tolist()
                    with td2:
                        q_tp_p_raw = st.selectbox("商品名（サイズ自動絞込）", products_p, key=tp_key,
                                                  on_change=_Q_TP_CBS[pidx])
                    q_tp_p = "" if q_tp_p_raw == "(選択なし)" else q_tp_p_raw
                    if q_tp_p:
                        row_m = matched_p[matched_p["product_name"] == q_tp_p]
                        retail_price_p = int(row_m["retail_price"].iloc[0]) if not row_m.empty else 0
                    else:
                        retail_price_p = 0
                    with td3:
                        if retail_price_p > 0:
                            st.markdown(f"""
                            <div style="background:#0f2a16;border:1px solid #2e7d32;border-radius:10px;
                                        padding:8px 12px;text-align:center">
                                <div style="font-size:.7rem;color:#999;margin-bottom:2px">定価/本（税込）</div>
                                <div style="font-size:1.1rem;font-weight:800;color:#66bb6a">¥{retail_price_p:,}</div>
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background:#1a1a1a;border:1px solid #333;border-radius:10px;
                                        padding:8px 12px;text-align:center">
                                <div style="font-size:.7rem;color:#555">商品を選択</div>
                            </div>""", unsafe_allow_html=True)

                q_qty_p = st.selectbox("本数", [4, 2, 1], key=qty_key)
                a_price_p = round(retail_price_p * 0.70)

                st.markdown("<div class='sec-title'>⚡ 値引きプリセット</div>", unsafe_allow_html=True)
                preset_idx_p = st.radio(
                    "プリセット選択",
                    options=list(range(len(PRESET_LABELS))),
                    format_func=lambda i: PRESET_LABELS[i],
                    key=preset_key_r,
                    horizontal=False,
                    label_visibility="collapsed",
                )
                pkey = f"{ou_key_pfx}_{preset_idx_p}"

                if preset_idx_p == 0:
                    dou, dol, dod = retail_price_p, STD_LABOR, STD_DISP
                elif preset_idx_p == 1:
                    dou, dol, dod = round(retail_price_p / 1.1), STD_LABOR, STD_DISP
                elif preset_idx_p == 2:
                    dou, dol, dod = retail_price_p, 0, STD_DISP
                elif preset_idx_p == 3:
                    dou, dol, dod = retail_price_p, 0, 0
                else:
                    dou, dol, dod = a_price_p, 0, 0

                st.markdown("<div class='sec-title'>📝 提示価格（1本あたり・税込）</div>", unsafe_allow_html=True)
                ni1, ni2, ni3 = st.columns(3)
                with ni1:
                    offer_unit_p  = st.number_input("🛞 提示タイヤ単価/本", min_value=0, value=dou, step=100,
                                                    key=f"{ou_key_pfx}_{pkey}", format="%d")
                with ni2:
                    offer_labor_p = st.number_input("🔧 提示工賃/本",       min_value=0, value=dol, step=100,
                                                    key=f"{ol_key_pfx}_{pkey}", format="%d")
                with ni3:
                    offer_disp_p  = st.number_input("♻️ 提示廃タイヤ/本",   min_value=0, value=dod, step=50,
                                                    key=f"{od_key_pfx}_{pkey}", format="%d")

                if retail_price_p > 0 and offer_unit_p < a_price_p:
                    st.markdown(f"""
                    <div class="acheck-ng" style="margin:6px 0">
                        <div style="font-size:1rem">⚠️ <b>A表割れ注意</b></div>
                        <div style="font-size:.82rem;color:#991b1b;margin-top:4px">
                            提示単価 ¥{offer_unit_p:,} ＜ A表価格 ¥{a_price_p:,}（定価70%）&nbsp;／&nbsp;差額 <b>-¥{a_price_p - offer_unit_p:,}</b>/本
                        </div>
                    </div>""", unsafe_allow_html=True)
                elif retail_price_p > 0:
                    st.markdown(f'<div class="acheck-ok" style="margin:6px 0">✅ A表クリア（A表価格 ¥{a_price_p:,} 以上）</div>', unsafe_allow_html=True)

                r_tire_p  = retail_price_p * q_qty_p
                r_labor_p = STD_LABOR      * q_qty_p
                r_disp_p  = STD_DISP       * q_qty_p
                r_total_p = r_tire_p + r_labor_p + r_disp_p
                o_tire_p  = offer_unit_p  * q_qty_p
                o_labor_p = offer_labor_p * q_qty_p
                o_disp_p  = offer_disp_p  * q_qty_p
                o_total_p = o_tire_p + o_labor_p + o_disp_p
                savings_p  = r_total_p - o_total_p
                save_pct_p = round(savings_p / r_total_p * 100, 1) if r_total_p > 0 else 0.0

                st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                col_r, col_o = st.columns(2, gap="medium")
                with col_r:
                    st.markdown(f"""
                    <div style="background:#1a2128;border:1.5px solid #4a5a64;border-radius:14px;padding:14px 16px">
                    <div style="font-size:.9rem;font-weight:800;color:#b0c4cf;margin-bottom:8px">📋 定価（税込）</div>
                    <div class="q-row"><span class="q-label">🛞 タイヤ代（{q_qty_p}本）</span><span class="q-val">¥{r_tire_p:,}</span></div>
                    <div class="q-row"><span class="q-label">🔧 工賃（{q_qty_p}本）</span><span class="q-val">¥{r_labor_p:,}</span></div>
                    <div class="q-row"><span class="q-label">♻️ 廃タイヤ（{q_qty_p}本）</span><span class="q-val">¥{r_disp_p:,}</span></div>
                    <div style="font-size:1.1rem;font-weight:800;color:#b0c4cf;padding-top:10px;margin-top:6px;border-top:2px solid #4a5a64;display:flex;justify-content:space-between">
                        <span>定価合計（税込）</span><span>¥{r_total_p:,}</span>
                    </div>
                    </div>""", unsafe_allow_html=True)
                with col_o:
                    st.markdown(f"""
                    <div style="background:#0f2a16;border:1.5px solid #388e3c;border-radius:14px;padding:14px 16px">
                    <div style="font-size:.9rem;font-weight:800;color:#66bb6a;margin-bottom:8px">⭐ 提示価格（税込）</div>
                    <div class="q-row"><span class="q-label">🛞 タイヤ代（{q_qty_p}本）</span><span class="q-val">¥{o_tire_p:,}</span></div>
                    <div class="q-row"><span class="q-label">🔧 工賃（{q_qty_p}本）</span><span class="q-val">¥{o_labor_p:,}</span></div>
                    <div class="q-row"><span class="q-label">♻️ 廃タイヤ（{q_qty_p}本）</span><span class="q-val">¥{o_disp_p:,}</span></div>
                    <div style="font-size:1.2rem;font-weight:800;color:#81c784;padding-top:10px;margin-top:6px;border-top:2px solid #388e3c;display:flex;justify-content:space-between">
                        <span>提示合計（税込）</span><span>¥{o_total_p:,}</span>
                    </div>
                    </div>""", unsafe_allow_html=True)

                sc_color = "#c62828" if savings_p > 0 else "#888"
                _off_txt = f"({save_pct_p}% OFF)" if savings_p > 0 else ""
                st.markdown(f"""
<div style="background:#2a0e1e;border:2px solid #c2185b;border-radius:14px;padding:14px 20px;margin:10px 0;display:flex;justify-content:space-between;align-items:center">
<div><div style="font-size:.78rem;font-weight:700;color:#f48fb1;margin-bottom:4px">🎉 お得額</div><div style="font-size:.75rem;color:#aaa">定価 ¥{r_total_p:,} → 提示 ¥{o_total_p:,}</div></div>
<div style="text-align:right"><span style="font-size:2rem;font-weight:800;color:{sc_color}">¥{abs(savings_p):,}</span><span style="font-size:1.1rem;font-weight:700;color:#f06292;margin-left:6px">{_off_txt}</span></div>
</div>""", unsafe_allow_html=True)

                return {
                    "q_tm": q_tm_p, "q_tp": q_tp_p,
                    "retail_price": retail_price_p, "q_qty": q_qty_p,
                    "offer_unit": offer_unit_p, "offer_labor": offer_labor_p, "offer_disp": offer_disp_p,
                    "o_total": o_total_p, "r_total": r_total_p, "savings": savings_p,
                    "size_p": size_p,
                }

            # ── 商品A・B・C 常設3タブ ──────────────────────────────────────────
            PROD_LABELS = ["商品A", "商品B", "商品C"]
            products_data = []

            # 各商品のタイヤサイズ初期化（未設定の場合のみ）
            for _pi in range(3):
                _sz_key = f"q_size_{_pi}"
                if _sz_key not in st.session_state:
                    st.session_state[_sz_key] = hs_size

            tabs = st.tabs(PROD_LABELS)
            for pidx, tab in enumerate(tabs):
                with tab:
                    res = _render_product_inputs(pidx)
                    products_data.append(res)

            # デフォルト参照は商品A
            q_tm = products_data[0]["q_tm"]; q_tp = products_data[0]["q_tp"]
            retail_price = products_data[0]["retail_price"]; q_qty = products_data[0]["q_qty"]
            offer_unit = products_data[0]["offer_unit"]; offer_labor = products_data[0]["offer_labor"]
            offer_disp = products_data[0]["offer_disp"]
            o_total = products_data[0]["o_total"]

            # ── 比較サマリー（入力済み商品のみ） ──────────────────────────────────
            filled_summary = [p for p in products_data if p.get("q_tp") or p.get("retail_price", 0) > 0]
            if filled_summary:
                st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:.9rem;font-weight:800;color:#f5f5f5;margin-bottom:8px'>📊 比較サマリー（入力済み商品）</div>", unsafe_allow_html=True)
                best_total = min(p["o_total"] for p in filled_summary) if any(p["o_total"] > 0 for p in filled_summary) else 0
                cmp_cols = st.columns(len(filled_summary), gap="small")
                for col, pdata in zip(cmp_cols, filled_summary):
                    pidx_f = products_data.index(pdata)
                    is_best = pdata["o_total"] == best_total and best_total > 0
                    border_c = "#2e7d32" if is_best else "#383838"
                    bg_c = "#0a2010" if is_best else "#1a1a1a"
                    badge = " 🏆 最安" if is_best else ""
                    with col:
                        st.markdown(f"""
                        <div style="background:{bg_c};border:2px solid {border_c};border-radius:12px;padding:12px 14px;margin-bottom:8px">
                            <div style="font-size:.82rem;font-weight:800;color:#f5f5f5;margin-bottom:6px">{PROD_LABELS[pidx_f]}{badge}</div>
                            <div style="font-size:.75rem;color:#aaa;margin-bottom:4px">{pdata['q_tp'] or '未入力'}</div>
                            <div style="font-size:.72rem;color:#aaa">{pdata.get('size_p','')} {pdata['q_qty']}本</div>
                            <div style="font-size:1.2rem;font-weight:800;color:#81c784;margin-top:6px">¥{pdata['o_total']:,}</div>
                            <div style="font-size:.7rem;color:#f06292;margin-top:2px">お得額 ¥{pdata['savings']:,}</div>
                        </div>""", unsafe_allow_html=True)

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("<div class='sec-title'>✏️ 接客メモ</div>", unsafe_allow_html=True)
            q_memo = st.text_area("接客メモ", placeholder="お客様要望・タイヤ状態・次回案内など", height=100, key="q_memo", label_visibility="collapsed")

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            pa, pb, pc, pd_ = st.columns(4)
            with pa:
                do_print = st.button("📄 見積書プレビュー・印刷", use_container_width=True, key="do_print")
            with pb:
                do_save = st.button("📋 履歴に保存", type="primary", use_container_width=True, key="save_quote")
            with pc:
                if st.button("📅 予約を追加", use_container_width=True, key="quote_to_sched"):
                    _tp_info = " / ".join(
                        filter(None, [f"{PROD_LABELS[i]}: {p['q_tp']}" for i, p in enumerate(products_data) if p["q_tp"]])
                    )
                    _detail = " ".join(filter(None, [hs_size, _tp_info]))
                    import datetime as _dt
                    _today_str = _dt.date.today().strftime("%Y/%m/%d")
                    _inject_dialog_state_new(_today_str, "10:00", "タイヤ交換（4本）", 60, True, False, "")
                    st.session_state["uf_memo"]             = _detail
                    st.session_state["uf_mode"]             = "new"
                    st.session_state["uf_prefill"]          = {"plate_num": hs_plate[-4:] if len(hs_plate) >= 4 else hs_plate}
                    st.session_state["show_booking_dialog"] = True
                    st.session_state["show_sched_history"]  = False
                    st.session_state.mode = "schedule"
                    st.session_state.quote_step = "hearing"; st.rerun()
            with pd_:
                if st.button("閉じる", use_container_width=True, key="close_quote"):
                    st.session_state.mode = "list"; st.session_state.quote_step = "hearing"; st.rerun()

            if do_print or st.session_state.get("show_print"):
                st.session_state["show_print"] = True
                _filled_print = [p for p in products_data if p.get("q_tp") or p.get("retail_price", 0) > 0]
                if not _filled_print:
                    st.warning("商品情報を入力してください（商品名または定価が必要です）")
                    st.session_state["show_print"] = False
                else:
                    _print_labels = [PROD_LABELS[products_data.index(p)] for p in _filled_print]
                    html_str = generate_estimate_html_multi(
                        _filled_print, _print_labels,
                        hs_plate, hs_customer, hs_staff,
                        hs_maker, hs_model, q_memo
                    )
                    components.html(html_str, height=1080, scrolling=True)
                    if st.button("プレビューを閉じる", key="close_print"):
                        st.session_state["show_print"] = False; st.rerun()
            else:
                st.session_state["show_print"] = False

            if do_save:
                # 入力済み商品のみメモに展開して1レコード保存
                _filled_save = [p for p in products_data if p.get("q_tp") or p.get("retail_price", 0) > 0]
                lines = []
                for pdata in _filled_save:
                    pidx_s = products_data.index(pdata)
                    lbl = PROD_LABELS[pidx_s]
                    size_str = pdata.get("size_p", hs_size)
                    lines.append(
                        f"[{lbl}]【タイヤ見積】{opt(pdata['q_tm'])} {pdata['q_tp']} {size_str} / {pdata['q_qty']}本 "
                        f"/ 定価¥{pdata['retail_price']:,}→提示¥{pdata['offer_unit']:,}/本 / 合計¥{pdata['o_total']:,} "
                        f"/ お得額¥{pdata['savings']:,}"
                    )
                note = "\n".join(lines) + (f"\n{q_memo}" if q_memo else "")
                # tire_maker / tire_product は商品Aで代表
                append_record({
                    "date": datetime.now().strftime("%Y/%m/%d %H:%M"),
                    "purpose": "タイヤ見積",
                    "cust_type": "", "plate_area": "", "plate_3digit": "", "plate_kana": "",
                    "plate_num": hs_plate, "maker": hs_maker, "car_model": hs_model,
                    "color": "", "age": "", "gender": "",
                    "tire_size": hs_size, "tire_size_num": tire_to_num(hs_size),
                    "tire_year": "", "tire_maker": opt(products_data[0]["q_tm"]),
                    "tire_product": products_data[0]["q_tp"],
                    "memo": note,
                })
                st.success("見積を保存しました！")
                st.session_state.mode = "list"; st.session_state.searched_plate = hs_plate or ""
                st.session_state.quote_step = "hearing"; st.rerun()

    # ════════════════════════════════════════════════════════════════════════════
    #  📅 予定ボード / スマート予約
    # ════════════════════════════════════════════════════════════════════════════
    elif mode == "schedule":
        _tab_board, _tab_booking, _tab_loaner = st.tabs([
            "📋 ホワイトボード（ベテラン用メモ）",
            "🗓️ スマート予約（空き確認）",
            "🚙 代車貸出管理表",
        ])
        _gs_force_tab = st.session_state.pop("gs_force_tab", None)
        if _gs_force_tab:
            _gs_txt = "スマート予約" if _gs_force_tab == "sb" else "代車貸出"
            components.html(f"""<script>
(function(){{
  var pd=document;try{{if(window.parent&&window.parent!==window)pd=window.parent.document;}}catch(e){{}}
  function tryTab(){{
    var btns=pd.querySelectorAll('[data-baseweb="tab"]');
    for(var i=0;i<btns.length;i++)if(btns[i].textContent.indexOf('{_gs_txt}')>=0){{btns[i].click();return true;}}
    return false;
  }}
  if(!tryTab()){{
    var ob=new MutationObserver(function(m,o){{if(tryTab())o.disconnect();}});
    ob.observe(pd.body||document.body,{{childList:true,subtree:true}});
    setTimeout(function(){{ob.disconnect();}},2000);
  }}
}})();
</script>""", height=0)
        with _tab_board:
            render_schedule_board_tab()
        with _tab_booking:
            render_smart_booking_tab()
        with _tab_loaner:
            render_loaner_board_tab()
        if st.session_state.get("show_overtime_warning"):
            st.session_state["show_overtime_warning"] = False  # 1回だけ消費
            _overtime_warning_dialog()
        if st.session_state.get("show_booking_dialog"):
            st.session_state["show_booking_dialog"] = False  # 1回だけ消費（Escape 暴走を防止）
            _unified_booking_form()
        if st.session_state.get("show_wb_quick_add"):
            st.session_state["show_wb_quick_add"] = False    # 1回だけ消費
            _wb_quick_add_form()
        if st.session_state.get("show_archive_dialog"):
            st.session_state["show_archive_dialog"] = False  # 1回だけ消費
            _archive_detail_dialog()
        if st.session_state.pop("booking_saved_success", False):
            st.toast("📅 予約を正常に登録しました！ グリッドに即時反映されています。", icon="✅")

    # ════════════════════════════════════════════════════════════════════════════
    #  🤖 AI一括入力
    # ════════════════════════════════════════════════════════════════════════════
    elif mode == "ai_input":
        if st.button("← 戻る", key="ai_back", use_container_width=True):
            st.session_state.ai_parse_result = None
            st.session_state.mode = "list"; st.rerun()

        st.markdown("<div style='font-size:.98rem;font-weight:800;color:#f5f5f5;margin:8px 0 4px'>🤖 AI一括入力</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#999;font-size:.86rem;margin:0 0 14px'>接客メモを自由に貼り付けてください。AIが各項目に自動で分類します。</p>", unsafe_allow_html=True)

        # ── 入力エリア ────────────────────────────────────────────────────────
        memo_text = st.text_area(
            "📝 接客メモ（自由形式）",
            value=st.session_state.get("ai_memo_text", ""),
            height=150,
            placeholder=(
                "例：10:21 香川 333 あ 3666 ダイハツ EXE 黒 40代男\n"
                "    タイヤ 1556514 製造24年 BSのREGNO\n"
                "    給油のみ。次回タイヤ交換検討中とのこと。"
            ),
            key="ai_memo_area",
        )
        st.session_state.ai_memo_text = memo_text

        parse_col, _ = st.columns([1, 2])
        with parse_col:
            parse_btn = st.button(
                "🔍 AIで解析する",
                type="primary",
                use_container_width=True,
                disabled=not memo_text.strip(),
            )

        if parse_btn and memo_text.strip():
            with st.spinner("AIが解析中..."):
                _ref_date = get_last_record_date().strftime("%Y/%m/%d")
                result, err = ai_parse_record(memo_text, ref_date=_ref_date)
            if err:
                st.warning(f"AI解析できませんでした: {err}\n\n入力内容をメモ欄に転記して手動入力フォームに進みます。")
                _now = datetime.now()
                fallback = {"date": f"{_ref_date} {_now.strftime('%H:%M')}", "memo": memo_text}
                st.session_state.ai_parse_result = fallback
            else:
                st.session_state.ai_parse_result = result

        # ── プレビュー ────────────────────────────────────────────────────────
        ai_res = st.session_state.get("ai_parse_result")
        if ai_res:
            st.markdown("---")
            st.markdown("<div class='sec-title'>📋 解析結果プレビュー（確認・修正は次の画面で）</div>", unsafe_allow_html=True)

            def _pv(label, val):
                disp = val if val else "<span style='color:#ccc'>—</span>"
                return f"<div style='margin-bottom:10px'><div style='font-size:.73rem;color:#999'>{label}</div><div style='font-size:.9rem;font-weight:600;color:#f0f0f0'>{disp}</div></div>"

            r = ai_res
            plate_str = " ".join(filter(None, [r.get("plate_area",""), r.get("plate_3digit",""), r.get("plate_kana",""), r.get("plate_num","")]))
            car_str   = " ".join(filter(None, [r.get("maker",""), r.get("car_model","")]))
            age_str   = " ".join(filter(None, [r.get("age",""), r.get("gender","")]))

            g1, g2, g3 = st.columns(3)
            with g1:
                st.markdown(_pv("日時",     r.get("date","")),      unsafe_allow_html=True)
                st.markdown(_pv("来店目的", r.get("purpose","")),   unsafe_allow_html=True)
                st.markdown(_pv("種別",     r.get("cust_type","")), unsafe_allow_html=True)
                st.markdown(_pv("ナンバー", plate_str),             unsafe_allow_html=True)
            with g2:
                st.markdown(_pv("車両",       car_str),               unsafe_allow_html=True)
                st.markdown(_pv("カラー",     r.get("color","")),     unsafe_allow_html=True)
                st.markdown(_pv("年齢/性別",  age_str),               unsafe_allow_html=True)
            with g3:
                st.markdown(_pv("タイヤサイズ",   r.get("tire_size","")),    unsafe_allow_html=True)
                st.markdown(_pv("製造年",         r.get("tire_year","")),    unsafe_allow_html=True)
                st.markdown(_pv("タイヤメーカー", r.get("tire_maker","")),   unsafe_allow_html=True)
                st.markdown(_pv("商品名",         r.get("tire_product","")), unsafe_allow_html=True)

            if r.get("memo"):
                st.markdown(_pv("備考", r.get("memo","")), unsafe_allow_html=True)

            st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)
            ok_col, ng_col = st.columns([2, 1])
            with ok_col:
                if st.button("✅ 入力フォームに反映する", type="primary", use_container_width=True):
                    # ── 日時
                    _d0, _h0, _m0 = _parse_dt(r.get("date", ""))
                    st.session_state["nr_date"]  = _d0
                    st.session_state["nr_hour"]  = _h0
                    st.session_state["nr_min"]   = _m0
                    # ── 来店情報
                    _rp = r.get("purpose", "")
                    st.session_state["nr_purpose"] = _rp if _rp in PURPOSE_OPTIONS else PURPOSE_OPTIONS[0]
                    _rc = r.get("cust_type", "")
                    st.session_state["nr_ctype"]   = _rc if _rc in CUST_TYPE_OPTIONS else "一般"
                    # ── ナンバー
                    _ra = r.get("plate_area", "")
                    st.session_state["nr_area"]   = _ra if _ra in PLATE_AREAS else "(未選択)"
                    st.session_state["nr_3digit"] = r.get("plate_3digit", "")
                    _rk = r.get("plate_kana", "")
                    st.session_state["nr_kana"]   = _rk if _rk in KANA_OPTIONS else "(未選択)"
                    st.session_state["nr_num"]    = r.get("plate_num", "")
                    # ── 車両（車種→メーカー・サイズ自動推定込み）
                    _rcar = r.get("car_model", "")
                    _rmk  = r.get("maker", "")
                    _rsz  = r.get("car_size", "")
                    _inf_mk, _inf_sz = infer_car_info(_rcar)
                    st.session_state["nr_car"]      = _rcar
                    st.session_state["nr_maker"]    = _rmk if _rmk in MAKER_OPTIONS else _inf_mk or "(未選択)"
                    st.session_state["nr_car_size"] = _rsz if _rsz in SIZE_OPTIONS else _inf_sz or "(未選択)"
                    _rcl = r.get("color", "")
                    st.session_state["nr_color"]    = _rcl if _rcl in COLOR_OPTIONS else "(未選択)"
                    _rage = r.get("age", "")
                    st.session_state["nr_age"]      = _rage if _rage in AGE_OPTIONS else "(未選択)"
                    _rgd = r.get("gender", "無記名")
                    st.session_state["nr_gender"]   = _rgd if _rgd in GENDER_OPTIONS else "無記名"
                    # ── タイヤ（商品名→メーカー自動推定込み）
                    _rtp = r.get("tire_product", "")
                    _rtm = r.get("tire_maker", "")
                    st.session_state["nr_tsize"]    = r.get("tire_size", "")
                    st.session_state["nr_tyear"]    = norm_tyear(r.get("tire_year", ""))
                    st.session_state["nr_tprod"]    = _rtp
                    st.session_state["nr_tmaker"]   = _rtm if _rtm in TIRE_MAKER_OPTIONS else infer_tire_maker(_rtp) or "(未選択)"
                    # ── 担当者・備考
                    _rst = r.get("staff", "")
                    st.session_state["nr_staff"]    = _rst if _rst in STAFF_OPTIONS else "(未選択)"
                    st.session_state["nr_memo"]     = r.get("memo", "")
                    # ── フラグ（初期化ブロックをスキップ／重複アラートをクリア）
                    st.session_state["nr_plate_match"]  = None
                    st.session_state["nr_initialized"]  = True
                    st.session_state.is_duplicate    = True
                    st.session_state.is_ai_input     = True
                    st.session_state.duplicate_data  = r
                    st.session_state.ai_parse_result = None
                    st.session_state.ai_memo_text    = ""
                    st.session_state.mode = "new_record"
                    st.rerun()
            with ng_col:
                if st.button("🔄 やり直す", use_container_width=True):
                    st.session_state.ai_parse_result = None
                    st.rerun()

    # ════════════════════════════════════════════════════════════════════════════
    #  ➕ 新規来店記録
    # ════════════════════════════════════════════════════════════════════════════
    elif mode == "new_record":
        is_dup      = st.session_state.get("is_duplicate", False)
        is_ai_input = st.session_state.get("is_ai_input", False)
        dup         = st.session_state.get("duplicate_data", {})

        if is_ai_input:
            st.markdown("""
            <div style="background:#0f1f3d;border:1.5px solid #2563eb;border-radius:12px;
                        padding:10px 16px;margin-bottom:10px;display:flex;align-items:center;gap:10px">
                <span style="font-size:1.3rem">🤖</span>
                <div>
                    <div style="font-size:.9rem;font-weight:800;color:#93c5fd">AIが解析した内容を下書き中</div>
                    <div style="font-size:.76rem;color:#60a5fa;margin-top:1px">内容を確認・修正してから保存してください</div>
                </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<div class='sec-title'>🤖 AI一括入力 → 確認・修正</div>", unsafe_allow_html=True)
        elif is_dup:
            st.markdown("""
            <div style="background:#2a2000;border:1.5px solid #f59e0b;border-radius:12px;
                        padding:10px 16px;margin-bottom:10px;display:flex;align-items:center;gap:10px">
                <span style="font-size:1.3rem">📋</span>
                <div>
                    <div style="font-size:.9rem;font-weight:800;color:#fcd34d">履歴をコピーして作成中</div>
                    <div style="font-size:.76rem;color:#f9c74f;margin-top:1px">元の日時を引き継いでいます。必要に応じて変更してください。</div>
                </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<div class='sec-title'>📋 複製して新規来店記録</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='sec-title'>➕ 新規来店記録</div>", unsafe_allow_html=True)

        # ── セッション初期化（新規モード突入時のみリセット）─────────────────────
        if not st.session_state.get("nr_initialized"):
            _n = datetime.now()
            if is_dup and dup.get("date",""):
                _dup_date, _dup_h, _dup_m = _parse_dt(dup["date"])
                st.session_state["nr_date"] = _dup_date
                st.session_state["nr_hour"] = _dup_h
                st.session_state["nr_min"]  = _dup_m
            else:
                st.session_state["nr_date"] = get_last_record_date()
                st.session_state["nr_hour"] = _n.hour
                st.session_state["nr_min"]  = _n.minute
            # 来店情報
            st.session_state["nr_purpose"] = dup.get("purpose", PURPOSE_OPTIONS[0]) if is_dup and dup.get("purpose","") in PURPOSE_OPTIONS else PURPOSE_OPTIONS[0]
            _ctype0 = dup.get("cust_type","") if is_dup else ""
            st.session_state["nr_ctype"]   = _ctype0 if _ctype0 in CUST_TYPE_OPTIONS else "一般"
            # ナンバー
            st.session_state["nr_area"]    = dup.get("plate_area","(未選択)") if is_dup else "(未選択)"
            st.session_state["nr_3digit"]  = dup.get("plate_3digit","") if is_dup else ""
            st.session_state["nr_kana"]    = dup.get("plate_kana","(未選択)") if is_dup else "(未選択)"
            st.session_state["nr_num"]     = dup.get("plate_num","") if is_dup else ""
            # 車両（車種→メーカー・サイズ自動推定）
            _car0    = dup.get("car_model","") if is_dup else ""
            _maker0  = dup.get("maker","") if is_dup else ""
            _size0   = dup.get("car_size","") if is_dup else ""
            _inf_maker, _inf_size = infer_car_info(_car0)
            st.session_state["nr_car"]      = _car0
            st.session_state["nr_maker"]    = (_maker0 if _maker0 in MAKER_OPTIONS else _inf_maker or "(未選択)")
            st.session_state["nr_car_size"] = (_size0 if _size0 in SIZE_OPTIONS else _inf_size or "(未選択)")
            _color0  = dup.get("color","(未選択)") if is_dup else "(未選択)"
            st.session_state["nr_color"]   = _color0 if _color0 in COLOR_OPTIONS else "(未選択)"
            _age0    = dup.get("age","(未選択)") if is_dup else "(未選択)"
            st.session_state["nr_age"]     = _age0 if _age0 in AGE_OPTIONS else "(未選択)"
            _gender0 = dup.get("gender","無記名") if is_dup else "無記名"
            st.session_state["nr_gender"]  = _gender0 if _gender0 in GENDER_OPTIONS else "無記名"
            # タイヤ（商品名→メーカー自動推定）
            _tprod0  = dup.get("tire_product","") if is_dup else ""
            _tmaker0 = dup.get("tire_maker","") if is_dup else ""
            st.session_state["nr_tsize"]   = dup.get("tire_size","") if is_dup else ""
            st.session_state["nr_tyear"]   = norm_tyear(dup.get("tire_year","") if is_dup else "")
            st.session_state["nr_tprod"]   = _tprod0
            st.session_state["nr_tmaker"]  = (_tmaker0 if _tmaker0 in TIRE_MAKER_OPTIONS else infer_tire_maker(_tprod0) or "(未選択)")
            # 担当者
            _staff0  = dup.get("staff","(未選択)") if is_dup else "(未選択)"
            st.session_state["nr_staff"]   = _staff0 if _staff0 in STAFF_OPTIONS else "(未選択)"
            st.session_state["nr_memo"]    = dup.get("memo","") if is_dup else ""
            # 車検日・天気
            _sd0 = dup.get("shaken_date","") if is_dup else ""
            try:
                st.session_state["nr_shaken_date"] = pd.to_datetime(_sd0).date() if _sd0 else None
            except Exception:
                st.session_state["nr_shaken_date"] = None
            _wt0 = dup.get("weather","") if is_dup else ""
            st.session_state["nr_weather"] = _wt0 if _wt0 in WEATHER_OPTIONS else "(未選択)"
            _ac0 = dup.get("air_check","") if is_dup else ""
            st.session_state["nr_air_check"] = _ac0 if _ac0 in AIR_CHECK_OPTIONS else "(未選択)"
            st.session_state["nr_plate_match"] = None
            st.session_state["nr_initialized"] = True

        # ── 日時ピッカー
        st.markdown("<div class='sec-title'>📅 日時</div>", unsafe_allow_html=True)
        _dt1, _dt2, _dt3, _dt4 = st.columns([2.5, 0.85, 0.85, 1.1])
        with _dt1: _d = st.date_input("日付", key="nr_date")
        _nr_h0 = st.session_state.get("nr_hour", 0)
        _nr_m0 = st.session_state.get("nr_min", 0)
        _nr_hopts = list(range(_nr_h0, 24)) + list(range(0, _nr_h0))
        _nr_mopts = list(range(_nr_m0, 60)) + list(range(0, _nr_m0))
        with _dt2: _h = st.selectbox("時", _nr_hopts, key="nr_hour", format_func=lambda x: f"{x:02d}")
        with _dt3: _m = st.selectbox("分", _nr_mopts, key="nr_min",  format_func=lambda x: f"{x:02d}")
        with _dt4:
            st.markdown("<div style='margin-top:25px'></div>", unsafe_allow_html=True)
            if st.button("📍 今", key="nr_now", use_container_width=True, help="現在時刻をセット"):
                _n = datetime.now()
                st.session_state["nr_date"] = _n.date()
                st.session_state["nr_hour"] = _n.hour
                st.session_state["nr_min"]  = _n.minute
                st.rerun()
        f_date = f"{_d.strftime('%Y/%m/%d')} {_h:02d}:{_m:02d}"

        # ── 来店目的・種別
        c1, c2 = st.columns(2)
        with c1: f_purpose = st.selectbox("🎯 来店目的", PURPOSE_OPTIONS, key="nr_purpose")
        with c2: f_ctype   = st.selectbox("👤 種別", CUST_TYPE_OPTIONS, key="nr_ctype")

        # ── ナンバープレート
        st.markdown("<div class='sec-title'>ナンバープレート</div>", unsafe_allow_html=True)
        p1, p2, p3, p4 = st.columns([2, 1, 1, 1])
        with p1: f_area   = st.selectbox("地名", PLATE_AREAS, key="nr_area")
        with p2: f_3digit = st.text_input("3桁", placeholder="500", max_chars=3, key="nr_3digit")
        with p3: f_kana   = st.selectbox("かな", KANA_OPTIONS, key="nr_kana")
        with p4: f_num    = st.text_input("下4桁", placeholder="1234", max_chars=4, key="nr_num", on_change=_on_nr_num_change)

        # ── 車番重複アラート＋引き継ぎ
        _matches = st.session_state.get("nr_plate_matches", [])
        if _matches:
            if len(_matches) == 1:
                # 1件のみ：従来通りのシンプル表示
                _pm = _matches[0]
                _pm_car  = " ".join(filter(None, [_pm.get("maker",""), _pm.get("car_model","")]))
                _pm_tire = " ".join(filter(None, [_pm.get("tire_maker",""), _pm.get("tire_product","")]))
                _pm_info = " / ".join(filter(None, [_pm.get("date","")[:10], _pm_car, _pm_tire]))
                _wa, _wb = st.columns([3, 1])
                with _wa:
                    st.warning(f"⚠️ 過去に同じ車番の記録があります（最新：{_pm_info}）")
                with _wb:
                    st.button("📋 過去データを引き継ぐ", key="nr_inherit",
                              on_click=_do_nr_inherit, use_container_width=True)
            else:
                # 複数車種：ラジオ選択UI
                st.warning("⚠️ 同じ車番で異なる車両記録が複数あります。引き継ぐ車両を選択してください。")
                _mlabels = _nr_match_labels(_matches)
                st.radio("引き継ぎ対象車両", _mlabels, key="nr_inherit_radio",
                         label_visibility="collapsed")
                st.button("📋 選択した車両のデータを引き継ぐ", key="nr_inherit",
                          on_click=_do_nr_inherit, use_container_width=True)

        # ── 車両情報（車種入力→メーカー・サイズ即時連動）
        st.markdown("<div class='sec-title'>車両情報</div>", unsafe_allow_html=True)
        v1, v2, v3, v4 = st.columns([2, 2, 1, 2])
        with v1: f_maker    = st.selectbox("メーカー", MAKER_OPTIONS, key="nr_maker")
        with v2: f_car      = st.text_input("車種", placeholder="プリウス", key="nr_car", on_change=_on_nr_car_change)
        with v3: f_car_size = st.selectbox("サイズ", SIZE_OPTIONS, key="nr_car_size")
        with v4: f_color    = st.selectbox("カラー", COLOR_OPTIONS, key="nr_color")
        v5, v6 = st.columns([1, 1])
        with v5: f_age    = st.selectbox("年齢", AGE_OPTIONS, key="nr_age")
        with v6: f_gender = st.selectbox("性別", GENDER_OPTIONS, key="nr_gender")

        # ── タイヤ情報（商品名入力→タイヤメーカー即時連動）
        st.markdown("<div class='sec-title'>タイヤ情報</div>", unsafe_allow_html=True)
        t1, t2, t3, t4 = st.columns([2, 1, 2, 2])
        with t1: f_tsize  = st.text_input("タイヤサイズ", placeholder="225/50R17", key="nr_tsize")
        with t2: f_tyear  = st.selectbox("製造年", TIRE_YEAR_OPTIONS, key="nr_tyear")
        with t3: f_tmaker = st.selectbox("タイヤメーカー", TIRE_MAKER_OPTIONS, key="nr_tmaker")
        with t4: f_tprod  = st.text_input("タイヤ商品名", placeholder="ENASAVE EC204", key="nr_tprod", on_change=_on_nr_tprod_change)

        # ── 車検日・天気
        st.markdown("<div class='sec-title'>車検日・天気</div>", unsafe_allow_html=True)
        sx1, sx2 = st.columns([2, 1])
        with sx1:
            _sd_val = st.session_state.get("nr_shaken_date")
            f_shaken_date = st.date_input("🔧 車検日", value=_sd_val, key="nr_shaken_date")
        with sx2:
            f_weather = st.selectbox("🌤 天気", WEATHER_OPTIONS, key="nr_weather")

        # ── 担当者・空気圧点検・備考
        st.markdown("<div class='sec-title'>担当者・空気圧点検・備考</div>", unsafe_allow_html=True)
        sa0, sb0 = st.columns([1, 1])
        with sa0: f_staff     = st.selectbox("担当者", STAFF_OPTIONS, key="nr_staff")
        with sb0: f_air_check = st.selectbox("💨 空気圧点検", AIR_CHECK_OPTIONS, key="nr_air_check")
        f_memo = st.text_area("📝 備考", placeholder="接客メモ・特記事項など", height=80, key="nr_memo")

        # ── 保存・キャンセル
        sa, sb = st.columns(2)
        with sa: ok = st.button("💾 保存する", type="primary", use_container_width=True, key="nr_ok")
        with sb: ng = st.button("キャンセル", use_container_width=True, key="nr_ng")

        if ok:
            append_record({"date":f_date,"purpose":f_purpose,"cust_type":f_ctype if f_ctype != "なし" else "",
                           "plate_area":opt(f_area),"plate_3digit":f_3digit,
                           "plate_kana":opt(f_kana),"plate_num":f_num,
                           "maker":opt(f_maker),"car_model":f_car,"car_size":opt(f_car_size),"color":opt(f_color),
                           "age":opt(f_age),"gender":f_gender,
                           "tire_size":f_tsize,"tire_size_num":tire_to_num(f_tsize),
                           "tire_year":f_tyear,"tire_maker":opt(f_tmaker),
                           "tire_product":f_tprod,"staff":opt(f_staff),"memo":f_memo,
                           "shaken_date":f_shaken_date.strftime("%Y/%m/%d") if f_shaken_date else "",
                           "weather":opt(f_weather),
                           "air_check":opt(f_air_check)})
            learn_car_mapping(f_car, opt(f_maker), opt(f_car_size))
            learn_tire_mapping(f_tprod, opt(f_tmaker))
            # 2c: 同一車番の「予定」ステータスをゴミ箱へ自動アーカイブ
            if f_num:
                _sdf = load_schedule()
                if not _sdf.empty:
                    _mask = (_sdf["plate_num"] == f_num) & (_sdf["status"] == "予定")
                    if _mask.any():
                        _sdf.loc[_mask, "status"] = "ゴミ箱"
                        save_schedule(_sdf)
            st.success("保存しました！")
            st.session_state.nr_initialized = False
            st.session_state.is_duplicate = False
            st.session_state.is_ai_input  = False
            st.session_state.duplicate_data = {}
            st.session_state.mode="list"; st.session_state.searched_plate=""; st.rerun()
        if ng:
            st.session_state.nr_initialized = False
            st.session_state.is_duplicate = False
            st.session_state.is_ai_input  = False
            st.session_state.duplicate_data = {}
            st.session_state.mode="list"; st.rerun()

    # ════════════════════════════════════════════════════════════════════════════
    #  ✏️ 履歴編集（全16項目）
    # ════════════════════════════════════════════════════════════════════════════
    elif mode == "edit_record":
        df  = load_history()
        idx = st.session_state.edit_idx
        if idx is None or idx not in df.index:
            st.session_state.mode = "list"; st.rerun()

        row = df.loc[idx]
        if st.button("← 一覧に戻る（変更を破棄）", key="edit_back", use_container_width=True):
            st.session_state.er_last_idx = None
            st.session_state.mode = "list"; st.rerun()

        st.markdown(f"<div style='font-size:.98rem;font-weight:800;color:#f5f5f5;margin:8px 0 4px'>✏️ 来店記録を編集</div>", unsafe_allow_html=True)

        # ── セッション初期化（レコード切り替え時のみ）────────────────────────────
        if st.session_state.get("er_last_idx") != idx:
            _d0, _h0, _m0 = _parse_dt(row["date"])
            st.session_state["er_date"]    = _d0
            st.session_state["er_hour"]    = _h0
            st.session_state["er_min"]     = _m0
            st.session_state["er_purpose"] = row["purpose"] if row["purpose"] in PURPOSE_OPTIONS else PURPOSE_OPTIONS[0]
            _ctype_e = row["cust_type"] or ""
            st.session_state["er_ctype"]   = _ctype_e if _ctype_e in CUST_TYPE_OPTIONS else "一般"
            st.session_state["er_area"]    = row["plate_area"] if row["plate_area"] in PLATE_AREAS else "(未選択)"
            st.session_state["er_3digit"]  = row["plate_3digit"] or ""
            st.session_state["er_kana"]    = row["plate_kana"] if row["plate_kana"] in KANA_OPTIONS else "(未選択)"
            st.session_state["er_num"]     = row["plate_num"] or ""
            _car_e   = row["car_model"] or ""
            _maker_e = row["maker"] or ""
            _size_e  = row.get("car_size","") or ""
            _inf_maker_e, _inf_size_e = infer_car_info(_car_e)
            st.session_state["er_car"]      = _car_e
            st.session_state["er_maker"]    = (_maker_e if _maker_e in MAKER_OPTIONS else _inf_maker_e or "(未選択)")
            st.session_state["er_car_size"] = (_size_e if _size_e in SIZE_OPTIONS else _inf_size_e or "(未選択)")
            _color_e = row["color"] or "(未選択)"
            st.session_state["er_color"]   = _color_e if _color_e in COLOR_OPTIONS else "(未選択)"
            _age_e   = row["age"] or "(未選択)"
            st.session_state["er_age"]     = _age_e if _age_e in AGE_OPTIONS else "(未選択)"
            _gender_e= row["gender"] or "無記名"
            st.session_state["er_gender"]  = _gender_e if _gender_e in GENDER_OPTIONS else "無記名"
            _tprod_e = row["tire_product"] or ""
            _tmaker_e= row["tire_maker"] or ""
            st.session_state["er_tsize"]   = row["tire_size"] or ""
            st.session_state["er_tyear"]   = norm_tyear(row["tire_year"] or "")
            st.session_state["er_tprod"]   = _tprod_e
            st.session_state["er_tmaker"]  = (_tmaker_e if _tmaker_e in TIRE_MAKER_OPTIONS else infer_tire_maker(_tprod_e) or "(未選択)")
            _staff_e = row.get("staff", "") or ""
            st.session_state["er_staff"]   = _staff_e if _staff_e in STAFF_OPTIONS else "(未選択)"
            st.session_state["er_memo"]    = row["memo"] or ""
            # 車検日・天気
            _sd_e = row.get("shaken_date", "") or ""
            try:
                st.session_state["er_shaken_date"] = pd.to_datetime(_sd_e).date() if _sd_e else None
            except Exception:
                st.session_state["er_shaken_date"] = None
            _wt_e = row.get("weather", "") or ""
            st.session_state["er_weather"] = _wt_e if _wt_e in WEATHER_OPTIONS else "(未選択)"
            _ac_e = row.get("air_check", "") or ""
            st.session_state["er_air_check"] = _ac_e if _ac_e in AIR_CHECK_OPTIONS else "(未選択)"
            st.session_state["er_last_idx"] = idx
            st.rerun()

        # ── 日時ピッカー
        st.markdown("<div class='sec-title'>📅 日時</div>", unsafe_allow_html=True)
        _edt1, _edt2, _edt3, _edt4 = st.columns([2.5, 0.85, 0.85, 1.1])
        with _edt1: _ed = st.date_input("日付", key="er_date")
        _er_h0 = st.session_state.get("er_hour", 0)
        _er_m0 = st.session_state.get("er_min", 0)
        _er_hopts = list(range(_er_h0, 24)) + list(range(0, _er_h0))
        _er_mopts = list(range(_er_m0, 60)) + list(range(0, _er_m0))
        with _edt2: _eh = st.selectbox("時", _er_hopts, key="er_hour", format_func=lambda x: f"{x:02d}")
        with _edt3: _em = st.selectbox("分", _er_mopts, key="er_min",  format_func=lambda x: f"{x:02d}")
        with _edt4:
            st.markdown("<div style='margin-top:25px'></div>", unsafe_allow_html=True)
            if st.button("📍 今", key="er_now", use_container_width=True, help="現在時刻をセット"):
                _n = datetime.now()
                st.session_state["er_date"] = _n.date()
                st.session_state["er_hour"] = _n.hour
                st.session_state["er_min"]  = _n.minute
                st.rerun()
        f_date = f"{_ed.strftime('%Y/%m/%d')} {_eh:02d}:{_em:02d}"

        # ── 来店目的・種別
        c1, c2 = st.columns(2)
        with c1: f_purpose = st.selectbox("🎯 来店目的", PURPOSE_OPTIONS, key="er_purpose")
        with c2: f_ctype   = st.selectbox("👤 種別", CUST_TYPE_OPTIONS, key="er_ctype")

        # ── ナンバープレート
        st.markdown("<div class='sec-title'>ナンバープレート</div>", unsafe_allow_html=True)
        p1, p2, p3, p4 = st.columns([2, 1, 1, 1])
        with p1: f_area   = st.selectbox("地名", PLATE_AREAS, key="er_area")
        with p2: f_3digit = st.text_input("3桁", max_chars=3, key="er_3digit")
        with p3: f_kana   = st.selectbox("かな", KANA_OPTIONS, key="er_kana")
        with p4: f_num    = st.text_input("下4桁", max_chars=4, key="er_num")

        # ── 車両情報（車種→メーカー・サイズ即時連動）
        st.markdown("<div class='sec-title'>車両情報</div>", unsafe_allow_html=True)
        v1, v2, v3, v4 = st.columns([2, 2, 1, 2])
        with v1: f_maker    = st.selectbox("メーカー", MAKER_OPTIONS, key="er_maker")
        with v2: f_car      = st.text_input("車種", key="er_car", on_change=_on_er_car_change)
        with v3: f_car_size = st.selectbox("サイズ", SIZE_OPTIONS, key="er_car_size")
        with v4: f_color    = st.selectbox("カラー", COLOR_OPTIONS, key="er_color")
        v5, v6 = st.columns([1, 1])
        with v5: f_age    = st.selectbox("年齢", AGE_OPTIONS, key="er_age")
        with v6: f_gender = st.selectbox("性別", GENDER_OPTIONS, key="er_gender")

        # ── タイヤ情報（商品名→タイヤメーカー即時連動）
        st.markdown("<div class='sec-title'>タイヤ情報</div>", unsafe_allow_html=True)
        t1, t2, t3, t4 = st.columns([2, 1, 2, 2])
        with t1: f_tsize  = st.text_input("タイヤサイズ", key="er_tsize")
        with t2: f_tyear  = st.selectbox("製造年", TIRE_YEAR_OPTIONS, key="er_tyear")
        with t3: f_tmaker = st.selectbox("タイヤメーカー", TIRE_MAKER_OPTIONS, key="er_tmaker")
        with t4: f_tprod  = st.text_input("タイヤ商品名", key="er_tprod", on_change=_on_er_tprod_change)

        # ── 車検日・天気
        st.markdown("<div class='sec-title'>車検日・天気</div>", unsafe_allow_html=True)
        ex1, ex2 = st.columns([2, 1])
        with ex1:
            _esd_val = st.session_state.get("er_shaken_date")
            f_shaken_date = st.date_input("🔧 車検日", value=_esd_val, key="er_shaken_date")
        with ex2:
            f_weather = st.selectbox("🌤 天気", WEATHER_OPTIONS, key="er_weather")

        # ── 担当者・空気圧点検・備考
        st.markdown("<div class='sec-title'>担当者・空気圧点検・備考</div>", unsafe_allow_html=True)
        ea0, eb0 = st.columns([1, 1])
        with ea0: f_staff     = st.selectbox("担当者", STAFF_OPTIONS, key="er_staff")
        with eb0: f_air_check = st.selectbox("💨 空気圧点検", AIR_CHECK_OPTIONS, key="er_air_check")
        f_memo = st.text_area("📝 備考", height=90, key="er_memo")

        # ── 上書き保存・キャンセル
        sa, sb = st.columns(2)
        with sa: ok = st.button("💾 上書き保存", type="primary", use_container_width=True, key="er_ok")
        with sb: ng = st.button("キャンセル", use_container_width=True, key="er_ng")

        if ok:
            df.loc[idx, "date"]         = f_date
            df.loc[idx, "purpose"]      = f_purpose
            df.loc[idx, "cust_type"]    = f_ctype if f_ctype != "なし" else ""
            df.loc[idx, "plate_area"]   = opt(f_area)
            df.loc[idx, "plate_3digit"] = f_3digit
            df.loc[idx, "plate_kana"]   = opt(f_kana)
            df.loc[idx, "plate_num"]    = f_num
            df.loc[idx, "maker"]        = opt(f_maker)
            df.loc[idx, "car_model"]    = f_car
            df.loc[idx, "car_size"]     = opt(f_car_size)
            df.loc[idx, "color"]        = opt(f_color)
            df.loc[idx, "age"]          = opt(f_age)
            df.loc[idx, "gender"]       = f_gender
            df.loc[idx, "tire_size"]    = f_tsize
            df.loc[idx, "tire_size_num"]= tire_to_num(f_tsize)
            df.loc[idx, "tire_year"]    = f_tyear
            df.loc[idx, "tire_maker"]   = opt(f_tmaker)
            df.loc[idx, "tire_product"] = f_tprod
            df.loc[idx, "staff"]        = opt(f_staff)
            df.loc[idx, "memo"]         = f_memo
            df.loc[idx, "shaken_date"]  = f_shaken_date.strftime("%Y/%m/%d") if f_shaken_date else ""
            df.loc[idx, "weather"]      = opt(f_weather)
            df.loc[idx, "air_check"]    = opt(f_air_check)
            save_history(df)
            learn_car_mapping(f_car, opt(f_maker), opt(f_car_size))
            learn_tire_mapping(f_tprod, opt(f_tmaker))
            st.success("更新しました！")
            st.session_state.er_last_idx = None
            st.session_state.mode="list"; st.rerun()
        if ng:
            st.session_state.er_last_idx = None
            st.session_state.mode="list"; st.rerun()

    # ════════════════════════════════════════════════════════════════════════════
    #  📋 一覧（全件 or 絞り込み）
    # ════════════════════════════════════════════════════════════════════════════
    elif mode == "list":
        df = load_history()
        if pq:
            filtered = df[df["plate_num"] == pq].copy()
            header   = f"🔎 車番「{pq}」の記録"
        else:
            filtered = df.copy()
            header   = "📋 全来店記録（最新順）"

        filtered["_dt"] = pd.to_datetime(filtered["date"], errors="coerce")
        filtered = filtered.sort_values("_dt", ascending=False)   # index保持（reset_indexしない）

        st.markdown(f"<div style='font-size:.98rem;font-weight:700;color:#f0f0f0;margin-bottom:4px'>{header} <span style='font-size:.78rem;color:#aaa;font-weight:400'>({len(filtered)}件)</span></div>", unsafe_allow_html=True)
        if st.button("➕ 新規記録", use_container_width=True, key="new2"):
            st.session_state.nr_initialized = False
            st.session_state.mode="new_record"; st.rerun()
        if st.button("🛞 見積作成", use_container_width=True, key="quote2"):
            st.session_state.mode="quote"; st.rerun()

        # 削除完了メッセージ
        if st.session_state.get("deleted_message"):
            st.success(st.session_state.deleted_message)
            st.session_state.deleted_message = ""

        # 削除確認パネル
        del_idx = st.session_state.get("confirm_delete_idx")
        if del_idx is not None and del_idx in df.index:
            crow    = df.loc[del_idx]
            c_plate = " ".join(filter(None,[crow["plate_area"],crow["plate_3digit"],crow["plate_kana"],crow["plate_num"]]))
            c_car   = " ".join(filter(None,[crow["maker"],crow["car_model"]]))
            c_memo  = f'<div style="color:#888;margin-top:4px;font-size:.76rem">{crow["memo"][:60]}</div>' if crow["memo"] else ""
            st.markdown(
                f"<div style='background:#2d0d0d;border:2px solid #ef4444;border-radius:12px;padding:14px 16px;margin:8px 0'>"
                f"<div style='font-size:.9rem;font-weight:800;color:#f87171;margin-bottom:6px'>🗑️ 削除の確認</div>"
                f"<div style='font-size:.82rem;color:#ccc;margin-bottom:8px'>以下のデータを削除します。この操作は<b>取り消せません</b>。</div>"
                f"<div style='background:#1e0808;border-radius:8px;padding:8px 12px;font-size:.82rem;border:1px solid #7f1d1d'>"
                f"<b>{crow['date']}</b>&nbsp;/&nbsp;{crow['purpose']}&nbsp;/&nbsp;{c_plate or '（車番なし）'}&nbsp;/&nbsp;{c_car or '（車種なし）'}"
                f"{c_memo}</div></div>",
                unsafe_allow_html=True,
            )
            dc1, dc2, _ = st.columns([1, 1, 4])
            with dc1:
                if st.button("🗑️ はい、削除する", use_container_width=True, key="confirm_delete_btn", type="primary"):
                    new_df = df.drop(index=del_idx)
                    save_history(new_df)
                    label = c_plate or crow["purpose"] or "記録"
                    st.session_state.confirm_delete_idx = None
                    st.session_state.deleted_message = f"「{label}」の記録を削除しました"
                    st.rerun()
            with dc2:
                if st.button("キャンセル", use_container_width=True, key="cancel_delete_btn"):
                    st.session_state.confirm_delete_idx = None
                    st.rerun()

        if filtered.empty:
            st.markdown("<div style='padding:36px;text-align:center;color:#ccc;border:1px dashed #e0e0e0;border-radius:14px;margin-top:10px'>記録が見つかりません</div>", unsafe_allow_html=True)
        else:
            # ── スペースキーショートカット（選択行を複製・再描画後も継続動作） ──
            components.html("""<script>
            (function(){
              var doc=window.parent.document;

              /* 再描画のたびに古いハンドラを除去して新規登録（重複防止＋確実再登録） */
              if(window.parent._kbDupHandler){
                doc.removeEventListener('keydown',window.parent._kbDupHandler,true);
              }

              window.parent._kbDupHandler=function(e){
                if(e.code!=='Space'&&e.key!==' ') return;
                /* テキスト入力系にフォーカスがある場合はスペース入力を優先 */
                var ae=doc.activeElement||{};
                var tag=(ae.tagName||'').toUpperCase();
                if(tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT'||ae.isContentEditable) return;
                e.preventDefault();
                /* アクションパネルの「📋 複製」ボタンをクリック */
                var btns=doc.querySelectorAll('[data-testid="stButton"] button');
                for(var i=0;i<btns.length;i++){
                  var t=btns[i].innerText||btns[i].textContent||'';
                  if(t.indexOf('📋')>=0&&t.indexOf('複製')>=0){
                    btns[i].click(); return;
                  }
                }
              };
              doc.addEventListener('keydown',window.parent._kbDupHandler,true);

              /* 再描画後にフォーカスを強制復帰（スペースキーを確実に受け取るため） */
              function refocus(){
                var ae=doc.activeElement;
                if(ae&&ae!==doc.body&&ae.tagName!=='BODY') return; /* 既に何かにフォーカス中なら不要 */
                var target=doc.querySelector('[data-testid="stMainBlockContainer"]')
                          ||doc.querySelector('[data-testid="stAppViewContainer"]')
                          ||doc.body;
                if(!target) return;
                if(!target.getAttribute('tabindex')) target.setAttribute('tabindex','-1');
                target.focus({preventScroll:true});
              }
              /* 50ms / 200ms / 600ms の3段階でカバー（Streamlit非同期描画タイミングのブレに対応） */
              [50,200,600].forEach(function(d){ setTimeout(refocus,d); });
            })();
            </script>""", height=0, scrolling=False)

            # ── st.dataframe 高密度表示 ──────────────────────────────────────
            _DISP_COLS = [
                "date","purpose","cust_type",
                "plate_num",
                "maker","car_model","car_size","color","age","gender",
                "tire_size","tire_year","tire_maker","tire_product",
                "staff","memo","shaken_date","weather","air_check",
            ]
            _COL_LABELS = {
                "date":"日時","purpose":"目的","cust_type":"種別",
                "plate_num":"ナンバー",
                "maker":"メーカー","car_model":"車種","car_size":"サイズ","color":"カラー",
                "age":"年齢","gender":"性別",
                "tire_size":"タイヤサイズ","tire_year":"製造年",
                "tire_maker":"タイヤメーカー","tire_product":"商品名",
                "staff":"担当者","memo":"備考",
                "shaken_date":"車検日","weather":"天気","air_check":"空気圧点検",
            }
            display_df = filtered[_DISP_COLS].copy().rename(columns=_COL_LABELS).reset_index(drop=True)
            # 日時カラムに曜日を追加（例: 2025/10/27 (月) 16:58）。CSV保存値は変更しない。
            def _add_dow(s: str) -> str:
                try:
                    dt = pd.to_datetime(s, errors="raise")
                    dow = DAYS_JP[dt.weekday()]
                    date_part = dt.strftime("%Y/%m/%d")
                    time_part = dt.strftime("%H:%M")
                    return f"{date_part} ({dow}) {time_part}"
                except Exception:
                    return s
            display_df["日時"] = display_df["日時"].apply(_add_dow)
            event = st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=430,
                column_config={
                    "日時":          st.column_config.TextColumn("日時",          width="medium"),
                    "目的":          st.column_config.TextColumn("目的",          width="small"),
                    "種別":          st.column_config.TextColumn("種別",          width="small"),
                    "ナンバー":      st.column_config.TextColumn("ナンバー",      width="small"),
                    "メーカー":      st.column_config.TextColumn("メーカー",      width="small"),
                    "車種":          st.column_config.TextColumn("車種",          width="medium"),
                    "サイズ":        st.column_config.TextColumn("サイズ",        width="small"),
                    "カラー":        st.column_config.TextColumn("カラー",        width="small"),
                    "年齢":          st.column_config.TextColumn("年齢",          width="small"),
                    "性別":          st.column_config.TextColumn("性別",          width="small"),
                    "タイヤサイズ":  st.column_config.TextColumn("タイヤサイズ",  width="small"),
                    "製造年":        st.column_config.TextColumn("製造年",        width="small"),
                    "タイヤメーカー":st.column_config.TextColumn("タイヤメーカー",width="medium"),
                    "商品名":        st.column_config.TextColumn("商品名",        width="medium"),
                    "担当者":        st.column_config.TextColumn("担当者",        width="small"),
                    "備考":          st.column_config.TextColumn("備考",          width="large"),
                    "車検日":        st.column_config.TextColumn("車検日",        width="small"),
                    "天気":          st.column_config.TextColumn("天気",          width="small"),
                    "空気圧点検":    st.column_config.TextColumn("空気圧点検",    width="small"),
                },
            )

            # ── 選択行のアクションパネル（Cmd+D はこのパネルの複製ボタンを叩く） ──
            sel_rows = event.selection.rows if event and event.selection else []
            if sel_rows:
                sel_pos      = sel_rows[0]
                sel_orig_idx = filtered.index[sel_pos]
                sel_row      = filtered.loc[sel_orig_idx]
                _plate_s = " ".join(filter(None,[sel_row["plate_area"],sel_row["plate_3digit"],sel_row["plate_kana"],sel_row["plate_num"]]))
                _car_s   = " ".join(filter(None,[sel_row["maker"],sel_row["car_model"]]))
                st.markdown(f"""
                <div style="background:#0f1f3d;border:1.5px solid #2563eb;border-radius:10px;
                            padding:8px 14px;margin:5px 0;display:flex;align-items:center;gap:10px">
                  <span style="font-size:.82rem;font-weight:700;color:#93c5fd;flex:1">
                    ▶ {sel_row['date']} &nbsp;/&nbsp; {sel_row['purpose']} &nbsp;/&nbsp;
                    {_plate_s or '（車番なし）'} &nbsp;{_car_s}
                  </span>
                  <span style="font-size:.7rem;color:#93c5fd">⌘D=複製</span>
                </div>""", unsafe_allow_html=True)
                if st.button("🔍 詳細", key="list_det", use_container_width=True):
                    st.session_state.mode="view_record"
                    st.session_state.view_idx=int(sel_orig_idx); st.rerun()
                if st.button("✏️ 編集", key="list_edt", use_container_width=True):
                    st.session_state.mode="edit_record"
                    st.session_state.edit_idx=int(sel_orig_idx); st.rerun()
                if st.button("📋 複製", key="list_dup", use_container_width=True):
                    # 日付含む全項目をそのまま保持
                    _d0, _h0, _m0 = _parse_dt(sel_row.get("date", ""))
                    st.session_state["nr_date"]     = _d0
                    st.session_state["nr_hour"]     = _h0
                    st.session_state["nr_min"]      = _m0
                    st.session_state.nr_initialized = True
                    st.session_state.is_duplicate   = True
                    st.session_state.is_ai_input    = False
                    st.session_state.duplicate_data = sel_row.to_dict()
                    st.session_state.mode           = "new_record"
                    st.session_state.view_idx       = None
                    st.rerun()
                if st.button("🗑️ 削除", key="list_del", use_container_width=True):
                    st.session_state.confirm_delete_idx = int(sel_orig_idx)
                    st.rerun()
            else:
                st.markdown("<div style='font-size:.76rem;color:#bbb;text-align:center;padding:5px 0'>"
                            "行をクリックして選択 → 詳細・編集・📋複製・削除 | 選択後 ⌘D で即複製</div>",
                            unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════════
    #  🔍 詳細表示
    # ════════════════════════════════════════════════════════════════════════════
    elif mode == "view_record":
        df  = load_history()
        idx = st.session_state.view_idx
        if idx is None or idx not in df.index:
            st.session_state.mode="list"; st.rerun()
        row = df.loc[idx]

        if st.button("← 一覧に戻る", key="back", use_container_width=True):
            st.session_state.mode="list"; st.rerun()
        if st.button("✏️ この記録を編集", use_container_width=True, key="to_edit"):
            st.session_state.mode="edit_record"; st.session_state.edit_idx=idx; st.rerun()

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        plate_str = " ".join(filter(None,[row["plate_area"],row["plate_3digit"],row["plate_kana"],row["plate_num"]]))
        car_str   = " ".join(filter(None,[row["maker"],row["car_model"]]))

        def badge(text:str,cls:str)->str: return f'<span class="badge {cls}">{text}</span>' if text else ""

        ctype_b  = badge(row["cust_type"], f"bt-{row['cust_type']}")
        gender_b = badge(row["gender"],    f"bg-{row['gender']}")
        purp_b   = badge(row["purpose"],   "bp")
        tire_full = " ".join(filter(None,[row["tire_size"],row["tire_maker"],row["tire_product"]]))
        tyear_s   = f"{row['tire_year']}年製" if row["tire_year"] else ""
        age_s     = row["age"] if row["age"] not in ("","(未選択)") else ""
        memo_html = f'<div class="memo-box">📝 {row["memo"]}</div>' if row["memo"] else ""

        staff_s  = row.get("staff","") or ""
        car_size_s = row.get("car_size","") or ""
        st.markdown(f"""
        <div class="detail-card">
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                <span style="font-size:1.3rem;font-weight:800;color:#f5f5f5">{plate_str}</span>
                {ctype_b} {purp_b}
            </div>
            <div class="detail-grid">
                <div><span class="detail-label">日時</span><span class="detail-val">{row['date']}</span></div>
                <div><span class="detail-label">車両</span><span class="detail-val">{car_str}</span></div>
                {f'<div><span class="detail-label">サイズ</span><span class="detail-val">{car_size_s}</span></div>' if car_size_s else ''}
                <div><span class="detail-label">カラー</span><span class="detail-val">{row['color']}</span></div>
                <div><span class="detail-label">客層</span><span class="detail-val">{gender_b} {age_s}</span></div>
                <div><span class="detail-label">タイヤ</span><span class="detail-val">{tire_full}</span></div>
                <div><span class="detail-label">製造年</span><span class="detail-val">{tyear_s}</span></div>
                {f'<div><span class="detail-label">担当者</span><span class="detail-val">{staff_s}</span></div>' if staff_s else ''}
            </div>{memo_html}</div>""", unsafe_allow_html=True)

        same = df[(df["plate_num"] == row["plate_num"]) & (df.index != idx)]
        if not same.empty:
            st.markdown(f"<div class='sec-title'>同一車番の過去記録（{len(same)}件）</div>", unsafe_allow_html=True)
            for _, pr in same.sort_values(by=df.columns[0], ascending=False).iterrows():
                pr_purp = badge(pr["purpose"],"bp")
                pr_car  = " ".join(filter(None,[pr["maker"],pr["car_model"]]))
                st.markdown(f"""
                <div style="padding:10px 14px;border:1px solid #ebebeb;border-left:4px solid #a5b4fc;border-radius:0 12px 12px 0;margin-bottom:7px;background:#fff">
                    <div style="font-size:.74rem;color:#aaa;margin-bottom:3px">{pr['date']}</div>
                    <div style="font-size:.86rem;font-weight:600">{pr_purp} &nbsp;{pr_car}</div>
                    <div style="font-size:.78rem;color:#888;margin-top:2px">{pr['memo']}</div>
                </div>""", unsafe_allow_html=True)
