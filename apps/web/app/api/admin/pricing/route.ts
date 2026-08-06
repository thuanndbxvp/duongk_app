import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export async function GET(req: NextRequest) {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    const authHeader = req.headers.get('authorization');

    if (!supabaseUrl || !supabaseServiceKey) {
        return NextResponse.json({ error: 'Server config error' }, { status: 500 });
    }

    if (!authHeader) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
        global: { headers: { Authorization: authHeader } },
    });

    try {
        const result = await supabase
            .from('credit_pricing')
            .select('*')
            .order('job_type', { ascending: true });

        if (result.error) {
            return NextResponse.json({ error: result.error.message }, { status: 400 });
        }

        return NextResponse.json(result.data || []);
    } catch {
        return NextResponse.json({ error: 'Internal error' }, { status: 500 });
    }
}
