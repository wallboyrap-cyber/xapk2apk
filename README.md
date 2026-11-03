# xapk2apk

Конвертер **XAPK / APKS / APKM → один APK** без сплитов. Склеивает base + config-сплиты (архитектура, язык, плотность экрана) и подписывает результат.

## Требования
- Python 3.8+
- Java 8+ (`java -version`)
- Интернет при первом запуске (скачает APKEditor и uber-apk-signer в `~/.xapk2apk`)

## Использование
```bash
python xapk2apk.py game.xapk
python xapk2apk.py game.xapk -o result.apk
```

Результат: `game.apk` рядом с исходником.

## OBB
Если в XAPK есть `.obb` (кэш игры), они выложатся в папку `<имя>_obb`. Скопируй их на телефон в `Android/obb/<package_name>/`.

## Ограничения
- Подпись отладочная, поэтому поверх оригинала из Play Market она не обновится: сначала удали старую версию.
- Некоторые приложения проверяют подпись или целостность и после пересборки могут не запускаться.
- Склеенный APK содержит все архитектуры и языки, поэтому он больше оригинального.

## Как выложить на GitHub
```bash
git init
git add .
git commit -m "xapk2apk"
gh repo create xapk2apk --public --source=. --push
```

## Благодарности
[APKEditor](https://github.com/REAndroid/APKEditor), [uber-apk-signer](https://github.com/patrickfav/uber-apk-signer)
