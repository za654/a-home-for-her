# -*- coding: utf-8 -*-
"""把仓库里的 md 转成 docx（标题 / 段落 / 表格 / 代码块 / 引用 / 列表）。"""
import os
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor


def set_cn(run, name="宋体"):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def add_code(doc, lines):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(12)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run("\n".join(lines))
    set_cn(r, "等线")
    r.font.size = Pt(9.5)


def add_table(doc, rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [c for c in cells if not all(re.fullmatch(r":?-{2,}:?", x or "-") for x in c)]
    if not cells:
        return
    n = max(len(r) for r in cells)
    t = doc.add_table(rows=0, cols=n)
    t.style = "Table Grid"
    for row in cells:
        cs = t.add_row().cells
        for i in range(n):
            cs[i].text = row[i] if i < len(row) else ""
            for p in cs[i].paragraphs:
                for r in p.runs:
                    set_cn(r)
                    r.font.size = Pt(10)


def md_to_docx(src, dst, title=None):
    lines = open(src, encoding="utf-8").read().splitlines()
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "宋体"
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i].rstrip())
                i += 1
            add_code(doc, buf)
            i += 1
            continue

        if line.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            add_table(doc, rows)
            continue

        if not line.strip():
            i += 1
            continue

        if line.startswith("# "):
            p = doc.add_paragraph()
            r = p.add_run(line[2:].strip())
            r.bold = True
            r.font.size = Pt(18)
            set_cn(r)
            i += 1
            continue

        if line.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            r = p.add_run(line[3:].strip())
            r.bold = True
            r.font.size = Pt(14)
            set_cn(r)
            i += 1
            continue

        if line.startswith("### "):
            p = doc.add_paragraph()
            r = p.add_run(line[4:].strip())
            r.bold = True
            r.font.size = Pt(12)
            set_cn(r)
            i += 1
            continue

        if line.strip() == "---":
            p = doc.add_paragraph()
            r = p.add_run("—" * 20)
            r.font.color.rgb = RGBColor(0xBB, 0xBB, 0xBB)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            i += 1
            continue

        if line.startswith(">"):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            txt = line.lstrip("> ").strip()
            r = p.add_run(txt)
            r.italic = True
            set_cn(r)
            i += 1
            continue

        if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\[\s?\]\s*", line):
            p = doc.add_paragraph(style="List Bullet")
            txt = re.sub(r"^\s*[-*]\s+", "", line)
            txt = re.sub(r"^\s*\[\s?\]\s*", "", txt)
            add_runs(p, txt)
            i += 1
            continue

        p = doc.add_paragraph()
        add_runs(p, line.strip())
        i += 1

    doc.save(dst)
    return dst


def add_runs(p, text):
    """处理 **加粗** 和 `代码`。"""
    parts = re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2])
            r.bold = True
            set_cn(r)
        elif part.startswith("`") and part.endswith("`"):
            r = p.add_run(part[1:-1])
            set_cn(r, "等线")
            r.font.size = Pt(10)
        else:
            r = p.add_run(part)
            set_cn(r)


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    for name in ("心法", "教程", "唤醒包", "找东西"):
        src = os.path.join(base, name + ".md")
        dst = os.path.join(base, name + ".docx")
        md_to_docx(src, dst)
        print("生成:", name + ".docx")
