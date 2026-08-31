-- Create investigation_history table (table already exists, adding for documentation)
CREATE TABLE IF NOT EXISTS investigation_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID,
    root_cause TEXT,
    explanation TEXT,
    fix TEXT,
    kubectl_command JSONB,
    confidence INTEGER,
    namespace TEXT,
    status TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_investigation_history_user_id ON investigation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_investigation_history_created_at ON investigation_history(created_at DESC);