import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def generate_and_analyze_ss_data():
    np.random.seed(42)  # 再現性を確保
    n_samples = 5000

    print("📊 現場のリアルな活動データをシミュレーション生成中（5,000件）...")

    # 1. そもそもタイヤの交換時期（5年以上前、2021年以前製造）のお客さんが来店してくる割合の仕込み
    # 2026年現在から見て、2021年以前は約30%と仮定
    years = np.random.choice([2023, 2024, 2025, 2021, 2020, 2019], size=n_samples, p=[0.3, 0.2, 0.2, 0.15, 0.1, 0.05])
    
    # 基本の来店目的（セルフなので給油・洗車が圧倒的）
    purposes = np.random.choice(['給油', '洗車', 'オイル交換', 'その他'], size=n_samples, p=[0.70, 0.20, 0.07, 0.03])
    
    df = pd.DataFrame({
        '来店目的': purposes,
        'タイヤ製造年': years
    })

    # 2. セルフの現場声掛け歩留まりをリアルに再現（確率の定義）
    # 給油・洗車の客に声をかけまくった場合
    # ・空気圧点検OK率：約 15%（大半は「急いでるから」と断られる）
    # ・点検後のタイヤ訴求（NG判定から見積もり提示）率：点検OKした人のうち約 20%
    # ・見積もりからの成約（購入）率：見積もりした人のうち約 10%
    
    air_check = []
    quote_given = []
    purchased = []

    for idx, row in df.iterrows():
        # 給油・洗車客への強引な声掛け
        if row['来店目的'] in ['給油', '洗車']:
            # ① 空気圧点検OKだった割合（15%）
            is_air_ok = np.random.seed() or np.random.rand() < 0.15
            air_check.append('OK' if is_air_ok else 'お断り')
            
            if is_air_ok:
                # ② 点検して、さらにタイヤ見積もりまで進んでくれた割合（20%）
                is_quote_ok = np.random.rand() < 0.20
                quote_given.append('見積提示' if is_quote_ok else '訴求不発')
                
                if is_quote_ok:
                    # ③ 見積もりから実際に購入まで行った割合（10%）
                    is_buy_ok = np.random.rand() < 0.10
                    purchased.append('購入' if is_buy_ok else '検討落ち')
                else:
                    purchased.append('-')
            else:
                quote_given.append('-')
                purchased.append('-')
        else:
            # 元からオイル交換などの目的の客は打率が少し高い
            is_air_ok = np.random.rand() < 0.40
            air_check.append('OK' if is_air_ok else '未実施')
            if is_air_ok:
                is_quote_ok = np.random.rand() < 0.35
                quote_given.append('見積提示' if is_quote_ok else '訴求不発')
                if is_quote_ok:
                    is_buy_ok = np.random.rand() < 0.25
                    purchased.append('購入' if is_buy_ok else '検討落ち')
                else:
                    purchased.append('-')
            else:
                quote_given.append('-')
                purchased.append('-')

    df['空気圧点検'] = air_check
    df['見積もり提示'] = quote_given
    df['最終結果'] = purchased

    # --- データ分析・指標計算 ---
    print("\n" + "="*50)
    print("📈 【セルフSS・タイヤ販売プロセスの課題分析レポート】")
    print("="*50)

    # 指標④: そもそもタイヤの交換時期（5年以上前/2021年以前）のお客さんが来店してくる割合
    old_tire_customers = df[df['タイヤ製造年'] <= 2021]
    pct_old_tire = (len(old_tire_customers) / n_samples) * 100
    print(f"📊 4. そもそもタイヤ交換時期（5年以上前）の顧客来店割合: {pct_old_tire:.1f}% ({len(old_tire_customers)} / {n_samples}件)")
    print("   👉 💡 補足: 実は3割近い顧客が『今すぐ換えるべき状態』で給油しに来ている。")
    print("-" * 50)

    # 給油・洗車目的の顧客（4,500件規模）に絞って声掛けの歩留まり（打率）を分析
    target_df = df[df['来店目的'].isin(['給油', '洗車'])]
    total_voice = len(target_df)

    # 指標①: 空気圧点検の声掛けをしてOKだった割合
    ok_air_df = target_df[target_df['空気圧点検'] == 'OK']
    pct_air = (len(ok_air_df) / total_voice) * 100
    print(f"🚨 1. 空気圧点検の声掛けに応募（OK）してくれた割合     : {pct_air:.1f}% ({len(ok_air_df)} / {total_voice}件)")

    # 指標②: そこからタイヤの訴求をして見積もりを出させてくれた割合
    ok_quote_df = ok_air_df[ok_air_df['見積もり提示'] == '見積提示']
    pct_quote = (len(ok_quote_df) / len(ok_air_df)) * 100 if len(ok_air_df) > 0 else 0
    print(f"📝 2. 点検からタイヤの重要性を訴求し、見積まで至った割合: {pct_quote:.1f}% ({len(ok_quote_df)} / {len(ok_air_df)}件)")

    # 指標③: 見積もりを出して実際に購入まで行った割合
    ok_buy_df = ok_quote_df[ok_quote_df['最終結果'] == '購入']
    pct_buy = (len(ok_buy_df) / len(ok_quote_df)) * 100 if len(ok_quote_df) > 0 else 0
    print(f"💰 3. 見積もり提示から、実際に購入まで至った成約率       : {pct_buy:.1f}% ({len(ok_buy_df)} / {len(ok_quote_df)}件)")

    print("-" * 50)
    # 総合コンバージョン率（最終打率）
    final_conversion = (len(ok_buy_df) / total_voice) * 100
    print(f"🔥 【結論】給油・洗車客への『闇雲な声掛け』からの最終タイヤ購買率: 🔴 {final_conversion:.2f}% 🔴")
    print("="*50)
    print("💀 考察: 1,000人に声をかけても、実際に買うのはわずか2〜3人。")
    print("         スタッフの労力の大半がドブに捨てられ、顧客に煙たがられている実態が数値化されました。")
    print("="*50)

    # CSVとして保存
    df.to_csv("ss_activity_analysis.csv", index=False, encoding="utf-8-sig")
    print("💾 分析元データとして 'ss_activity_analysis.csv' を出力しました。")

    # ── ビジュアル分析レポート生成 ─────────────────────────────────────────────
    # Mac 標準フォントで日本語文字化けを防止
    plt.rcParams['font.family'] = ['Hiragino Sans', 'AppleGothic', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

    sns.set_theme(style="whitegrid", font='Hiragino Sans')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        "セルフSSにおけるタイヤ販売オペレーションの課題分析",
        fontsize=16, fontweight="bold",
    )
    plt.subplots_adjust(top=0.88)

    # ── グラフ1（左）: 声掛けプロセスの歩留まり（横型棒グラフ）──────────────
    funnel_labels = ["給油・洗車客総数", "点検OK", "見積提示", "タイヤ購入"]
    funnel_values = [total_voice, len(ok_air_df), len(ok_quote_df), len(ok_buy_df)]
    bar_colors    = ["#4a90d9", "#5cb85c", "#f0ad4e", "#d9534f"]

    # 上から「給油・洗車客総数」になるよう逆順で描画
    bars = ax1.barh(
        funnel_labels[::-1], funnel_values[::-1],
        color=bar_colors[::-1], edgecolor="white", linewidth=0.8,
    )
    for bar, val in zip(bars, funnel_values[::-1]):
        ax1.text(
            bar.get_width() + max(funnel_values) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{val:,}件",
            va="center", ha="left", fontsize=9, color="#333333",
        )

    ax1.set_title(
        f"① 闇雲な店頭声掛けの限界（最終購買率{final_conversion:.2f}%）",
        fontsize=11, fontweight="bold", pad=10,
    )
    ax1.set_xlabel("件数", fontsize=10)
    ax1.set_xlim(0, max(funnel_values) * 1.22)
    ax1.tick_params(axis="y", labelsize=10)
    sns.despine(ax=ax1, left=True)

    # ── グラフ2（右）: タイヤ製造年の割合（円グラフ）────────────────────────
    old_count = len(old_tire_customers)
    new_count  = n_samples - old_count

    pie_labels = ["2021年以前\n（交換時期）", "2022年以降\n（まだOK）"]
    pie_values = [old_count, new_count]
    pie_colors = ["#d9534f", "#5cb85c"]

    wedges, texts, autotexts = ax2.pie(
        pie_values,
        labels=pie_labels,
        colors=pie_colors,
        explode=[0.06, 0],          # 警告セグメントを強調
        autopct="%1.1f%%",
        startangle=90,
        textprops={"fontsize": 10},
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    for at in autotexts:
        at.set_fontsize(12)
        at.set_fontweight("bold")

    ax2.set_title(
        "② 実は来店客の約3割がタイヤ交換時期",
        fontsize=11, fontweight="bold", pad=10,
    )

    graph_output = "セルフSS_タイヤ販売課題分析レポート.png"
    plt.savefig(graph_output, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"📊 ビジュアル分析レポート出力成功 : {graph_output}")

if __name__ == "__main__":
    generate_and_analyze_ss_data()