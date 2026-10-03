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
