-- ====================================================================
-- PROYECTO: Asistente Personal Inteligente Multi-Agente
-- FASE 3: Esquema de Base de Datos PostgreSQL / Supabase
-- ====================================================================

-- Habilitar extensión UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Función para actualizar automáticamente el campo updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- --------------------------------------------------------------------
-- 1. TABLA: USERS
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50),
    preferences JSONB DEFAULT '{"language": "es", "currency": "USD", "notifications": true}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- --------------------------------------------------------------------
-- 2. TABLA: TASKS (Gestionada por el Secretary Agent)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    priority VARCHAR(20) NOT NULL DEFAULT 'medium' 
        CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    category VARCHAR(50) NOT NULL DEFAULT 'general',
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- --------------------------------------------------------------------
-- 3. TABLA: EMAILS (Gestionada por el Secretary Agent)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sender VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body TEXT,
    snippet VARCHAR(500),
    status VARCHAR(50) NOT NULL DEFAULT 'unread' 
        CHECK (status IN ('unread', 'read', 'archived', 'starred', 'spam')),
    category VARCHAR(50) NOT NULL DEFAULT 'general' 
        CHECK (category IN ('general', 'finance', 'work', 'personal', 'promotions', 'alerts')),
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_important BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emails_user_id ON emails(user_id);
CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(status);
CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at);

CREATE TRIGGER update_emails_updated_at
    BEFORE UPDATE ON emails
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- --------------------------------------------------------------------
-- 4. TABLA: FINANCIAL_ACCOUNTS (Cuentas Bancarias / Billeteras)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS financial_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(50) NOT NULL 
        CHECK (account_type IN ('checking', 'savings', 'investment', 'cash', 'digital_wallet')),
    institution VARCHAR(100) NOT NULL,
    account_number_mask VARCHAR(20),
    balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'active' 
        CHECK (status IN ('active', 'inactive', 'frozen', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON financial_accounts(user_id);

CREATE TRIGGER update_accounts_updated_at
    BEFORE UPDATE ON financial_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- --------------------------------------------------------------------
-- 5. TABLA: CREDIT_CARDS (Tarjetas de Crédito)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS credit_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_name VARCHAR(100) NOT NULL,
    institution VARCHAR(100) NOT NULL,
    card_number_mask VARCHAR(20),
    credit_limit NUMERIC(15, 2) NOT NULL,
    current_balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    available_credit NUMERIC(15, 2) GENERATED ALWAYS AS (credit_limit - current_balance) STORED,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    cutoff_day SMALLINT CHECK (cutoff_day BETWEEN 1 AND 31),
    due_day SMALLINT CHECK (due_day BETWEEN 1 AND 31),
    status VARCHAR(20) NOT NULL DEFAULT 'active' 
        CHECK (status IN ('active', 'blocked', 'cancelled', 'expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_credit_cards_user_id ON credit_cards(user_id);

CREATE TRIGGER update_credit_cards_updated_at
    BEFORE UPDATE ON credit_cards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- --------------------------------------------------------------------
-- 6. TABLA: LOANS (Préstamos e Hipotecas)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lender_name VARCHAR(100) NOT NULL,
    loan_type VARCHAR(50) NOT NULL 
        CHECK (loan_type IN ('personal', 'mortgage', 'auto', 'student', 'business')),
    original_amount NUMERIC(15, 2) NOT NULL,
    remaining_balance NUMERIC(15, 2) NOT NULL,
    interest_rate_annual NUMERIC(5, 2) NOT NULL,
    monthly_payment NUMERIC(15, 2) NOT NULL,
    payment_day SMALLINT CHECK (payment_day BETWEEN 1 AND 31),
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' 
        CHECK (status IN ('active', 'paid_off', 'defaulted', 'refinanced')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_loans_user_id ON loans(user_id);

CREATE TRIGGER update_loans_updated_at
    BEFORE UPDATE ON loans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- --------------------------------------------------------------------
-- 7. TABLA: SAVING_GOALS (Metas de Ahorro)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS saving_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_name VARCHAR(100) NOT NULL,
    target_amount NUMERIC(15, 2) NOT NULL,
    current_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    deadline DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress' 
        CHECK (status IN ('in_progress', 'completed', 'paused', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_saving_goals_user_id ON saving_goals(user_id);

CREATE TRIGGER update_saving_goals_updated_at
    BEFORE UPDATE ON saving_goals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- --------------------------------------------------------------------
-- 8. TABLA: TRANSACTIONS (Ingresos, Gastos y Transferencias)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id UUID REFERENCES financial_accounts(id) ON DELETE SET NULL,
    credit_card_id UUID REFERENCES credit_cards(id) ON DELETE SET NULL,
    type VARCHAR(20) NOT NULL 
        CHECK (type IN ('income', 'expense', 'transfer')),
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    category VARCHAR(50) NOT NULL,
    description VARCHAR(255) NOT NULL,
    merchant VARCHAR(100),
    transaction_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'posted' 
        CHECK (status IN ('pending', 'posted', 'cancelled', 'refunded')),
    source VARCHAR(50) NOT NULL DEFAULT 'manual' 
        CHECK (source IN ('manual', 'webhook_bank', 'voice_agent', 'email_import')),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_credit_card_id ON transactions(credit_card_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);

CREATE TRIGGER update_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
