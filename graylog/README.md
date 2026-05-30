# Graylog Deployment

This folder runs a local Graylog stack for FinDoctor backend logs.

It uses the locally pulled images:

- `graylog/graylog:5.2`
- `mongo:6`
- `docker.elastic.co/elasticsearch/elasticsearch:7.17.23`

## Setup

```bash
cd graylog
make init-env
make up
make wait
make input
make streams
```

Open the UI:

```text
http://localhost:${GRAYLOG_HTTP_PORT}
```

Default local credentials from `.env.example`:

```text
admin / admin
```

Change these values in `graylog/.env` for real use.

## Commands

```bash
make up
make down
make restart
make logs
make status
make wait
make input
make streams
make configure
make reset-old
make test-input
```

`make input` creates a global GELF TCP input.

`make streams` creates project-specific streams:

- `FinDoctor Backend`
- `FinDoctor HTTP Traffic`
- `FinDoctor DB Writes`

`make configure` waits for Graylog, creates the GELF input, and creates the streams.

## Backend Configuration

The backend sends structured logs to Graylog when enabled in `backend/.env`:

```bash
GRAYLOG_ENABLED=true
GRAYLOG_REQUIRED=false
GRAYLOG_PROTOCOL=tcp
GRAYLOG_HOST=localhost
GRAYLOG_PORT=5556
GRAYLOG_FACILITY=findoctor-backend
LOG_HTTP_HEADERS=true
LOG_HTTP_BODIES=true
LOG_RESPONSE_HEADERS=true
LOG_RESPONSE_BODIES=true
LOG_DB_WRITES=true
```

HTTP middleware logs:

- request method/path/query
- all request headers
- full request body
- response status
- all response headers
- full response body
- request duration

DB write logging records:

- write operation type
- inferred table name
- affected row count
- duration
- parameter names

It intentionally does not log raw SQL parameter values for DB writes.
