-- Enable RLS on investigation_history table
ALTER TABLE investigation_history ENABLE ROW LEVEL SECURITY;

-- Policy for users to view their own investigations
CREATE POLICY "Users can view own investigations" 
ON investigation_history FOR SELECT 
USING (auth.uid() = user_id);

-- Policy for users to insert their own investigations
CREATE POLICY "Users can insert own investigations" 
ON investigation_history FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Policy for users to update their own investigations
CREATE POLICY "Users can update own investigations" 
ON investigation_history FOR UPDATE 
USING (auth.uid() = user_id);

-- Policy for users to delete their own investigations
CREATE POLICY "Users can delete own investigations" 
ON investigation_history FOR DELETE 
USING (auth.uid() = user_id);