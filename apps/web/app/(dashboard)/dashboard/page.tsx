import { redirect } from 'next/navigation'
import { getUser } from '@/lib/auth'

export default async function DashboardPage() {
  const user = await getUser()

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow p-6">
        <h1 className="text-3xl font-bold mb-4 text-gray-900">Dashboard</h1>
        <p className="mb-6 text-gray-700">Welcome back, {user.email}!</p>
        <form action="/api/auth/logout" method="POST">
          <button type="submit" className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
            Sign Out
          </button>
        </form>
      </div>
    </div>
  )
}
