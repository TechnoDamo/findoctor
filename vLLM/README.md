# vLLM

OpenAI-совместимый HTTP-сервер инференса LLM на базе [vLLM](https://github.com/vllm-project/vllm). Работает полностью локально, без облачных API. Поддерживает автоопределение доступного железа — NVIDIA CUDA, AMD ROCm, CPU.

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Структура](#структура)
- [Команды Make](#команды-make)
- [Конфигурация](#конфигурация)
- [API](#api)
- [curl-примеры](#curl-примеры)
- [Тестирование и бенчмаркинг](#тестирование-и-бенчмаркинг)
- [Аппаратное ускорение](#аппаратное-ускорение)
- [Выбор модели](#выбор-модели)
- [Тюнинг производительности](#тюнинг-производительности)
- [Интеграция с ФинДоктор](#интеграция-с-финдоĸтор)
- [Диагностика](#диагностика)
- [Типовые проблемы](#типовые-проблемы)

## Быстрый старт

```bash
cd vLLM

# 1. Создать .env из шаблона
make init

# 2. Скачать Docker-образ
make pull

# 3. Запустить сервер (модель скачается автоматически при первом запуске)
make run
```

После запуска сервер слушает на `http://0.0.0.0:8100`. Основной эндпоинт — `POST /v1/chat/completions`.

Модель по умолчанию — `Qwen/Qwen2.5-1.5B-Instruct` (~3 ГБ), запускается практически на любом железе, включая CPU.

## Структура

```
vLLM/
├── .env.example          # Шаблон переменных окружения
├── .env                  # Рабочий конфиг (не коммитится)
├── Makefile              # Система управления
├── models/               # Кэш скачанных моделей (создаётся при запуске)
└── README.md
```

## Команды Make

| Команда | Назначение |
|---|---|
| `make help` | Справка по всем командам |
| `make init` | Создать `.env` из `.env.example` |
| `make pull` | Скачать Docker-образ и подготовить кэш моделей |
| `make download-model` | Скачать модель в кэш без запуска сервера |
| `make run` | Запустить vLLM-сервер |
| `make stop` | Остановить и удалить контейнер |
| `make restart` | Перезапустить сервер |
| `make logs` | Логи контейнера (follow) |
| `make shell` | Зайти в bash внутри контейнера |
| `make info` | Показать железо, конфигурацию, состояние сервера |
| `make test` | Полный набор тестов API + бенчмарк производительности |
| `make bench` | Только бенчмарк (сервер должен быть запущен) |
| `make clean` | Удалить контейнер |
| `make clean-all` | Удалить контейнер и весь кэш моделей |

## Конфигурация

Все параметры задаются в `.env`. Полный список:

### Модель

| Переменная | По умолчанию | Описание |
|---|---|---|
| `VLLM_MODEL` | `Qwen/Qwen2.5-1.5B-Instruct` | Идентификатор модели на HuggingFace Hub |
| `VLLM_REVISION` | *пусто* | Ревизия (ветка/тег/коммит), основная если пусто |
| `VLLM_TOKENIZER_MODE` | `auto` | Режим токенизатора: `auto`, `slow`, `mistral` |

### Сервер

| Переменная | По умолчанию | Описание |
|---|---|---|
| `VLLM_HOST` | `0.0.0.0` | Адрес, на котором слушает сервер |
| `VLLM_PORT` | `8100` | Порт сервера |
| `VLLM_CONTAINER_NAME` | `vllm-findoctor` | Имя Docker-контейнера |

### Аппаратное ускорение

| Переменная | По умолчанию | Описание |
|---|---|---|
| `VLLM_ACCELERATION` | *пусто* (авто) | Принудительный выбор: `cuda`, `rocm`, `cpu`. Пусто — автоопределение |
| `VLLM_TENSOR_PARALLEL` | `1` | Количество GPU для tensor parallelism |
| `VLLM_GPU_MEMORY_UTILIZATION` | `0.90` | Доля VRAM под KV-кэш (0.0–1.0) |
| `VLLM_MAX_MODEL_LEN` | *пусто* | Макс. длина контекста. Пусто — из конфига модели. Задайте число для экономии VRAM |

### Производительность

| Переменная | По умолчанию | Описание |
|---|---|---|
| `VLLM_MAX_NUM_SEQS` | `256` | Максимум одновременно обрабатываемых последовательностей |
| `VLLM_MAX_NUM_BATCHED_TOKENS` | *пусто* | Максимум токенов в батче (auto если пусто) |
| `VLLM_CPU_THREADS` | *пусто* | Потоки CPU (auto если пусто — все ядра) |

### Кэширование

| Переменная | По умолчанию | Описание |
|---|---|---|
| `VLLM_MODELS_DIR` | `./models` | Директория для кэша моделей на хосте |
| `VLLM_HF_HOME` | `/root/.cache/huggingface` | Путь к HuggingFace-кэшу внутри контейнера |

### Логирование

| Переменная | По умолчанию | Описание |
|---|---|---|
| `VLLM_LOG_LEVEL` | `info` | Уровень логов: `debug`, `info`, `warning`, `error` |

### Docker-образ

| Переменная | По умолчанию | Описание |
|---|---|---|
| `VLLM_IMAGE` | *пусто* (автовыбор) | Переопределить Docker-образ. Автовыбор: CUDA → `vllm/vllm-openai:latest`, ROCm → `rocm/vllm:latest`, CPU → `vllm/vllm-openai:latest-cpu` |
| `VLLM_PLATFORM` | *пусто* | Платформа Docker-образа (`linux/amd64`). На Apple Silicon Docker подставит сам |

### Тестирование и бенчмарк

| Переменная | По умолчанию | Описание |
|---|---|---|
| `VLLM_BENCH_ITERATIONS` | `5` | Количество итераций для бенчмарка |
| `VLLM_BENCH_CONCURRENCY` | `2` | Количество параллельных запросов |

## API

vLLM предоставляет OpenAI-совместимое API. Все эндпоинты доступны по префиксу `/v1`.

### GET /v1/models

Список загруженных моделей:

```bash
curl -s http://0.0.0.0:8100/v1/models | python3 -m json.tool
```

Ответ:

```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen2.5-1.5B-Instruct",
      "object": "model",
      "created": 1234567890,
      "owned_by": "vllm"
    }
  ]
}
```

### POST /v1/chat/completions

Основной эндпоинт — чат-завершения. Поддерживает streaming и non-streaming режимы.

**Параметры запроса:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `model` | string | *обязателен* | Идентификатор модели |
| `messages` | array | *обязателен* | Сообщения: `[{"role":"user/system/assistant","content":"..."}]` |
| `temperature` | float | `1.0` | Температура сэмплирования (0.0 — детерминированно) |
| `top_p` | float | `1.0` | Nucleus sampling |
| `max_tokens` | int | *безлимитно* | Максимальное число токенов в ответе |
| `stream` | bool | `false` | Потоковый режим (Server-Sent Events) |
| `stop` | string/array | *пусто* | Стоп-токены |
| `frequency_penalty` | float | `0.0` | Штраф за повторение |
| `presence_penalty` | float | `0.0` | Штраф за присутствие |
| `n` | int | `1` | Количество вариантов ответа |
| `seed` | int | *пусто* | Зерно генератора для воспроизводимости |

### GET /health

Проверка здоровья сервера:

```bash
curl -s http://0.0.0.0:8100/health
# → 200 OK (пустое тело)
```

## curl-примеры

Все примеры предполагают сервер на `http://0.0.0.0:8100`.

### Базовый текстовый запрос

```bash
curl -s -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "Что такое инфляция? Объясни кратко"}],
    "temperature": 0.7,
    "max_tokens": 200
  }' | python3 -m json.tool
```

Ответ:

```json
{
  "id": "cmpl-abc123",
  "object": "chat.completion",
  "created": 1717000000,
  "model": "Qwen/Qwen2.5-1.5B-Instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Инфляция — это устойчивый рост общего уровня цен на товары и услуги..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 45,
    "total_tokens": 70
  }
}
```

### Streaming (SSE)

```bash
curl -s -N -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "Расскажи короткую историю"}],
    "temperature": 0.7,
    "max_tokens": 100,
    "stream": true
  }'
```

Потоковый вывод — строки вида `data: {"choices":[{"delta":{"content":"токен"}}]}` с финальным `data: [DONE]`.

### Детерминированный ответ (temperature=0)

```bash
curl -s -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "Ответь числом: 2+2="}],
    "temperature": 0,
    "max_tokens": 10
  }'
```

### System prompt

```bash
curl -s -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [
      {"role": "system", "content": "Ты — финансовый консультант. Отвечай строго по делу, без лишних слов."},
      {"role": "user", "content": "Стоит ли брать кредит под 25% годовых?"}
    ],
    "temperature": 0.3,
    "max_tokens": 150
  }' | python3 -m json.tool
```

### История диалога (multi-turn)

```bash
curl -s -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [
      {"role": "user", "content": "Меня зовут Иван, мне 30 лет"},
      {"role": "assistant", "content": "Приятно познакомиться, Иван! Чем могу помочь?"},
      {"role": "user", "content": "Как меня зовут и сколько мне лет?"}
    ],
    "temperature": 0,
    "max_tokens": 30
  }'
```

### Ограничение длины ответа (max_tokens)

```bash
curl -s -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "Напиши длинное эссе об экономике"}],
    "temperature": 0,
    "max_tokens": 10
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])"
```

Ответ обрежется на ~10 токенах.

### JSON-ответ (только текст)

```bash
curl -s -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "Скажи привет"}],
    "max_tokens": 20
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### Проверка здоровья

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://0.0.0.0:8100/health
# → HTTP 200
```

### Проверка списка моделей — только id

```bash
curl -s http://0.0.0.0:8100/v1/models | python3 -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin)['data']]"
```

### Замер скорости (time)

```bash
time curl -s -o /dev/null -w "HTTP %{http_code}, %{size_download} bytes, %{time_total}s\n" \
  -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "Объясни что такое сложный процент"}],
    "temperature": 0,
    "max_tokens": 200
  }'
```

Вывод: HTTP-код, размер тела ответа, общее время запроса.

### Multi-turn диалог с историей (финансовый контекст)

```bash
curl -s -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [
      {"role": "system", "content": "Ты — личный финансовый ассистент. Помогаешь пользователю планировать бюджет, анализировать расходы и давать советы по сбережениям."},
      {"role": "user", "content": "Мой доход 100 000 рублей в месяц. Сколько стоит откладывать?"},
      {"role": "assistant", "content": "Рекомендую откладывать минимум 10-20% дохода — это 10 000-20 000 рублей в месяц. Из них сформируйте подушку безопасности (3-6 месячных расходов), а остальное инвестируйте."},
      {"role": "user", "content": "А если я хочу накопить на машину за год?"}
    ],
    "temperature": 0.5,
    "max_tokens": 200
  }' | python3 -m json.tool
```

### Temperature и top_p

```bash
# Творческий ответ (высокая температура)
curl -s -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "Придумай название для финтех-стартапа"}],
    "temperature": 1.0,
    "top_p": 0.9,
    "max_tokens": 50
  }'
```

### Пакетная обработка нескольких запросов

```bash
for question in \
  "Что такое дебет?" \
  "Что такое кредит?" \
  "Что такое баланс?"; do
  echo "=== Вопрос: $question ==="
  curl -s -X POST http://0.0.0.0:8100/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d "{\"model\":\"Qwen/Qwen2.5-1.5B-Instruct\",\"messages\":[{\"role\":\"user\",\"content\":\"$question\"}],\"temperature\":0,\"max_tokens\":60}" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
  echo ""
done
```

### Запрос с явным seed для воспроизводимости

```bash
curl -s -X POST http://0.0.0.0:8100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "Придумай пароль из 8 символов"}],
    "temperature": 1.0,
    "max_tokens": 20,
    "seed": 42
  }'
```

## Тестирование и бенчмаркинг

### `make test` — полный набор тестов

Запускает 9 тестов API и бенчмарк производительности. Если сервер уже запущен — использует его, иначе поднимает временный тестовый сервер.

```bash
make test
```

**Тесты проверяют:**

| # | Тест | Что проверяет |
|---|---|---|
| 1 | Health-чек | Сервер отвечает на `/health` |
| 2 | GET /v1/models | Список моделей не пуст, модель присутствует |
| 3 | Chat non-streaming | JSON-ответ, `choices[0].message.content` не пуст, usage-статистика |
| 4 | Chat streaming (SSE) | Заголовок, data-фреймы, сборка полного текста |
| 5 | Temperature=0 | Детерминированность (одинаковый ответ на одинаковый запрос) |
| 6 | System prompt | Ответ содержит ожидаемый паттерн из system-сообщения |
| 7 | Русский язык | Ответ содержит кириллицу |
| 8 | max_tokens | Ответ обрезается запрошенным лимитом |
| 9 | Ошибка: несуществующая модель | Сервер возвращает ошибку, а не 200 |

**Бенчмарк измеряет:**

| Метрика | Описание |
|---|---|
| **TTFT** (Time-To-First-Token) | Время до первого токена через streaming (3 итерации) |
| **Sequential throughput** | `VLLM_BENCH_ITERATIONS` последовательных non-streaming запросов. Измеряет время, токены, tok/s, stddev |
| **Parallel throughput** | `VLLM_BENCH_CONCURRENCY` одновременных запросов. Измеряет wall-time, latency, throughput, speedup |

Пример вывода бенчмарка:

```
────────────────────────────────────────────────────────────────────────
BENCHMARK SUMMARY
  TTFT (avg):            450 ms
  Seq throughput:        31.2 tok/s (5 requests, avg 3.21s)
  Parallel throughput:   43.8 tok/s (2 concurrent, wall 4.48s)
────────────────────────────────────────────────────────────────────────
```

### `make bench` — только бенчмарк

Сервер должен быть уже запущен (`make run`). Запускает те же измерения без тестов API:

```bash
make run    # запустить и дождаться загрузки
make bench  # только бенчмарк
```

Настройка количества итераций и параллельности — в `.env`:

```bash
VLLM_BENCH_ITERATIONS=10
VLLM_BENCH_CONCURRENCY=4
```

## Аппаратное ускорение

При запуске (`make run`, `make test`) Makefile автоматически определяет доступное железо и выбирает подходящий Docker-образ.

### Автоопределение

| Платформа | Бэкенд | Docker-образ | Docker-флаги |
|---|---|---|---|
| Linux + NVIDIA GPU | CUDA | `vllm/vllm-openai:latest` | `--gpus all` |
| Linux + AMD GPU | ROCm | `rocm/vllm:latest` | `--device /dev/kfd --device /dev/dri` |
| macOS (Intel/Apple Silicon) | CPU | `vllm/vllm-openai:latest-cpu` | — |
| Linux без GPU | CPU | `vllm/vllm-openai:latest-cpu` | — |

### Ручной выбор

Задайте `VLLM_ACCELERATION` в `.env`:

```bash
# Только CPU
VLLM_ACCELERATION=cpu

# Принудительно CUDA
VLLM_ACCELERATION=cuda

# Принудительно ROCm
VLLM_ACCELERATION=rocm
```

### Требования по бэкендам

| Бэкенд | Что нужно |
|---|---|
| **CUDA** | Драйвер NVIDIA (>=525), NVIDIA Container Toolkit (`nvidia-container-toolkit`) |
| **ROCm** | Драйвер AMD ROCm (>=6.0), Docker с поддержкой устройств |
| **CPU** | Ничего дополнительного. Работает на любом x86_64 или ARM64 (Apple Silicon) |

**Установка NVIDIA Container Toolkit (Linux):**

```bash
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker

# Проверка
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

### Apple Silicon (M1/M2/M3/M4)

На Mac Docker работает в виртуализации без прямого доступа к GPU. vLLM запускается в CPU-режиме. Производительность будет ниже, но для лёгких моделей (1.5B–7B параметров) вполне приемлема.

## Выбор модели

### Рекомендованные модели для русского языка

| Модель | Размер | VRAM / RAM | Скорость | Качество RU | Лицензия |
|---|---|---|---|---|---|
| `Qwen/Qwen2.5-1.5B-Instruct` | ~3 ГБ | ~3–4 ГБ | ★★★★★ | ★★ | Apache 2.0 |
| `Qwen/Qwen2.5-7B-Instruct` | ~14 ГБ | ~14–16 ГБ | ★★★★ | ★★★★ | Apache 2.0 |
| `Qwen/Qwen2.5-14B-Instruct` | ~28 ГБ | ~28–32 ГБ | ★★★ | ★★★★★ | Apache 2.0 |
| `Qwen/Qwen2.5-32B-Instruct` | ~64 ГБ | ~64–70 ГБ | ★★ | ★★★★★★ | Apache 2.0 |
| `google/gemma-3-4b-it` | ~8 ГБ | ~8–10 ГБ | ★★★★ | ★★ | Gemma |
| `meta-llama/Llama-3.1-8B-Instruct` | ~16 ГБ | ~16–18 ГБ | ★★★ | ★★★ | Llama 3.1 |

- `Qwen2.5-1.5B-Instruct` — сверхлёгкая, запускается на CPU, базовая поддержка русского. **По умолчанию.**
- `Qwen2.5-7B-Instruct` — лучший баланс качество/скорость для одной GPU (RTX 3060+, A10, T4).
- `Qwen2.5-14B-Instruct` — отличный русский, помещается на RTX 4090 (24 ГБ) с `VLLM_GPU_MEMORY_UTILIZATION=0.85`.
- `Qwen2.5-32B-Instruct` — лучший русский, нужна A100 (80 ГБ) или 2x RTX 4090.

### Квантизация для экономии VRAM

vLLM поддерживает GPTQ и AWQ квантизацию (4-bit). Чтобы использовать, укажите квантизованную версию модели:

```bash
VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ     # ~4 ГБ вместо ~14 ГБ
VLLM_MODEL=Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4  # ~8 ГБ вместо ~28 ГБ
```

### Как найти другие модели

Любая модель на [HuggingFace Hub](https://huggingface.co/models) с поддержкой `transformers` и архитектурой, которую понимает vLLM (Llama, Qwen, Mistral, Gemma, Phi, DeepSeek и др.), будет работать. Просто скопируйте идентификатор модели в `VLLM_MODEL`.

## Тюнинг производительности

### Увеличение throughput

```bash
# Больше параллельных последовательностей — выше пропускная способность, но больше VRAM
VLLM_MAX_NUM_SEQS=512

# Больше токенов в батче
VLLM_MAX_NUM_BATCHED_TOKENS=16384
```

### Экономия VRAM

```bash
# Ограничить длину контекста до 4096 вместо 32768 (по умолчанию у Qwen)
VLLM_MAX_MODEL_LEN=4096

# Уменьшить долю KV-кэша если GPU используется параллельно
VLLM_GPU_MEMORY_UTILIZATION=0.70
```

### Ускорение на нескольких GPU

```bash
# Tensor parallelism на 2 GPU
VLLM_TENSOR_PARALLEL=2
```

Требуется, чтобы модель помещалась в суммарную VRAM всех GPU.

### CPU-режим: больше потоков

```bash
# Задать количество потоков CPU вручную
VLLM_CPU_THREADS=16
```

По умолчанию используются все доступные ядра.

## Интеграция с ФинДоктор

vLLM — полностью локальная замена облачным LLM-провайдерам для AI-чата ФинДоктор.

Подключение в `backend/.env`:

```bash
# vLLM/.env
VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct
VLLM_PORT=8100
VLLM_GPU_MEMORY_UTILIZATION=0.85
VLLM_MAX_MODEL_LEN=8192

# backend/.env
LLM_BASE_URL=http://0.0.0.0:8100/v1
LLM_API_KEY=not-needed
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```

API vLLM полностью совместим с OpenAI Chat Completions, поэтому замена прозрачна для вызывающего кода. Backend использует `/chat/completions` — именно этот эндпоинт предоставляет vLLM.

**Важно:** vLLM заменяет только LLM-часть. STT и TTS продолжают работать через свои провайдеры (`STT_BASE_URL`, `TTS_BASE_URL`).

## Диагностика

### `make info` — сводка состояния

```bash
$ make info
=== Система ===
OS:            Linux
Архитектура:   x86_64

=== Аппаратное ускорение ===
Бэкенд:        cuda
Docker-образ:  vllm/vllm-openai:latest
GPU-флаги:     --gpus all

=== Модель ===
Модель:        Qwen/Qwen2.5-1.5B-Instruct
Ревизия:       основная
Кэш моделей:   /home/user/findoctor/vLLM/models
Размер кэша:   3.1G

=== Сервер ===
URL:           http://0.0.0.0:8100/v1
Порт:          8100
Контейнер:     vllm-findoctor
Max seqs:      256
GPU mem:       0.90

=== Контейнер ===
NAMES              STATUS          PORTS
vllm-findoctor     Up 5 minutes    0.0.0.0:8100->8100/tcp

=== Эндпоинты OpenAI ===
  Список моделей:  GET  http://0.0.0.0:8100/v1/models
  Chat:            POST http://0.0.0.0:8100/v1/chat/completions
  Health:          GET  http://0.0.0.0:8100/health

Интеграция с backend:
  LLM_BASE_URL=http://0.0.0.0:8100/v1
  LLM_API_KEY=not-needed
  LLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
```

### Проверка, что GPU используется

```bash
# При запуске с CUDA в логах будет:
make logs | grep -i "gpu\|cuda\|memory"

# Или зайдите в контейнер:
make shell
nvidia-smi
```

### Проверка доступного места на диске

Модели кэшируются в `vLLM/models/` на хосте:

```bash
du -sh vLLM/models/
df -h .
```

## Типовые проблемы

### «Cannot connect to the Docker daemon»

Docker не запущен. Запустите Docker Desktop (macOS) или `sudo systemctl start docker` (Linux).

### «could not select device driver with capabilities: [[gpu]]»

NVIDIA Container Toolkit не установлен:

```bash
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### «CUDA out of memory»

Модель не помещается в VRAM. Решения:

```bash
VLLM_GPU_MEMORY_UTILIZATION=0.70
VLLM_MAX_MODEL_LEN=4096
# или взять квантизованную версию:
VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ
# или модель поменьше:
VLLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
```

### Контейнер не запускается на macOS

Docker Desktop должен быть запущен. На Apple Silicon используется CPU-образ. Если образ не находится:

```bash
VLLM_PLATFORM=linux/amd64
```

### Модель не скачивается (нет интернета или HF-блокировка)

Скачайте модель заранее на машине с интернетом:

```bash
pip install huggingface_hub
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct --local-dir ./Qwen2.5-1.5B-Instruct
# Скопируйте папку в vLLM/models/hub/models--Qwen--Qwen2.5-1.5B-Instruct/
```

### Медленная работа на CPU

CPU-инференс LLM всегда медленнее GPU. Для ускорения:

```bash
VLLM_CPU_THREADS=16
VLLM_MAX_NUM_SEQS=4
VLLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
```

### Сервер долго грузится

Первая загрузка скачивает модель с HuggingFace (~3 ГБ для 1.5B). Скорость зависит от интернета. При последующих запусках модель берётся из кэша. Отслеживайте:

```bash
make logs
```

### Порт 8100 занят

```bash
lsof -i :8100
# Изменить порт в .env:
VLLM_PORT=8101
```

### «Permission denied» при монтировании models/

```bash
chmod -R 755 vLLM/models/
```
