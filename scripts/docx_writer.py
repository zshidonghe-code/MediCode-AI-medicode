"""Minimal .docx generator using only stdlib (zipfile + xml.etree). No lxml dependency."""
import zipfile
import os
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace

# OOXML namespaces
NSMAP = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
}
for prefix, uri in NSMAP.items():
    register_namespace(prefix, uri)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

def _tag(ns, name):
    return f"{{{ns}}}{name}"


class DocxWriter:
    def __init__(self):
        self.body = Element(_tag(W, "body"))
        self.document = Element(_tag(W, "document"))
        self.document.append(self.body)
        self._rels: list[tuple[str, str, str]] = []  # (id, type, target)

    def add_heading(self, text: str, level: int = 1):
        p = SubElement(self.body, _tag(W, "p"))
        pPr = SubElement(p, _tag(W, "pPr"))
        pStyle = SubElement(pPr, _tag(W, "pStyle"))
        pStyle.set(_tag(W, "val"), f"Heading{level}")
        r = SubElement(p, _tag(W, "r"))
        t = SubElement(r, _tag(W, "t"))
        t.set("{}space", "preserve")
        t.text = text

    def add_para(self, text: str, bold: bool = False, italic: bool = False, size: int = 11, color: str = "000000", alignment: str = "left"):
        p = SubElement(self.body, _tag(W, "p"))
        pPr = SubElement(p, _tag(W, "pPr"))
        if alignment != "left":
            jc = SubElement(pPr, _tag(W, "jc"))
            jc.set(_tag(W, "val"), alignment)
        r = SubElement(p, _tag(W, "r"))
        rPr = SubElement(r, _tag(W, "rPr"))
        if bold:
            SubElement(rPr, _tag(W, "b"))
        if italic:
            SubElement(rPr, _tag(W, "i"))
        if color != "000000":
            c = SubElement(rPr, _tag(W, "color"))
            c.set(_tag(W, "val"), color)
        sz = SubElement(rPr, _tag(W, "sz"))
        sz.set(_tag(W, "val"), str(size * 2))  # half-points
        t = SubElement(r, _tag(W, "t"))
        t.set("{}space", "preserve")
        t.text = text

    def add_table(self, headers: list[str], rows: list[list[str]]):
        tbl = SubElement(self.body, _tag(W, "tbl"))
        tblPr = SubElement(tbl, _tag(W, "tblPr"))
        tblW = SubElement(tblPr, _tag(W, "tblW"))
        tblW.set(_tag(W, "w"), "5000")
        tblW.set(_tag(W, "type"), "pct")
        tblBorders = SubElement(tblPr, _tag(W, "tblBorders"))
        for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
            border = SubElement(tblBorders, _tag(W, border_name))
            border.set(_tag(W, "val"), "single")
            border.set(_tag(W, "sz"), "4")
            border.set(_tag(W, "space"), "0")
            border.set(_tag(W, "color"), "CCCCCC")

        # Header row
        tr = SubElement(tbl, _tag(W, "tr"))
        for h in headers:
            tc = SubElement(tr, _tag(W, "tc"))
            tcPr = SubElement(tc, _tag(W, "tcPr"))
            shd = SubElement(tcPr, _tag(W, "shd"))
            shd.set(_tag(W, "val"), "clear")
            shd.set(_tag(W, "color"), "auto")
            shd.set(_tag(W, "fill"), "D9E8F7")
            p = SubElement(tc, _tag(W, "p"))
            r = SubElement(p, _tag(W, "r"))
            rPr = SubElement(r, _tag(W, "rPr"))
            SubElement(rPr, _tag(W, "b"))
            sz = SubElement(rPr, _tag(W, "sz"))
            sz.set(_tag(W, "val"), "20")
            t = SubElement(r, _tag(W, "t"))
            t.set("{}space", "preserve")
            t.text = str(h)

        # Data rows
        for row in rows:
            tr = SubElement(tbl, _tag(W, "tr"))
            for cell in row:
                tc = SubElement(tr, _tag(W, "tc"))
                p = SubElement(tc, _tag(W, "p"))
                r = SubElement(p, _tag(W, "r"))
                t = SubElement(r, _tag(W, "t"))
                t.set("{}space", "preserve")
                t.text = str(cell)

        # Empty paragraph after table
        SubElement(self.body, _tag(W, "p"))

    def _build_document_xml(self) -> str:
        return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + tostring(self.document, encoding="unicode")

    def save(self, path: str):
        doc_xml = self._build_document_xml()
        rels_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + tostring(
            Element(_tag(R, "Relationships")), encoding="unicode")

        ct_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                  '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                  '<Default Extension="xml" ContentType="application/xml"/>'
                  '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                  '</Types>')

        root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                     '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                     '</Relationships>')

        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", ct_xml)
            zf.writestr("_rels/.rels", root_rels)
            zf.writestr("word/document.xml", doc_xml)
            zf.writestr("word/_rels/document.xml.rels", rels_xml)


def add_table_simple(doc: DocxWriter, headers: list[str], rows: list[list[str]]):
    """Convenience: add table + empty paragraph."""
    doc.add_table(headers, rows)


# ─── Test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    doc = DocxWriter()
    doc.add_heading("Test Document", 1)
    doc.add_para("This is a test paragraph with bold text.", bold=False)
    doc.add_table(["Col A", "Col B", "Col C"], [["1", "2", "3"], ["a", "b", "c"]])
    doc.add_para("End test.")
    out = os.path.expanduser("~/Desktop/test_stdlib_docx.docx")
    doc.save(out)
    print(f"Saved: {out} ({os.path.getsize(out)} bytes)")
