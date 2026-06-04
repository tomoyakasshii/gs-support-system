🚗 タイヤ商談・見積管理 DX システム（GS 店舗向けプロトタイプ）

本システムは、ガソリンスタンド（GS）の現場におけるタイヤ商談の効率化、見積作成時間の短縮、および顧客管理（CRM）の高度化を一気通貫で実現するために開発した店舗 DX プロトタイプです。

前職（ガソリンスタンドでの販売活動）でのリアルな現場課題をもとに、UI/UX の細部までこだわり抜いて設計・開発しました。

ーーー

🛠️ 開発背景と解決する課題

1.  見積作成のタイムロス： 従来の紙の見積書や手計算では、お客様を待たせる時間が長くなり、機会損失が発生していた。

2.  スタッフ間の提案レベルのバラつき： タイヤの知識量によって、2 軸のプラン比較（例：プレミアムタイヤ vs エコノミータイヤ）の提案がスムーズにできない課題。

3.  顧客情報の分散： 過去の来店記録や商談履歴が即座に検索できず、リピート商談への繋ぎ込みが弱かった。

➡️ 本システムを導入することで、スマホ・PC から直感的に「2 軸プランの爆速同時見積」が可能になり、商談時間を大幅に短縮します。

ーーー

📱 主要機能と画面イメージ

1.  【現場最優先】テンキー風車両ナンバー入力（スマートフォン画面）

    ・解決する課題： PC を開けない店頭でも、片手のスマホ操作で車番 4 桁を入力し、瞬時に顧客情報を呼び出せます。

    <img width="1170" height="2329" alt="ss1" src="https://github.com/user-attachments/assets/ce150023-698e-4782-bfdb-494f6e8cf1cb" />

2.  【高度なデータ設計】新規来店記録・車両情報入力画面（PC 画面）

    ・解決する課題： 日本のナンバープレートの規格（地名/分類番号/かな/一連指定番号）に完全準拠。タイヤサイズや製造年、メーカー名までを一元管理し、店頭での的確な顧客提案の土台を作ります。

    <img width="1673" height="897" alt="ss2" src="https://github.com/user-attachments/assets/f0e56422-015c-481c-adc8-5cb0c883c018" />

3.  【一元管理】全来店記録ダッシュボード（PC 画面）

    ・解決する課題： 登録されたデータを基に、店舗全体の過去の商談履歴やタイヤ交換進捗を一覧で把握。アナログ管理による引き継ぎ漏れを防ぎます。

    <img width="1710" height="848" alt="ss3" src="https://github.com/user-attachments/assets/46d33c71-101d-48d1-8731-67569a7c585f" />

4.  【機会損失防止】タイヤ御見積書発行

    ・解決する課題： 紙の見積によるタイムロスを無くし、2〜3 パターンの商品を自動比較。お得額を可視化して顧客満足度を向上させます。

    <img width="1079" height="919" alt="ss4" src="https://github.com/user-attachments/assets/c0387968-f0c3-4015-8be4-7711f8e2b37d" />

5.  【業務標準化】予定ボード ＆ ピット空き状況（スマート予約）

    ・解決する課題： 誰が受付しても「作業ピットの空き時間」が視覚的に分かり、ダブルブッキングや受付ミスをゼロにします。

    <img width="1697" height="868" alt="ss5-1" src="https://github.com/user-attachments/assets/b8bfeb46-477c-4430-96ff-e967299ce8cb" />
    <img width="1705" height="995" alt="ss5-2" src="https://github.com/user-attachments/assets/72961d69-59fd-4b77-a273-ea88b735b362" />

ーーー

💻 使用技術（Tech Stack）

・Language: Python 3.9.12

・Framework: Streamlit (UI/UX 構築)

・Frontend: HTML5 / CSS3 (カスタムコンポーネント・印刷用レイアウト制御)

・Data Storage: CSV ベースによる軽量・高速なデータマネジメント

ーーー

📈 コミット履歴（一部抜粋）

・本プロジェクトは、Git による厳格なバージョン管理を行い、機能ごとにクリーンなコミット粒度を意識してビルドしています。

・feat: delete record with confirmation dialog （誤操作防止の 2 ステップ削除）

・feat: duplicate record button + HH:mm datetime display （過去の来店記録の複製機能）

・feat: 2-step NAVIMO-style quote flow with discount presets （見積フローの 2 軸化）

・Quote UI: retail vs offer 2-col layout, savings highlight, print CSS fix （見積画面の最適化）

・Initial commit: GS Support System （ベースシステムの構築）
