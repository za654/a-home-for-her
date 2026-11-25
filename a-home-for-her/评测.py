# -*- coding: utf-8 -*-
"""评测 —— 量一量你家的检索准不准

用法：
    python 评测.py <你的家目录>
    python 评测.py <你的家目录> --cases 我的题目.txt

它做什么：
    把 找.py 当模块加载，跑一组"查询 → 应该找到哪份文件"的题，
    算 hit@1 / hit@3，并逐条打印对不对。

题目格式（一行一题，用 | 分隔，可以有多个正确答案）：
    小鹿|索引-我与家|小鹿.png
    账本翻过去|2026-11-11
    芙莉莲|芙莉莲|看过的

没有题目文件时，用下面这组内置的（针对示例家，换你自己家的内容）。
"""
import importlib.util
import sys
import time
from pathlib import Path

BUILTIN = """\
小鹿|索引-我与家|小鹿
那个画画的女孩|索引-我与家
账本翻过去|2026-11-11
长江的江水|索引-旅行
居酒屋的招牌|索引-我与家|居酒屋
老先生那块旧表|索引-我与家
写字的十条|写字的十条
"""


def load_engine(home: Path):
    zhao = home / "_水电" / "找.py"
    if not zhao.is_file():
        print("这个家里没有 _水电/找.py：%s" % home)
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("zhao", str(zhao))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_cases(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2 and parts[0]:
            rows.append((parts[0], tuple(p for p in parts[1:] if p)))
    return rows


def rank(Z, query, top=3):
    """直接调引擎自己的检索——评测和被测对象必须是同一段代码。"""
    hits, _mode, _dt = Z.search_ranked(query, "", top)
    return hits

def main(argv):
    if not argv:
        print(__doc__)
        return 1
    home = Path(argv[0])
    cases = read_cases(argv[2]) if len(argv) > 2 and argv[1] == "--cases" else None
    if cases is None:
        cases = []
        for line in BUILTIN.splitlines():
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                cases.append((parts[0], tuple(parts[1:])))
    Z = load_engine(home)

    hit1 = hit3 = 0
    t0 = time.time()
    for q, wants in cases:
        names = [str(it.get("src")) for it in rank(Z, q, 3)]
        ok1 = bool(names) and any(w in names[0] for w in wants)
        ok3 = any(w in n for n in names for w in wants)
        hit1 += ok1
        hit3 += ok3
        print("%s %-16s → %s" % ("✓" if ok1 else ("△" if ok3 else "✗"), q,
                                 names[0][:46] if names else "（无）"))
    n = max(1, len(cases))
    print()
    print("hit@1 = %d/%d = %.0f%%" % (hit1, len(cases), 100.0 * hit1 / n))
    print("hit@3 = %d/%d = %.0f%%" % (hit3, len(cases), 100.0 * hit3 / n))
    print("耗时 %.1f 秒" % (time.time() - t0))
    print()
    print("怎么看这两个数：")
    print("  hit@1  第一条就是对的 —— 她伸手拿到的第一张纸")
    print("  hit@3  前三里有一张对的 —— 她翻两下能翻到")
    print("  低于 70% 就说明词表或分块有问题，不是模型的问题")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
