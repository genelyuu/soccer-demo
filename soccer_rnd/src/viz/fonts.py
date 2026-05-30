# -*- coding: utf-8 -*-
"""matplotlib 한글 폰트 설정 유틸리티.

모든 plot 스크립트가 공통으로 호출하여 한글 깨짐(tofu, □□□)을 방지한다.
우선순위: Noto Sans KR → Malgun Gothic → AppleGothic → NanumGothic.
시스템에 등록된 폰트가 없으면 Windows 폰트 디렉토리의 NotoSansKR 파일을 직접 등록한다.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# 선호 폰트 순서 (NotoSans 최우선)
_PREFERRED = ["Noto Sans KR", "Malgun Gothic", "AppleGothic", "NanumGothic"]

# 시스템 등록이 안 된 경우 직접 등록을 시도할 후보 파일
_FALLBACK_FILES = [
    Path("C:/Windows/Fonts/NotoSansKR-VF.ttf"),
    Path("C:/Windows/Fonts/malgun.ttf"),
]


def apply_korean_font() -> str:
    """matplotlib 전역 rcParams에 한글 폰트를 적용하고 선택된 폰트명을 반환한다."""
    available = {f.name for f in fm.fontManager.ttflist}
    chosen = next((name for name in _PREFERRED if name in available), None)

    if chosen is None:
        for path in _FALLBACK_FILES:
            if path.exists():
                fm.fontManager.addfont(str(path))
                chosen = fm.FontProperties(fname=str(path)).get_name()
                break

    plt.rcParams["font.family"] = chosen or "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False  # 음수 기호 깨짐 방지
    return chosen or "sans-serif"
