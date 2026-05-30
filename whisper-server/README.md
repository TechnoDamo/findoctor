# whisper-server

OpenAI-совместимый HTTP-сервер распознавания речи на базе [whisper.cpp](https://github.com/ggml-org/whisper.cpp). Преобразует аудиофайлы в текст, работает полностью локально, без облачных API.

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Структура](#структура)
- [Команды Make](#команды-make)
- [Конфигурация](#конфигурация)
- [API](#api)
- [curl-примеры](#curl-примеры)
- [Тестирование](#тестирование)
- [Аппаратное ускорение](#аппаратное-ускорение)
- [Выбор модели](#выбор-модели)
- [Тюнинг производительности](#тюнинг-производительности)
- [Интеграция с ФинДоктор](#интеграция-с-финдоĸтор)
- [Диагностика](#диагностика)

## Быстрый старт

```bash
cd whisper-server

# 1. Создать .env из шаблона
make init

# 2. Собрать whisper.cpp (аппаратное ускорение включится автоматически)
make build

# 3. Скачать модель
make model

# 4. Установить зависимости Python-прокси
make proxy-install

# 5. Запустить OpenAI-совместимый прокси
make run
```

После запуска прокси слушает на `127.0.0.1:8080`. Эндпоинт — `POST /chat/completions` (полная совместимость с форматом Chat Completions API, который использует бэкенд ФинДоктор).

Прокси автоматически запускает whisper.cpp на внутреннем порту (`WHISPER_CPP_PORT=8082` по умолчанию) и транслирует запросы между форматами:
- Принимает JSON с base64 `input_audio` (Chat Completions, как отправляет бэкенд)
- Отправляет multipart/form-data в whisper.cpp (`/inference`)
- Возвращает Chat Completions-ответ (`choices[0].message.content`)

## Структура

```
whisper-server/
├── whisper.cpp/          # Git-сабмодуль whisper.cpp (v1.8.5)
│   ├── models/           # Скачанные ggml-модели
│   ├── build/            # Сборочные артефакты (bin/whisper-server)
│   └── ...
├── proxy_server.py       # FastAPI-прокси — транслирует Chat Completions ↔ whisper.cpp
├── requirements.txt      # Python-зависимости прокси
├── .env.example          # Шаблон переменных окружения
├── .env                  # Рабочий конфиг (не коммитится)
├── Makefile              # Система сборки и управления
└── README.md
```

## Команды Make

| Команда | Назначение |
|---|---|
| `make help` | Справка по всем командам |
| `make init` | Создать `.env` из `.env.example` |
| `make build` | Собрать whisper.cpp с аппаратным ускорением |
| `make model` | Скачать Whisper-модель |
| `make proxy-install` | Установить Python-зависимости прокси |
| `make run` | Запустить OpenAI-совместимый прокси (рекомендуемый режим) |
| `make run-raw` | Запустить whisper.cpp напрямую (отладка) |
| `make info` | Информация о системе и конфигурации |
| `make test` | Запустить тестовый набор |
| `make clean` | Удалить сборочные артефакты |

## Конфигурация

Все параметры задаются в `.env`. Полный список:

### Модель

| Переменная | По умолчанию | Описание |
|---|---|---|
| `WHISPER_MODEL` | `large-v3-turbo` | Имя модели. Доступные: `tiny`, `tiny.en`, `base`, `base.en`, `small`, `small.en`, `medium`, `medium.en`, `large-v1`, `large-v2`, `large-v3`, `large-v3-turbo` |
| `WHISPER_MODELS_DIR` | `./whisper.cpp/models` | Путь к директории с файлами моделей |

### Сервер

| Переменная | По умолчанию | Описание |
|---|---|---|
| `WHISPER_HOST` | `127.0.0.1` | Адрес, на котором слушает прокси |
| `WHISPER_PORT` | `8080` | Порт прокси (наружу) |
| `WHISPER_CPP_PORT` | `8082` | Внутренний порт whisper.cpp (прокси управляет им) |

### Производительность

| Переменная | По умолчанию | Описание |
|---|---|---|
| `WHISPER_THREADS` | `4` | Количество потоков CPU |
| `WHISPER_PROCESSORS` | `1` | Количество параллельных обработчиков запросов |

### Распознавание

| Переменная | По умолчанию | Описание |
|---|---|---|
| `WHISPER_LANGUAGE` | `auto` | Язык (`auto` — автоопределение, `ru` — русский, `en` — английский и т.д.) |
| `WHISPER_MAX_CONTEXT` | `-1` | Макс. число токенов контекста. `-1` — без ограничения |
| `WHISPER_MAX_LEN` | `0` | Макс. длина сегмента в символах. `0` — без ограничения |
| `WHISPER_BEST_OF` | `5` | Количество лучших кандидатов для beam search |
| `WHISPER_BEAM_SIZE` | `-1` | Размер beam. `-1` — автоматически |
| `WHISPER_NO_SPEECH_THOLD` | `0.6` | Порог вероятности «нет речи» (0.0–1.0) |

### Флаги (true/false)

| Переменная | По умолчанию | Что делает |
|---|---|---|
| `WHISPER_NO_TIMESTAMPS` | `false` | Не включать временные метки в ответ |
| `WHISPER_SPLIT_ON_WORD` | `false` | Разбивать по словам, а не по токенам |
| `WHISPER_DEBUG_MODE` | `false` | Режим отладки (дампит log-mel спектрограммы) |
| `WHISPER_CONVERT` | `false` | Конвертировать входной формат через ffmpeg |
| `WHISPER_NO_GPU` | `false` | Не использовать GPU (только CPU) |
| `WHISPER_FLASH_ATTN` | `true` | Flash Attention (ускоряет инференс) |
| `WHISPER_NO_CONTEXT` | `false` | Не использовать контекст предыдущих запросов |
| `WHISPER_SUPPRESS_NST` | `false` | Подавлять non-speech токены |

### OpenAI-совместимые пути (режим `run-raw`)

При использовании whisper.cpp напрямую (`make run-raw`) можно задать кастомные пути:

| Переменная | По умолчанию | Описание |
|---|---|---|
| `WHISPER_REQUEST_PATH` | *пусто* | Префикс пути. Задайте `/v1` |
| `WHISPER_INFERENCE_PATH` | *пусто* | Путь эндпоинта. Задайте `/audio/transcriptions` |

При пустых значениях эндпоинт доступен как `POST /inference`.

В режиме по умолчанию (`make run`, через прокси) эти переменные не нужны — прокси предоставляет `POST /chat/completions`.

### Промпт и ускорение

| Переменная | По умолчанию | Описание |
|---|---|---|
| `WHISPER_PROMPT` | *пусто* | Начальный промпт (только для английских моделей) |
| `WHISPER_ACCELERATION` | *пусто* | Принудительный выбор ускорения: `coreml`, `cuda`, `metal`, `opencl`, `vulkan`, `openblas`, `hipblas`, `none` |

## API

### POST /inference

Транскрипция аудиофайла. Поддерживает форматы WAV, MP3, FLAC, OGG (при `WHISPER_CONVERT=true` — любые, которые понимает ffmpeg). Максимальный размер — 100 МБ.

**Запрос** (multipart/form-data):

```bash
curl -X POST http://127.0.0.1:8080/inference \
  -F "file=@audio.wav" \
  -F "response_format=json"
```

Параметры формы:

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `file` | file | *обязателен* | Аудиофайл |
| `response_format` | string | `json` | Формат ответа: `json`, `verbose_json`, `text`, `srt`, `vtt` |
| `language` | string | из `.env` | Язык аудио. `auto` — автоопределение |
| `temperature` | float | `0.0` | Temperature сэмплирования |
| `prompt` | string | из `.env` | Начальный промпт |

**Ответ** (json):

```json
{
  "text": "Распознанный текст полностью",
  "segments": [
    {
      "id": 0,
      "text": "Текст первого сегмента",
      "start": 0.0,
      "end": 5.2
    }
  ]
}
```

**Ответ** (verbose_json):

```json
{
  "task": "transcribe",
  "language": "russian",
  "duration": 12.345,
  "text": "...",
  "segments": [...],
  "detected_language": "ru",
  "detected_language_probability": 0.98,
  "language_probabilities": {"ru": 0.98, "en": 0.01, ...}
}
```

### POST /load

Загрузка другой модели без перезапуска сервера:

```bash
curl -X POST http://127.0.0.1:8080/load \
  -F "model=./models/ggml-large-v3.bin"
```

## curl-примеры

Все примеры предполагают, что сервер запущен на `127.0.0.1:8080` и есть тестовый аудиофайл `test.wav`.

### Базовая транскрипция

```bash
# JSON (по умолчанию) — возвращает полный текст и сегменты
curl -s -X POST http://127.0.0.1:8080/inference \
  -F "file=@audio.wav" \
  -F "response_format=json" | python3 -m json.tool
```

### Подробный JSON с информацией о языке

```bash
curl -s -X POST http://127.0.0.1:8080/inference \
  -F "file=@audio.wav" \
  -F "response_format=verbose_json" | python3 -m json.tool
```

В ответе дополнительно: `task`, `language`, `duration`, `detected_language`, `language_probabilities`, токены и вероятности слов в сегментах.

### Чистый текст

```bash
curl -s -X POST http://127.0.0.1:8080/inference \
  -F "file=@audio.wav" \
  -F "response_format=text"
```

### Субтитры SRT

```bash
curl -s -X POST http://127.0.0.1:8080/inference \
  -F "file=@audio.wav" \
  -F "response_format=srt" -o subtitles.srt
```

### Субтитры VTT

```bash
curl -s -X POST http://127.0.0.1:8080/inference \
  -F "file=@audio.wav" \
  -F "response_format=vtt" -o subtitles.vtt
```

### Указание языка вручную

```bash
# Принудительно русский — быстрее и точнее автоопределения
curl -s -X POST http://127.0.0.1:8080/inference \
  -F "file=@audio.wav" \
  -F "language=ru" \
  -F "response_format=json"
```

### С температурой сэмплирования

```bash
# Больше вариативности (0.0 — детерминированно, 1.0 — разнообразнее)
curl -s -X POST http://127.0.0.1:8080/inference \
  -F "file=@audio.wav" \
  -F "temperature=0.2" \
  -F "response_format=json"
```

### С начальным промптом

```bash
# Промпт помогает модели выбрать контекст (только для английских моделей)
curl -s -X POST http://127.0.0.1:8080/inference \
  -F "file=@audio.wav" \
  -F "prompt=The following is a financial report about..." \
  -F "response_format=json"
```

### Загрузить другую модель на лету

```bash
# Переключиться на medium без перезапуска сервера
curl -s -X POST http://127.0.0.1:8080/load \
  -F "model=./models/ggml-medium.bin"
```

### С конвертацией через ffmpeg

```bash
# Если сервер запущен с WHISPER_CONVERT=true, можно передавать любые форматы
curl -s -X POST http://127.0.0.1:8080/inference \
  -F "file=@recording.mp4" \
  -F "response_format=json"
```

### Chat Completions API (прокси)

```bash
# Формат, идентичный тому, что отправляет бэкенд ФинДоктор
BASE64=$(base64 -i audio.wav | tr -d '\n')
curl -s -X POST http://127.0.0.1:8080/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer not-needed" \
  -d "{
    \"model\": \"whisper-large-v3-turbo\",
    \"messages\": [{
      \"role\": \"user\",
      \"content\": [
        {\"type\": \"text\", \"text\": \"Transcribe the audio.\"},
        {\"type\": \"input_audio\", \"input_audio\": {\"data\": \"$BASE64\", \"format\": \"wav\"}}
      ]
    }]
  }" | python3 -m json.tool
```

### OpenAI Audio Transcriptions (режим `run-raw`)

```bash
# При настроенных WHISPER_REQUEST_PATH=/v1 и WHISPER_INFERENCE_PATH=/audio/transcriptions
curl -s -X POST http://127.0.0.1:8080/v1/audio/transcriptions \
  -H "Authorization: Bearer not-needed" \
  -F "file=@audio.wav" \
  -F "model=whisper-1" \
  -F "language=ru" | python3 -m json.tool
```

### Замер скорости

```bash
time curl -s -o /dev/null -w "HTTP %{http_code}, %{size_download} bytes, %{time_total}s\n" \
  -X POST http://127.0.0.1:8080/inference \
  -F "file=@large_audio.wav" \
  -F "response_format=json"
```

### Пакетная обработка папки

```bash
for f in recordings/*.wav; do
  echo "=== $f ===" >> transcripts.txt
  curl -s -X POST http://127.0.0.1:8080/inference \
    -F "file=@$f" \
    -F "response_format=text" >> transcripts.txt
  echo "" >> transcripts.txt
done
```

### Проверка здоровья сервера

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/
```

## Тестирование

```bash
# Запуск полного тестового набора
make test
```

Тесты проверяют:
1. Базовую транскрипцию (json, текст, verbose_json)
2. SRT и VTT форматы субтитров
3. Параметры `language` и `temperature`
4. Обработку ошибок (запрос без файла)
5. Отклик сервера на корневой эндпоинт
6. Детерминированность результата

Для тестов автоматически используется `for-tests-ggml-tiny.bin` (уже есть в `whisper.cpp/models/`) и скачивается тестовый аудиосэмпл `jfk.wav` (если отсутствует).

## Аппаратное ускорение

При сборке (`make build`) Makefile автоматически определяет доступное железо и включает соответствующие бэкенды.

### Автоопределение

| Платформа | Ускорение |
|---|---|
| macOS (Intel) | CoreML (Apple Neural Engine) |
| macOS (Apple Silicon) | CoreML + Metal (GPU) + Accelerate (BLAS) |
| Linux + NVIDIA GPU | CUDA |
| Linux + AMD GPU | ROCm / HIP |
| Linux без GPU | OpenBLAS (если установлен) |

### Ручной выбор

Задайте `WHISPER_ACCELERATION` в `.env`:

```bash
# Только CPU, без ускорения
WHISPER_ACCELERATION=none

# Конкретный бэкенд
WHISPER_ACCELERATION=cuda
```

Доступные значения: `coreml`, `cuda`, `metal`, `opencl`, `vulkan`, `openblas`, `hipblas`, `none`.

### Требования по бэкендам

- **CoreML**: macOS 12+ (встроен в ОС)
- **Metal**: macOS, Apple Silicon (встроен в ОС)
- **CUDA**: драйвер NVIDIA + CUDA Toolkit
- **ROCm/HIP**: драйвер AMD ROCm + `rocminfo`
- **OpenCL**: ICD-лоадер и драйвер устройства
- **Vulkan**: Vulkan SDK и драйвер устройства
- **OpenBLAS**: пакет `openblas` (`brew install openblas` / `apt install libopenblas-dev`)

## Выбор модели

Размер и качество моделей (от меньшей к большей):

| Модель | Размер | VRAM / RAM | Скорость | Качество |
|---|---|---|---|---|
| `tiny` / `tiny.en` | ~75 МБ | ~200 МБ | ★★★★★ | ★★ |
| `base` / `base.en` | ~140 МБ | ~300 МБ | ★★★★ | ★★★ |
| `small` / `small.en` | ~460 МБ | ~800 МБ | ★★★ | ★★★★ |
| `medium` / `medium.en` | ~1.5 ГБ | ~2.5 ГБ | ★★ | ★★★★★ |
| `large-v3` | ~3 ГБ | ~5 ГБ | ★ | ★★★★★★ |
| `large-v3-turbo` | ~1.5 ГБ | ~2.5 ГБ | ★★★ | ★★★★★★ |

- `.en` модели — только английский, быстрее и точнее для английской речи
- Рекомендация для русского языка: `large-v3-turbo` — лучший баланс скорости и качества
- `large-v3-turbo` по качеству сопоставим с `large-v3`, но в 2 раза меньше и быстрее

## Тюнинг производительности

### Увеличение скорости

```bash
# Больше потоков
WHISPER_THREADS=8

# Меньше кандидатов — быстрее, но чуть ниже качество
WHISPER_BEST_OF=2
```

### Улучшение качества

```bash
# Максимальные параметры beam search
WHISPER_BEST_OF=10
WHISPER_BEAM_SIZE=10

# Фиксированный язык (быстрее и точнее автоопределения)
WHISPER_LANGUAGE=ru
```

### Работа с длинными аудио

```bash
# Увеличить контекст для связности
WHISPER_MAX_CONTEXT=512

# Включить VAD для авторазбивки на сегменты (требует сборки с VAD)
```

### Параллельная обработка

```bash
# Количество одновременных запросов
WHISPER_PROCESSORS=4
```

Каждый процессор загружает свою копию модели. Увеличивайте осторожно — потребление RAM растёт линейно.

## Интеграция с ФинДоктор

whisper-server — полностью локальная замена облачным STT-провайдерам для голосового режима ФинДоктор.

Бэкенд использует Chat Completions API с `input_audio` (формат GPT-4o Audio Preview). Прокси принимает этот формат напрямую — замена прозрачна.

Подключение в `backend/.env`:

```bash
# whisper-server (прокси на порту 8080)
STT_BASE_URL=http://127.0.0.1:8080
STT_API_KEY=not-needed
STT_MODEL=whisper-large-v3-turbo
```

Бэкенд отправляет:
```
POST http://127.0.0.1:8080/chat/completions
Content-Type: application/json
{
  "model": "whisper-large-v3-turbo",
  "messages": [{
    "role": "user",
    "content": [
      {"type": "text", "text": "Transcribe the user's audio."},
      {"type": "input_audio", "input_audio": {"data": "<base64>", "format": "wav"}}
    ]
  }]
}
```

Прокси:
1. Извлекает base64-аудио, пишет во временный WAV
2. Отправляет multipart в whisper.cpp (`/inference`)
3. Возвращает Chat Completions-ответ, который бэкенд уже умеет парсить

## Диагностика

### `make info` — сводка состояния

```bash
$ make info
=== System ===
OS:           Darwin
Architecture: arm64

=== Hardware Acceleration ===
CMake args:   -DWHISPER_BUILD_SERVER=ON -DWHISPER_COREML=ON ...

=== Model ===
Model:        large-v3-turbo
Status:       Downloaded (1.5G)

=== Server ===
Host:         127.0.0.1:8080
Threads:      4 | Language: auto
Endpoint:     /inference
```

### Проверка, что ускорение работает

После запуска сервера отправьте тестовый запрос и смотрите логи. При использовании Metal/CoreML в логах будет:

```
whisper_init_from_file_with_params: loading model from 'models/ggml-large-v3-turbo.bin'
...
whisper_init_state: Core ML: using Metal device
whisper_init_state: Core ML: model loaded
```

### Типовые проблемы

**Сборка падает с ошибкой «Metal not found»**

macOS 11+ включает Metal по умолчанию. Если ошибка на более старой версии — отключите Metal в `.env`:
```bash
WHISPER_ACCELERATION=coreml
```

**Сервер не стартует — «model not found»**

Скачайте модель:
```bash
make model
```

**Модель не помещается в память**

Используйте модель поменьше:
```bash
WHISPER_MODEL=small
make model
```

**Медленная работа на CPU**

Убедитесь, что установлен OpenBLAS (`brew install openblas` / `apt install libopenblas-dev`), затем пересоберите:
```bash
make clean && make build
```

**Ошибка «Killed» при загрузке модели на маломощном сервере**

Модель `large-v3` требует ~5 ГБ RAM. Используйте `large-v3-turbo` (~2.5 ГБ) или `medium` (~2.5 ГБ).
