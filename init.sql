-- Инициализация базы данных dbname

-- Таблица для верификации токенов
CREATE TABLE "LiteLLM_VerificationTokenView" (
    id SERIAL PRIMARY KEY,
    token VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Таблица глобальных расходов за месяц
CREATE TABLE "MonthlyGlobalSpend" (
    id SERIAL PRIMARY KEY,
    month VARCHAR(7) NOT NULL, -- Формат: 'YYYY-MM'
    total_spend DECIMAL(15, 2) DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица расходов по ключам за последние 30 дней
CREATE TABLE "Last30dKeysBySpend" (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL,
    spend DECIMAL(15, 2) DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица расходов по моделям за последние 30 дней
CREATE TABLE "Last30dModelsBySpend" (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    spend DECIMAL(15, 2) DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица расходов по ключам за месяц
CREATE TABLE "MonthlyGlobalSpendPerKey" (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL,
    month VARCHAR(7) NOT NULL, -- Формат: 'YYYY-MM'
    spend DECIMAL(15, 2) DEFAULT 0.0,
    UNIQUE (key, month)
);

-- Таблица расходов по пользователям и ключам за месяц
CREATE TABLE "MonthlyGlobalSpendPerUserPerKey" (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    key VARCHAR(255) NOT NULL,
    month VARCHAR(7) NOT NULL, -- Формат: 'YYYY-MM'
    spend DECIMAL(15, 2) DEFAULT 0.0,
    UNIQUE (user_id, key, month)
);

-- Таблица расходов по тегам за день
CREATE TABLE "DailyTagSpend" (
    id SERIAL PRIMARY KEY,
    tag VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    spend DECIMAL(15, 2) DEFAULT 0.0,
    UNIQUE (tag, date)
);

-- Таблица топ-10 пользователей по расходам за последние 30 дней
CREATE TABLE "Last30dTopEndUsersSpend" (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    spend DECIMAL(15, 2) DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);