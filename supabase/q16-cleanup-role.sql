ALTER TABLE users DROP COLUMN IF EXISTS role;
ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin', 'super_admin'));
UPDATE users SET role = 'super_admin', updated_at = NOW() WHERE email = 'nobita6986@gmail.com';
SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role';
SELECT email, role FROM users WHERE email = 'nobita6986@gmail.com';
