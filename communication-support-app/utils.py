"""
ユーティリティ：乱数・重複防止・お題生成・エクスポート
=========================================================
責務：
- 乱数シードの安定化（任意の文字列→intシード変換）
- セッション内ユニーク（モード×レベル＝dedup_key 単位）管理
- 各モードのお題生成（n=3固定／スコアや順位付けは一切しない）

設計上の注意：
- 「重複防止」はセッション期間中に同一アイテムを再提示しない方針。
- すべての候補を使い切った後は、UIの「重複履歴リセット」で再提示を許容。
- 36の質問は constants の配列を直接参照。ビジネス言い換えは別配列。
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime
from typing import List, Optional

import streamlit as st

from constants import (
    Mode,
    AA36_QUESTIONS,
    AA36_BUSINESS_REWRITE,
    ITTAKU_TOPICS,
    ITTAKU_BUSINESS_TOPICS,
    CRIMINAL_TEMPLATE,
    COMPLAINER_TEMPLATE,
)

# ============================================================================ #
# RNG / Seeding
# ============================================================================ #
def _seed_to_int(seed: Optional[str]) -> Optional[int]:
    """
    任意文字列シードを、再現性のある安定的な int に変換する。
    - None/空文字は None を返す（=乱数に任せる）
    - 有値の場合は SHA-256 の先頭 16hex を int 化
    """
    if not seed:
        return None
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def get_rng(seed: Optional[str]) -> random.Random:
    """
    乱数生成器を返す。
    - seed が None の場合は非決定的な乱数
    - seed が指定されている場合は安定的な乱数系列
    """
    s = _seed_to_int(seed)
    if s is None:
        return random.Random()
    return random.Random(s)


# ============================================================================ #
# 重複防止（セッション内ユニーク管理）
# ============================================================================ #
def _get_used_set(dedup_key: str) -> set:
    """
    指定 dedup_key の使用済みハッシュ集合を返す。
    無ければ空集合を新規作成。
    """
    used_map = st.session_state.get("used_prompt_ids", {})
    if dedup_key not in used_map:
        used_map[dedup_key] = set()
        st.session_state["used_prompt_ids"] = used_map
    return used_map[dedup_key]

def _mark_used(dedup_key: str, pid: int) -> None:
    """
    指定 dedup_key において、アイテム識別子（pid=hash(str)）を使用済みに登録。
    """
    used_map = st.session_state["used_prompt_ids"]
    used_map.setdefault(dedup_key, set()).add(pid)
    st.session_state["used_prompt_ids"] = used_map

def _sample_without_used(
    items: List[str],
    n: int,
    rng: random.Random,
    dedup_key: str,
) -> List[str]:
    """
    使用済みを避けて n 件サンプルを返す。
    - 候補が n 件未満の場合は可能な範囲で返す（その後はフルプールから）
    - バッチ内重複を避ける（履歴の再提示は基本なし）
    - 取得したアイテムは使用済みにマークする
    """
    used = _get_used_set(dedup_key)
    candidates = [s for s in items if hash(s) not in used]

    if len(candidates) >= n:
        chosen = rng.sample(candidates, n)
    else:
        chosen = list(candidates)
        still_need = n - len(chosen)
        refill = items[:]  # フルプールから補充（バッチ内重複は避ける）
        while still_need > 0 and refill:
            pick = rng.choice(refill)
            if pick not in chosen:
                chosen.append(pick)
                still_need -= 1
            refill.remove(pick)

    # 取得アイテムを使用済みに登録
    for c in chosen:
        _mark_used(dedup_key, hash(c))
    return chosen

# ============================================================================ #
# プロンプト・ビルダ
# ============================================================================ #
def _aa36_pool(level: str) -> List[str]:
    """
    アーサー・アーロン36の質問のうち、レベルに応じた配列を返す。
    - beginner: 1–12
    - intermediate: 13–24
    - advanced: 25–36
    - business: ビジネス言い換え配列
    """
    if level == "business":
        return AA36_BUSINESS_REWRITE
    if level == "beginner":
        return AA36_QUESTIONS[0:12]
    if level == "intermediate":
        return AA36_QUESTIONS[12:24]
    if level == "advanced":
        return AA36_QUESTIONS[24:36]
    # 万一のフォールバック（全件）
    return AA36_QUESTIONS

def _ittaku_pool(level: str) -> List[str]:
    """
    結論！実際それ一択のテーマ配列を返す。
    """
    if level == "beginner":
        return ITTAKU_TOPICS
    if level == "topic_only":
        return ITTAKU_TOPICS
    if level == "business_topic":
        return ITTAKU_BUSINESS_TOPICS
    # フォールバック
    return ITTAKU_TOPICS

def _villain_pool(level: str) -> List[str]:
    """
    悪事の正当化テンプレート（犯罪／クレーマー）を返す。
    """
    if level == "criminal":
        return CRIMINAL_TEMPLATE
    if level == "claimer":
        return COMPLAINER_TEMPLATE
    # フォールバック
    return CRIMINAL_TEMPLATE

# ============================================================================ #
# 外部公開API：お題生成
# ============================================================================ #
def get_prompts(
    mode: Mode,
    level: str,
    n: int,
    rng: random.Random,
    dedup_key: str,
) -> List[str]:
    
    """
    指定モード/レベルに応じて、お題を n 件返す。
    返り値は「表示用テキスト」のみで、スコア/メタ情報は持たせない。
    指定モード/レベルで n 件のプロンプト文字列を返す。
    """
    if mode == Mode.AA36:
        pool = _aa36_pool(level)
        chosen = _sample_without_used(pool, n, rng, dedup_key)

    elif mode == Mode.ITTAKU:
        pool = _ittaku_pool(level)
        chosen = _sample_without_used(pool, n, rng, dedup_key)

    else:  # Mode.VILLAIN
        pool = _villain_pool(level)
        chosen = _sample_without_used(pool, n, rng, dedup_key)

    return chosen
