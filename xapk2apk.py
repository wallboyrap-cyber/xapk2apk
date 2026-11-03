#!/usr/bin/env python3
"""
xapk2apk: XAPK / APKS -> один APK без сплитов (склейка + подпись).

Использование:
    python xapk2apk.py game.xapk
    python xapk2apk.py game.xapk -o result.apk

Нужно: Python 3.8+ и Java (JDK/JRE 8+) в PATH.
Инструменты (APKEditor, uber-apk-signer) скачиваются автоматически в ~/.xapk2apk
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

TOOLS_DIR = Path.home() / ".xapk2apk"
APKEDITOR_REPO = "REAndroid/APKEditor"
SIGNER_REPO = "patrickfav/uber-apk-signer"


def log(msg):
    print(f"[xapk2apk] {msg}", flush=True)


def fail(msg):
    print(f"[xapk2apk] ОШИБКА: {msg}", file=sys.stderr)
    sys.exit(1)


def download_latest_jar(repo, prefix):
    """Скачивает последний релизный .jar из GitHub, если его ещё нет."""
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(TOOLS_DIR.glob(f"{prefix}*.jar"))
    if existing:
        return existing[-1]

    log(f"Скачиваю {repo} ...")
    api = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(api, headers={"User-Agent": "xapk2apk"})
    with urllib.request.urlopen(req) as r:
        release = json.load(r)

    for asset in release.get("assets", []):
        name = asset["name"]
        if name.endswith(".jar") and name.startswith(prefix):
            dest = TOOLS_DIR / name
            urllib.request.urlretrieve(asset["browser_download_url"], dest)
            return dest
    fail(f"Не нашёл .jar в релизе {repo}. Скачай вручную в {TOOLS_DIR}")


def run(cmd):
    log("→ " + " ".join(str(c) for c in cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr, file=sys.stderr)
        fail("Команда завершилась с ошибкой")
    return res.stdout


def main():
    p = argparse.ArgumentParser(description="XAPK/APKS -> single APK")
    p.add_argument("input", help="путь к .xapk / .apks / .apkm")
    p.add_argument("-o", "--output", help="имя выходного .apk")
    args = p.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.is_file():
        fail(f"Файл не найден: {src}")
    if not shutil.which("java"):
        fail("Java не найдена. Установи JDK (https://adoptium.net) и добавь в PATH.")

    out = Path(args.output).resolve() if args.output else src.with_suffix(".apk")

    with zipfile.ZipFile(src) as z:
        names = z.namelist()
        apks = [n for n in names if n.lower().endswith(".apk")]
        obbs = [n for n in names if n.lower().endswith(".obb")]
        pkg = None
        if "manifest.json" in names:
            try:
                pkg = json.loads(z.read("manifest.json")).get("package_name")
            except Exception:
                pass

    if not apks:
        fail("Внутри архива нет .apk файлов")
    log(f"Найдено APK: {len(apks)}, OBB: {len(obbs)}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        merged = tmp / "merged.apk"

        if len(apks) == 1:
            log("Сплитов нет — просто извлекаю APK")
            with zipfile.ZipFile(src) as z:
                merged.write_bytes(z.read(apks[0]))
        else:
            editor = download_latest_jar(APKEDITOR_REPO, "APKEditor")
            run(["java", "-jar", editor, "m", "-i", src, "-o", merged])

        signer = download_latest_jar(SIGNER_REPO, "uber-apk-signer")
        signed_dir = tmp / "signed"
        run(["java", "-jar", signer, "-a", merged, "-o", signed_dir, "--allowResign"])

        signed = next(signed_dir.glob("*.apk"), None)
        if not signed:
            fail("Не получилось подписать APK")
        shutil.copy(signed, out)

    log(f"Готово: {out}")

    if obbs:
        obb_dir = out.parent / f"{out.stem}_obb"
        obb_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(src) as z:
            for n in obbs:
                (obb_dir / Path(n).name).write_bytes(z.read(n))
        target = pkg or "<package_name>"
        log(f"В архиве были OBB (кэш игры) → {obb_dir}")
        log(f"Положи их на телефон в Android/obb/{target}/")


if __name__ == "__main__":
    main()
