from __future__ import annotations
from pathlib import Path
import re



# paths for dataset
ROOT = Path(__file__).resolve().parents[2]

RAW = ROOT / "data" / "raw"

CEDICT_FILE = RAW / "cedict_ts.u8"
UNIHAN_DIR = RAW / "unihan"
MMAH_FILE = RAW / "makemeahanzi" / "dictionary.txt"

def load_unihan(wanted_fields: set[str]) -> dict[int, dict[str,str]]:
    """Read every Unihan_*.txt file and keep only the fields we want.

    Returns {unicode (bit16 -> decimal): {field_name: value}}, e.g.
        {22909: {"kMandarin": "hǎo", "kTotalStrokes": "6", ...}}
    """

    data: dict[int, dict[str,str]] = {}
    files = sorted(UNIHAN_DIR.glob("Unihan_*.txt"))

    if not files:
        raise FileNotFoundError("No Unihan_*.txt files found")
    
    for path in files:
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                code, field, val = line.strip().split("\t", 2)
                if field in wanted_fields:
                    data.setdefault(int(code[2:],16), {})[field] = val

    return data

def first_int(value: str | None) -> int | None:
    '''parse first int from unihan dataset. ex: 10.9 -> 10'''
    if not value:
        return None

    m = re.match(r"\d+",value)
    return int(m.group()) if m else None


# CEDICT PINYIN CONVERSION

# Index 0..3 are tones 1..4, index 4 is the unmarked vowel.
TONE_MARKS = {
    "a": "āáǎàa",
    "e": "ēéěèe",
    "i": "īíǐìi",
    "o": "ōóǒòo",
    "u": "ūúǔùu",
    "ü": "ǖǘǚǜü",
}

SYLLABLE_RE = re.compile(r"([A-Za-z:]+)([1-5])")


def syllable_to_marked(syllable: str) -> str:
    """'hao3' -> 'hǎo'. Anything that is not a numbered syllable is returned unchanged."""
    m = SYLLABLE_RE.fullmatch(syllable)
    if not m:
        return syllable

    base, tone = m.group(1), int(m.group(2))
    base = base.replace("u:", "ü").replace("U:", "Ü")
    if tone == 5:
        return base  # neutral tone has no mark

    lower = base.lower()

    # Rules for where the tone mark goes:
    #   1. if there is an 'a' or an 'e', it goes there
    #   2. else if there is 'ou', it goes on the 'o'
    #   3. else it goes on the last vowel
    if "a" in lower:
        pos = lower.index("a")
    elif "e" in lower:
        pos = lower.index("e")
    elif "ou" in lower:
        pos = lower.index("o")
    else:
        pos = None
        for i in range(len(lower) - 1, -1, -1):
            if lower[i] in "aeiouü":
                pos = i
                break

    if pos is None:
        return base  # no vowel found (odd entries); leave as is

    original = base[pos]
    marked = TONE_MARKS[original.lower()][tone - 1]
    if original.isupper():
        marked = marked.upper()
    return base[:pos] + marked + base[pos + 1:]


def numbered_to_marked(text: str) -> str:
    """'ni3 hao3' -> 'nǐ hǎo'"""
    return " ".join(syllable_to_marked(s) for s in text.split())


def numbered_to_plain(text: str) -> str:
    """'Zhong1 guo2' -> 'zhong guo' (lowercase, no tones, ü written as u)."""
    out = []
    for syllable in text.split():
        syllable = re.sub(r"[1-5]$", "", syllable)
        syllable = syllable.replace("u:", "u").replace("U:", "U")
        out.append(syllable.lower())
    return " ".join(out)