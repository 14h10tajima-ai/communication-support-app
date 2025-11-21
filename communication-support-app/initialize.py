"""
セッション状態の初期化
===========================
責務：
- Streamlit の `st.session_state` に本アプリで必須となるキーを定義
- 既存値があれば保持し、未定義の場合のみ既定値を設定

カギとなるセッションキー：
- used_prompt_ids: {dedup_key -> set(hash(prompt_str))}   重複防止用
- history: [{ts, mode, level, prompts[], chosen}]         ログ/エクスポート用
"""

from __future__ import annotations

import streamlit as st


def ensure_session_state() -> None:
    """
    必須セッションキーを初期化する。
    既存の値は尊重し、欠損するキーのみ既定値を投入する。
    """
    defaults = {
        "used_prompt_ids": {},  # dict[str -> set[int]]
        "history": [],          # list[dict]
        "favorites": [],        # list[str]
        "seed_text": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
