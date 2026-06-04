import os
import pandas as pd
from datetime import datetime, timedelta

def extract_upcoming_inspections(file_path="gs_historical_data.csv"):
    if not os.path.exists(file_path):
        print(f"❌ エラー：{file_path} が見つかりません。先にダミーデータを生成してください。")
        return

    print("📖 大量顧客データを読み込み中...")
    df = pd.read_csv(file_path)

    # 1. 現在の日時を設定（システム日付: 2026年6月2日を基準とする）
    # ※ 面接でのデモ用に、スクリプト実行時の現実の日付ではなく、データ基準日に固定します
    current_date = datetime(2026, 6, 2)
    
    # 3ヶ月後の日付（2026年9月2日）を計算
    three_months_later = current_date + timedelta(days=90)
    
    print(f"⏰ 基準日: {current_date.strftime('%Y/%m/%d')}")
    print(f"🔍 抽出条件: 車検日が {current_date.strftime('%Y/%m/%d')} ～ {three_months_later.strftime('%Y/%m/%d')} のお客様")

    # 2. 車検日列を日付型に変換してフィルタリング
    df['車検日_dt'] = pd.to_datetime(df['車検日'], format='%Y/%m/%d', errors='coerce')
    
    # 条件A: 車検日が今日から3ヶ月以内
    # 条件B: ダミーデータの識別サインである「ナンバー地名が 横浜」
    condition = (df['車検日_dt'] >= current_date) & (df['車検日_dt'] <= three_months_later) & (df['ナンバー地名'] == "横浜")
    
    targets = df[condition].copy()

    # 3. 【現場の実務ロジック】すでに直近の来店目的が「車検見積」のお客様は、アプローチ済みのため除外
    before_count = len(targets)
    targets = targets[targets['来店目的'] != '車検見積']
    after_count = len(targets)
    excluded_count = before_count - after_count

    # 4. 見やすさのためにソート（車検日が近い順）
    targets = targets.sort_values(by='車検日_dt', ascending=True)

    # 不要になった計算用列を削除
    targets = targets.drop(columns=['車検日_dt'])

    # 5. アプローチ用のCSVとして出力
    output_file = "車検獲得アプローチリスト.csv"
    targets.to_csv(output_file, index=False, encoding="utf-8-sig")

    print("\n" + "="*40)
    print("✨ 【データ抽出・自動化完了】")
    print(f"📊 横浜ナンバーの車検接近者 : {before_count} 件")
    print(f"⚠️ 既に見積済みの除外対象   : {excluded_count} 件")
    print(f"📋 最終アプローチ即応リスト : {after_count} 件")
    print(f"💾 ファイル出力成功         : {output_file}")
    print("="*40)

    # 6. 担当者別集計
    staff_col = "担当者"
    if staff_col in targets.columns:
        staff_counts = (
            targets[staff_col]
            .fillna("（未設定）")
            .replace("", "（未設定）")
            .value_counts()
            .reset_index()
        )
        staff_counts.columns = ["担当者", "割当件数"]
        staff_counts = staff_counts.sort_values("割当件数", ascending=False).reset_index(drop=True)

        # ① コンソール出力
        print("\n" + "-"*34)
        print("👤 【担当者別・アプローチ対象件数】")
        max_len = staff_counts["担当者"].str.len().max() if not staff_counts.empty else 4
        for _, row in staff_counts.iterrows():
            name = row["担当者"]
            cnt  = row["割当件数"]
            # 全角スペースで右側を揃える
            padding = "　" * (max_len - len(name))
            print(f"  ・{name}{padding}: {cnt:>3} 件")
        print("-"*34)

        # ② CSVファイル出力
        staff_output = "担当者別_車検アプローチ件数.csv"
        staff_counts.to_csv(staff_output, index=False, encoding="utf-8-sig")
        print(f"💾 担当者別集計CSV出力成功  : {staff_output}")
    else:
        print(f"\n⚠️ 列「{staff_col}」が見つからないため担当者別集計をスキップしました。")

if __name__ == "__main__":
    extract_upcoming_inspections()