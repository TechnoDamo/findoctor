-- name: dashboard_summary
-- Сводка финансового состояния (общая валюта пользователя)
SELECT
    %(base_currency)s AS currency,
    cash.total_cash::text AS total_cash,
    assets.total_assets::text AS total_assets,
    liabilities.total_liabilities::text AS total_liabilities,
    (cash.total_cash + assets.total_assets - liabilities.total_liabilities)::text AS net_worth,
    monthly.monthly_income::text AS monthly_income,
    monthly.monthly_expenses::text AS monthly_expenses,
    CASE
        WHEN monthly.monthly_income > 0
        THEN ROUND(
            ((monthly.monthly_income - monthly.monthly_expenses) / monthly.monthly_income * 100)::numeric,
            2
        )::float
        ELSE NULL
    END AS savings_rate,
    COALESCE(recurring.items, '[]'::json) AS upcoming_recurring_transactions
FROM (
    SELECT COALESCE(SUM(balance), 0) AS total_cash
    FROM accounts
    WHERE user_id = %(user_id)s
      AND is_active
      AND currency = %(base_currency)s
) cash
CROSS JOIN (
    SELECT COALESCE(SUM(estimated_value), 0) AS total_assets
    FROM assets
    WHERE user_id = %(user_id)s
      AND currency = %(base_currency)s
) assets
CROSS JOIN (
    SELECT COALESCE(SUM(current_balance), 0) AS total_liabilities
    FROM liabilities
    WHERE user_id = %(user_id)s
      AND status = 'active'
      AND currency = %(base_currency)s
) liabilities
CROSS JOIN (
    SELECT
        COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS monthly_income,
        COALESCE(SUM(CASE WHEN type = 'expense' THEN ABS(amount) ELSE 0 END), 0) AS monthly_expenses
    FROM transactions
    WHERE user_id = %(user_id)s
      AND currency = %(base_currency)s
      AND transaction_datetime >= date_trunc('month', now())
) monthly
CROSS JOIN (
    SELECT COALESCE(
        json_agg(
            json_build_object(
                'id', id,
                'name', name,
                'expected_amount', expected_amount::text,
                'currency', currency,
                'next_payment_date', next_payment_date
            )
            ORDER BY next_payment_date ASC NULLS LAST
        ) FILTER (WHERE id IS NOT NULL),
        '[]'::json
    ) AS items
    FROM (
        SELECT id, name, expected_amount, currency, next_payment_date
        FROM recurring_transactions
        WHERE user_id = %(user_id)s
          AND is_active
          AND next_payment_date IS NOT NULL
        ORDER BY next_payment_date ASC
        LIMIT 5
    ) upcoming
) recurring;

-- name: list_snapshots
-- Список ежедневных финансовых снимков
SELECT id, user_id, snapshot_date, total_cash, total_assets, total_liabilities,
       net_worth, monthly_income, monthly_expenses, savings_rate
FROM daily_financial_snapshots
WHERE user_id = %(user_id)s
  AND (%(from)s::timestamptz IS NULL OR snapshot_date >= %(from)s)
  AND (%(to)s::timestamptz IS NULL OR snapshot_date <= %(to)s)
ORDER BY snapshot_date;

-- name: recalculate_snapshots
-- Удаление снимков за период для перерасчёта
DELETE FROM daily_financial_snapshots
WHERE user_id = %(user_id)s
  AND snapshot_date >= %(from)s
  AND snapshot_date <= %(to)s;

-- name: insert_snapshot
-- Вставка пересчитанного снимка
INSERT INTO daily_financial_snapshots (id, user_id, snapshot_date, total_cash, total_assets,
    total_liabilities, net_worth, monthly_income, monthly_expenses, savings_rate)
VALUES (gen_random_uuid(), %(user_id)s, %(snapshot_date)s, %(total_cash)s, %(total_assets)s,
    %(total_liabilities)s, %(net_worth)s, %(monthly_income)s, %(monthly_expenses)s, %(savings_rate)s);

-- name: cash_flow
-- Денежный поток по периодам (день/неделя/месяц)
SELECT
    date_trunc(%(group_by)s, t.transaction_datetime)::date AS period_start,
    COALESCE(SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END), 0)::text AS income,
    COALESCE(SUM(CASE WHEN t.type = 'expense' THEN ABS(t.amount) ELSE 0 END), 0)::text AS expenses,
    COALESCE(SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END) -
             SUM(CASE WHEN t.type = 'expense' THEN ABS(t.amount) ELSE 0 END), 0)::text AS net
FROM transactions t
WHERE t.user_id = %(user_id)s
  AND (%(from)s::timestamptz IS NULL OR t.transaction_datetime >= %(from)s)
  AND (%(to)s::timestamptz IS NULL OR t.transaction_datetime <= %(to)s)
GROUP BY period_start
ORDER BY period_start;

-- name: net_worth
-- История изменения чистого капитала
SELECT
    s.snapshot_date AS date,
    s.total_cash::text,
    s.total_assets::text,
    s.total_liabilities::text,
    s.net_worth::text
FROM daily_financial_snapshots s
WHERE s.user_id = %(user_id)s
  AND (%(from)s::timestamptz IS NULL OR s.snapshot_date >= %(from)s)
  AND (%(to)s::timestamptz IS NULL OR s.snapshot_date <= %(to)s)
ORDER BY s.snapshot_date;
