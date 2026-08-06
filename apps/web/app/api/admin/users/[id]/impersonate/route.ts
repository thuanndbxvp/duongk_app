import { NextRequest } from 'next/server';
import { proxyAdminUserAction } from '../_proxy';

export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  return proxyAdminUserAction(req, ctx.params, 'POST', '/api/admin/users/{id}/impersonate');
}
