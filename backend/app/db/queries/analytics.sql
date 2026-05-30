-- name: dashboard_summary
-- Сводка финансового состояния (общая валюта пользователя)
SELECT
    %(base_currency)s AS currency,
    COALESCE(SUM(CASE WHEN a.is_active AND a.currency = %(base_currency)s THEN a.balance ELSE 0 END), 0)::text AS total_cash,
    COALESCE(SUM(CASE WHEN ast.currency = %(base_currency)s THEN ast.estimated_value ELSE 0 END), 0)::text AS total_assets,
    COALESCE(SUM(CASE WHEN l.currency = %(base_currency)s AND l.status = 'active' THEN l.current_balance ELSE 0 END), 0)::text AS total_liabilities,
    COALESCE(
        (SELECT COALESCE(SUM(CASE WHEN t.type = 'income' AND t.currency = %(base_currency)s THEN t.amount ELSE 0 END), 0)::text
         FROM transactions t
         WHERE t.user_id = %(user_id)s
           AND t.transaction_datetime >= date_trunc('month', now())),
        '0'
    ) AS monthly_income,
    COALESCE(
        (SELECT COALESCE(SUM(CASE WHEN t.type = 'expense' AND t.currency = %(base_currency)s THEN ABS(t.amount) ELSE 0 END), 0)::text
         FROM transactions t
         WHERE t.user_id = %(user_id)s
           AND t.transaction_datetime >= date_trunc('month', now())),
        '0'
    ) AS monthly_expenses
FROM accounts a
CROSS JOIN (SELECT %(user_id)s AS uid) u
LEFT JOIN assets ast ON ast.user_id = u.uid
LEFT JOIN liabilities l ON l.user_id = u.uid
WHERE a.user_id = u.uid;

-- name: list_snapshots
-- Список ежедневных финансовых снимков
SELECT id, user_id, snapshot_date, total_cash, total_assets, total_liabilities,
       net_worth, monthly_income, monthly_expenses, savings_rate
FROM daily_financial_snapshots
WHERE user_id = %(user_id)s
  AND (%(from)s IS NULL OR snapshot_date >= %(from)s)
  AND (%(to)s IS NULL OR snapshot_date <= %(to)s)
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
  AND (%(from)s IS NULL OR t.transaction_datetime >= %(from)s)
  AND (%(to)s IS NULL OR t.transaction_datetime <= %(to)s)
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
  AND (%(from)s IS NULL OR s.snapshot_date >= %(from)s)
  AND (%(to)s IS NULL OR s.snapshot_date <= %(to)s)
ORDER BY s.snapshot_date;
