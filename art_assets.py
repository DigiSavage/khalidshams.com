"""Validate optional illustration layers. SVG remains the source of technical diagrams."""
from pathlib import Path

STUDIES = {
    "atlas-workshop", "shams-autonomy", "production-review", "enterprise-clarity",
    "architectural-judgment", "thread-2077", "workbench-objects", "approval-mobile",
}
VARIANTS = {"desktop", "compact", "mobile", "thumb"}
THEMES = {"light", "dark"}


def validate_art(manifest, concepts, static):
    """Return actionable build errors; an empty manifest honestly means no supplied art."""
    errors, seen = [], set()
    if not isinstance(manifest, dict) or not isinstance(manifest.get("assets"), list):
        return ["art: assets must be a list"]
    for index, asset in enumerate(manifest["assets"]):
        prefix = f"art asset {index + 1}"
        if not isinstance(asset, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        for field in ("scene", "variant", "theme", "file", "purpose", "crop", "background", "alt"):
            if not isinstance(asset.get(field), str) or not asset[field].strip():
                errors.append(f"{prefix}: {field} must be nonempty text")
        scene, variant, theme = (asset.get(k) for k in ("scene", "variant", "theme"))
        valid = True
        for field, value, allowed in (("scene", scene, STUDIES), ("variant", variant, VARIANTS), ("theme", theme, THEMES)):
            if not isinstance(value, str) or value not in allowed:
                errors.append(f"{prefix}: unknown {field}")
                valid = False
        if asset.get("text_in_image") is not False:
            errors.append(f"{prefix}: text_in_image must be false; text-bearing studies are references only")
        for dimension in ("width", "height"):
            if dimension in asset and (type(asset[dimension]) is not int or asset[dimension] <= 0):
                errors.append(f"{prefix}: {dimension} must be a positive integer")
        ids = asset.get("concepts")
        if not isinstance(ids, list) or not ids or any(not isinstance(c, str) or c not in concepts for c in ids):
            errors.append(f"{prefix}: concepts must be a nonempty list of atlas concept ids")
        if not valid:
            continue
        key = (scene, variant, theme)
        if key in seen:
            errors.append(f"{prefix}: duplicate scene, variant and theme")
        seen.add(key)
        expected = f"/art/{scene}/{variant}-{theme}.webp"
        if asset.get("file") != expected:
            errors.append(f"{prefix}: file must be {expected}")
            continue
        root = Path(static).resolve()
        file = root / expected.lstrip("/")
        if not file.resolve().is_relative_to(root):
            errors.append(f"{prefix}: file escapes static directory")
        elif not file.is_file():
            errors.append(f"{prefix}: missing static{expected}")
        else:
            with file.open("rb") as stream:
                header = stream.read(12)
            if header[:4] != b"RIFF" or header[8:12] != b"WEBP":
                errors.append(f"{prefix}: expected a WebP file")
    return errors


def illustration(manifest, scene, *, eager=False):
    """Render a complete themed, responsive study; never silently omit requested art."""
    from html import escape
    assets = {(a['variant'], a['theme']): a for a in manifest['assets'] if a['scene'] == scene}
    missing = {(v, t) for v in VARIANTS for t in THEMES} - assets.keys()
    if missing:
        raise ValueError(f'art {scene}: missing variants {sorted(missing)}')
    if any(type(a.get(d)) is not int or a[d] <= 0 for a in assets.values() for d in ("width", "height")):
        raise ValueError(f"art {scene}: placed illustrations require positive width and height")
    pictures = []
    for theme in ('light', 'dark'):
        asset = assets['desktop', theme]
        srcset = ', '.join(f'{assets[v, theme]["file"]} {assets[v, theme]["width"]}w'
                           for v in ('thumb', 'mobile', 'compact', 'desktop'))
        pictures.append(f'<img class="art-{theme}" src="{escape(assets["compact", theme]["file"])}" '
                        f'srcset="{escape(srcset)}" sizes="(max-width: 767px) calc(100vw - 40px), (max-width: 1099px) 90vw, 50vw" '
                        f'width="{asset["width"]}" height="{asset["height"]}" '
                        f'alt="{escape(asset["alt"])}" loading="{"eager" if eager else "lazy"}" decoding="async">')
    labels = {
        'atlas-workshop': 'Outline operator: software metaphor · ⏸ Review boundary',
        'production-review': 'Outline operator: software metaphor · ⏸ Proposal awaiting review',
        'approval-mobile': 'Outline operator: software metaphor · ⏸ Proposal awaiting review',
        'thread-2077': 'Outline operators: software metaphor · Reading order, not runtime flow',
        'shams-autonomy': '⏸ Control boundary · Higher is not automatically better',
        'workbench-objects': '⏸ Control boundary · Instruments represent software components',
    }
    caption = f'<span class="art-caption">{labels[scene]}</span>' if scene in labels else ''
    return f'<span class="studio-art" data-art-scene="{escape(scene)}">'+''.join(pictures)+caption+'</span>'


# Only reuse a finished study when it depicts the concept being taught.
# Unmatched families retain their live drawing until their own art pair is ready.
CONCEPT_STUDIES = {
    "request": "atlas-workshop", "door-architect": "architectural-judgment",
    "assistant": "workbench-objects", "act-on-records": "production-review",
    "knowledge": "workbench-objects", "decide": "shams-autonomy",
    "Decide": "shams-autonomy", "Agents": "atlas-workshop",
    "Operate": "workbench-objects", "estate": "enterprise-clarity",
    "judgment": "architectural-judgment",
}


def concept_visual(key, diagram, cls=""):
    """Enhance the existing card position without replacing its technical drawing."""
    import json
    from html import escape
    scene = CONCEPT_STUDIES.get(key)
    if scene is None:
        return diagram
    manifest = json.loads((Path(__file__).parent / "content/art.json").read_text())
    return (f'<div class="concept-visual {escape(cls)}" data-concept-visual="{escape(key)}">'
            + illustration(manifest, scene)
            + '<details class="concept-details"><summary>Read the concept diagram</summary>'
            + diagram + '</details></div>')
