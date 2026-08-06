import { redirectIfAuthenticated } from '@/lib/auth-redirect';
import { LoginForm } from './login-form';

interface PageProps {
  searchParams: Promise<{ next?: string }>;
}

export default async function LoginPage({ searchParams }: PageProps) {
  const { next } = await searchParams;

  // If user is already authenticated, send them somewhere useful
  // instead of showing them the login form again.
  await redirectIfAuthenticated(next);

  return <LoginForm nextPath={next} />;
}