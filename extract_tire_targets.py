import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def extract_winter_tire_targets(file_path="gs_historical_data.csv"):
    if not os.path.exists(file_path):
        print(f"❌ エラー：{file_path} が見つかりません。先にダミーデータを生成してください。")
        return

    print("📖 大量顧客データを読み込み中...")
    df = pd.read_csv(file_path)

    # ターゲットに絞る主要なタイヤサイズ（VOXY、プリウス、セレナ等に多い売れ筋サイズ）
    target_size = "195/65R15"
    
    # 2026年の冬商戦を想定：2022年以前（2022, 2021, 2020...）に製造されたタイヤは4年目以降で交換推奨時期
    border_year = 2022

    print(f"🔍 抽出条件①: タイヤサイズが 「{target_size}」")
    print(f"🔍 抽出条件②: 製造年が 「{border_year}年 以前」（ゴム硬化による交換推奨対象）")
    print(f"🔍 抽出条件③: テストデータ識別サイン 「ナンバー地名が 横浜」")

    # データ型を数値に変換（エラーは欠損値にする）
    df['製造年_num'] = pd.to_numeric(df['製造年'], errors='coerce')

    # 条件の組み合わせ
    condition = (
        (df['タイヤサイズ'] == target_size) & 
        (df['製造年_num'] <= border_year) & 
        (df['ナンバー地名'] == "横浜")
    )

    targets = df[condition].copy()

    # 製造年が古い順（＝より危険度・購入意欲が高い順）にソート
    targets = targets.sort_values(by='製造年_num', ascending=True)

    # 計算用の列を削除
    targets = targets.drop(columns=['製造年_num'])

    # 1. DM発送用アプローチリストのCSV出力
    output_file_list = "スタッドレスDM発送対象リスト.csv"
    targets.to_csv(output_file_list, index=False, encoding="utf-8-sig")

    # 2. 【現場実務ロジック】マーケティング分析用に「現在履いているタイヤメーカー別」の件数を自動集計
    # （どのメーカーからの履き替え需要が多いかを把握するため）
    manufacturer_counts = targets['タイヤメーカー'].value_counts()

    # 集計結果をCSV出力
    output_file_summary = "スタッドレスターゲット_メーカー別集計.csv"
    manufacturer_counts.to_frame(name='ターゲット件数').to_csv(output_file_summary, encoding="utf-8-sig")

    print("\n" + "="*40)
    print("✨ 【スタッドレスDMターゲット抽出完了】")
    print(f"📊 DM発送対象（195/65R15 × 寿命） : {len(targets)} 件")
    print(f"💾 リスト出力成功                   : {output_file_list}")
    print(f"💾 マーケティング集計出力成功       : {output_file_summary}")
    print("\n👤 【現在のタイヤメーカー別内訳（リプレイス元需要）】")
    for m, count in manufacturer_counts.items():
        print(f"・{m.ljust(8)} : {count} 件")
    print("="*40)

    # 3. タイヤメーカー別ターゲット件数グラフの自動生成
    # Mac 標準フォントで日本語文字化けを防止
    plt.rcParams['font.family'] = ['Hiragino Sans', 'AppleGothic', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け対策

    sns.set_theme(style="whitegrid", font='Hiragino Sans')

    plot_data = manufacturer_counts.reset_index()
    plot_data.columns = ["タイヤメーカー", "ターゲット件数"]
    plot_data = plot_data.sort_values("ターゲット件数", ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=plot_data,
        x="タイヤメーカー",
        y="ターゲット件数",
        palette="viridis",
        ax=ax,
    )

    ax.set_title("【195/65R15】現在のタイヤメーカー別ターゲット件数", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("タイヤメーカー", fontsize=11)
    ax.set_ylabel("ターゲット件数", fontsize=11)
    ax.tick_params(axis="x", labelrotation=30)

    # 各バーの上に件数ラベルを表示
    for bar in ax.patches:
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.3,
                f"{int(height)}件",
                ha="center", va="bottom", fontsize=9, color="#333333",
            )

    plt.tight_layout()
    graph_output = "スタッドレスターゲット_メーカー別内訳.png"
    plt.savefig(graph_output, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"📊 グラフ画像出力成功            : {graph_output}")

if __name__ == "__main__":
    extract_winter_tire_targets()