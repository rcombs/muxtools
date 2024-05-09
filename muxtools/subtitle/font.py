import os
import shutil
import logging
from pathlib import Path
from font_collector import ABCFontFace

from .sub import SubFile, FontFile as MTFontFile
from ..utils.env import get_workdir
from ..utils.log import warn, error, info


def _weight_to_name(weight: int) -> str | int:
    # https://learn.microsoft.com/en-us/typography/opentype/spec/os2#usweightclass
    match weight:
        case 100:
            return "Thin"
        case 200:
            return "ExtraLight"
        case 300:
            return "Light"
        case 400:
            return ""
        case 500:
            return "Medium"
        case 600:
            return "SemiBold"
        case 700:
            return "Bold"
        case 800:
            return "ExtraBold"
        case 900:
            return "Black"
    return weight


def _get_fontname(font: ABCFontFace) -> str:
    filename_fallback = False
    exact_fallback = False

    name = ""
    try:
        try:
            found = font.get_family_name_from_lang("en")
            if not found:
                found = font.get_best_family_name()
            name = found.value
        except:
            pass
        if not name:
            found = font.get_exact_name_from_lang("en")
            if not found:
                found = font.get_best_exact_name()
            name = found.value
            exact_fallback = True
    except:
        name = Path(font.font_file.filename).with_suffix("").name.strip()
        filename_fallback = True

    if not filename_fallback:
        if " " in name:
            name = "".join([(part.capitalize() if part.islower() else part) for part in name.split(" ")])
        elif "-" in name and exact_fallback:
            name = "".join([(part.strip().capitalize() if part.islower() else part.strip()) for part in name.split("-")])
        else:
            name = name.capitalize()
        weight = _weight_to_name(font.weight)
        name = f"{name}{'-' + weight if weight and str(weight) not in name else ''}"
        if isinstance(weight, int):
            name += f"-{'Italic' if font.is_italic else ''}"
        else:
            name += "Italic" if font.is_italic else ""

    return name


def collect_fonts(
    sub: SubFile, use_system_fonts: bool = True, additional_fonts: list[Path] = [], collect_draw_fonts: bool = True, error_missing: bool = False
) -> list[MTFontFile]:
    from font_collector import set_loglevel

    set_loglevel(logging.CRITICAL)

    from font_collector import AssDocument, FontLoader, FontCollection, FontSelectionStrategyLibass

    font_collection = FontCollection(
        use_system_fonts, additional_fonts=FontLoader.load_additional_fonts(additional_fonts, scan_subdirs=True) if additional_fonts else []
    )
    load_strategy = FontSelectionStrategyLibass()

    doc = AssDocument(sub._read_doc())
    styles = doc.get_used_style(collect_draw_fonts)

    found_fonts: list[MTFontFile] = []

    for style, usage_data in styles.items():
        query = font_collection.get_used_font_by_style(style, load_strategy)

        if not query:
            msg = f"Font '{style.fontname}' was not found!"
            if error_missing:
                raise error(msg, collect_fonts)
            else:
                warn(msg, collect_fonts, 3)
        else:
            fontname = _get_fontname(query.font_face)

            info(f"Found font '{fontname}'.", collect_fonts)
            fontpath = Path(query.font_face.font_file.filename)
            outpath = os.path.join(get_workdir(), f"{fontname}{fontpath.suffix}")
            missing_glyphs = query.font_face.get_missing_glyphs(usage_data.characters_used)
            if len(missing_glyphs) != 0:
                warn(f"'{fontname}' is missing the following glyphs: {missing_glyphs}", collect_fonts, 3)
            if query.need_faux_bold:
                warn(f"'{fontname}' is using faux bold!", collect_fonts, 2)
            if not Path(outpath).exists():
                shutil.copy(fontpath, outpath)

    for f in get_workdir().glob("*.[tT][tT][fF]"):
        found_fonts.append(MTFontFile(f))
    for f in get_workdir().glob("*.[oO][tT][fF]"):
        found_fonts.append(MTFontFile(f))
    return found_fonts
