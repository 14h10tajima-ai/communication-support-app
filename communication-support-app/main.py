"""
コミュニケーション補助（話題提供）アプリ
================================================================
- 【アプリ仕様ブロック（固定）】準拠：
    * RAG/DB/ベクターストア不使用（外部依存なし）
    * アーサー・アーロン36の質問／結論！実際それ一択／悪事の正当化の3モード
    * ランダム提示・重複防止（セッション内ユニーク）
- 依存：標準ライブラリ + streamlit のみ
- 起動方法：`streamlit run main.py`
"""

from __future__ import annotations

import random
from typing import Dict, Any

import streamlit as st

from constants import APP_TITLE, Mode
from initialize import ensure_session_state
from utils import get_rng, get_prompts
from components import (
    render_header,
    render_sidebar_controls,
    render_prompt_cards,
    render_mode_help,
)


# ============================================================================ #
# Streamlit ページエントリ
# ============================================================================ #
def page() -> None:
    """
    Streamlit UI の構築を一括で実行します。
    - サイドバーでパラメータを受け取り
    - 3件のお題を生成（重複防止）
    - 本文にカードUIを描画
    """

    # ページ設定（タイトルは constants 由来）
    st.set_page_config(page_title=APP_TITLE, page_icon="🍀", layout="wide")

    # セッション状態の必須キーを初期化
    ensure_session_state()

    # ヘッダ描画（固定文言）
    render_header()

    # サイドバー：モード・レベル
    controls: Dict[str, Any] = render_sidebar_controls()

    # モード別の説明カードを表示
    render_mode_help(controls["mode"])

    # 乱数生成器を確定（シード指定があれば再現性あり）
    rng: random.Random = get_rng(controls["seed"])
    n = 3 if controls["mode"] == Mode.AA36 else 1

    # 指定モード/レベルで 3 件のプロンプトを生成
    # - 「n=3」固定は仕様要件
    prompts = get_prompts(
        mode=controls["mode"],
        level=controls["level"],
        n=n,
        rng=rng,
        dedup_key=controls["dedup_key"],  # モード×レベル単位で重複防止
    )

    # 中央カラム：各お題カード
    render_prompt_cards(
        prompts=prompts,
        mode=controls["mode"],
        level=controls["level"],
    )


# ============================================================================ #
# 非 Streamlit 実行（ローカルCLI叩き）時の案内
# ============================================================================ #
def main() -> None:
    """
    直接 `python main.py` を実行した利用者への案内。
    Streamlit アプリとしての実行方法を表示します。
    """
    import textwrap

    print(
        textwrap.dedent(
            """
            このアプリは Streamlit で起動してください。

                streamlit run main.py

            必要条件:
            - Python 3.9+ 推奨
            - 追加依存は 'streamlit' のみ
            - 外部DB/RAG/ベクターストアは使用しません
            """
        )
    )


if __name__ == "__main__":
    # 直接実行時はガイドを表示。通常は `streamlit run main.py` を使用。
    main()

page()
