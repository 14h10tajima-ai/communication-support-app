"""
UI コンポーネント集（Streamlit描画のみ）
========================================
責務：
- 画面ヘッダ/サイドバー/カード/フッター等の描画関数を集約
- アプリの状態管理は原則 `st.session_state` に委譲
- ビジネスロジック（データ選定等）は utils 側へ集約し分離

保守方針：
- 画面構成や文言の変更は本ファイル
- プロンプト生成や履歴管理の変更は utils.py
"""
from __future__ import annotations

from typing import List, Dict, Any

import streamlit as st

from constants import (
    Mode,
    LEVEL_LABELS_AA36,
    LEVEL_LABELS_ITTAKU,
    LEVEL_LABELS_VILLAIN,
)
import constants as ct


# ============================================================================ #
# Header / Sidebar
# ============================================================================ #
def render_header() -> None:
    """
    画面上部のタイトルとサブ説明を描画。
    固定テキストのみを扱い、ロジックは持たない。
    """
    # タイトルは定数から取得
    st.title(ct.APP_TITLE)

    # 説明文は caption として簡潔に表示（文言自体は既存を流用）
    st.caption(
        "会話の始まりをデザインするツールです。"
        "質問・ロールプレイ・合意形成を通して、より深い相互理解を促します。"
    )


def _level_labels_for_mode(mode: Mode) -> Dict[str, str]:
    """
    モード別のレベル選択肢ラベルを返す。
    UI 用のみに使用。
    """
    if mode == Mode.AA36:
        return LEVEL_LABELS_AA36
    if mode == Mode.ITTAKU:
        return LEVEL_LABELS_ITTAKU
    return LEVEL_LABELS_VILLAIN


def render_sidebar_controls() -> Dict[str, Any]:
    """
    サイドバーのコントロール群を描画し、選択値を返却する。

    Returns:
        Dict[str, Any]: mode, level, seed, dedup_key を含む辞書
    """
    with st.sidebar:
        st.subheader("⚙️ 設定")

        # モード選択（3モード固定）
        mode: Mode = st.selectbox(
            "モード",
            options=[Mode.AA36, Mode.ITTAKU, Mode.VILLAIN],
            format_func=lambda m: m.label,
        )

        # レベル選択（モードに応じてラベル切り替え）
        level_labels = _level_labels_for_mode(mode)
        level_key = st.selectbox(
            "レベル",
            options=list(level_labels.keys()),
            format_func=lambda k: level_labels[k],
        )
        level = level_key

        # 乱数シード（UI 非表示・将来拡張用）
        seed = ""

        # 新しいお題・質問を生成（重複履歴をリセット）
        if st.button(
            "🔄 質問/お題の更新",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["used_prompt_ids"] = {}
            st.toast("次のお題を生成しました。", icon="✨")

        # モード×レベル単位で dedup_key を付与（外部I/Fへ渡す）
        dedup_key = f"{mode.value}:{level}"

        st.divider()

    return {
        "mode": mode,
        "level": level,
        "seed": seed or None,
        "dedup_key": dedup_key,
    }


# ============================================================================ #
# Prompt Cards
# ============================================================================ #
def render_prompt_cards(
    prompts: List[str],
    mode: Mode,
    level: str,
) -> None:
    """
    メインカラムに質問/お題カードを描画する。
    """
    # モード説明との区切り
    st.markdown("---")

    # セクション見出し
    if len(prompts) == 3:
        st.markdown("### 質問")
    else:
        st.markdown("### お題")

    # 各質問/お題のカード表示
    for i, p in enumerate(prompts, start=1):
        with st.container():
            st.code(p, language="markdown")


# ============================================================================ #
# Explain card
# ============================================================================ #
def render_mode_help(mode: ct.Mode) -> None:
    """モードごとの概要と遊び方を表示するヘルプカード。"""
    help_data = ct.MODE_HELP_MAP.get(mode)
    if not help_data:
        return

    # モード名（セクションタイトル）
    st.markdown(f"## {help_data.name}")

    # 要約（1行程度）
    if help_data.summary:
        st.write(help_data.summary)

    # 詳細な遊び方は折りたたみ内に格納
    if help_data.notes:
        with st.expander("遊び方", expanded=True):
            for note in help_data.notes:
                st.markdown(f"- {note}")
