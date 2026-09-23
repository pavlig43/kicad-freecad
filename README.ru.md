# TrueLib: установка на другом компьютере

Нужны KiCad 10, Git и Python 3.10 или новее. Один раз откройте KiCad 10, чтобы он создал общие таблицы библиотек. Затем закройте KiCad.

Откройте терминал в папке, где хотите хранить библиотеку. Путь может быть любым.

## Windows (PowerShell)

```powershell
git clone https://github.com/pavlig43/kicad-freecad.git
cd kicad-freecad
.\install.cmd
```

## Linux и macOS

```sh
git clone https://github.com/pavlig43/kicad-freecad.git
cd kicad-freecad
sh ./install.sh
```

После установки откройте KiCad заново. Знаки и футпринты будут в библиотеке `TrueLib`; путь к STEP настроится сам.

## Обновление

Закройте KiCad. В папке клона запустите `.\update.cmd` в Windows PowerShell или `sh ./update.sh` в Linux и macOS. Скрипт скачает новые файлы через Git и проверит путь библиотеки. Если клон перенесли, запустите установку ещё раз.

Проверка без правок: `.\install.cmd --check` в Windows PowerShell или `sh ./install.sh --check` в Linux и macOS.

Установщик делает копии файлов настроек перед правкой. Если имя `TrueLib` уже занято другой библиотекой, он остановится. Старые проекты и `my_lyb` не меняются.
