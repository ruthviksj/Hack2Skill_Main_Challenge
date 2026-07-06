import { NextResponse } from 'next/server';
import { processAgentSignal } from '@/lib/services/agent-service';
import { DEMO_USER_ID } from '@/lib/db';
import type { AgentSignalRequest } from '@/lib/types';

export async function POST(req: Request) {
  const body = await req.json();
  const request: AgentSignalRequest = {
    user_id: DEMO_USER_ID,
    signal_type: 'buddy_concern',
    content: body.observed_behavior,
    metadata: {
      source_type: 'buddy',
      buddy_id: body.buddy_id,
      urgency: body.urgency,
      safety_status: body.safety_status,
      direct_quote: body.direct_quote,
      observed_or_inferred: body.observed_or_inferred,
      what_tried: body.what_tried,
    },
  };
  
  const response = await processAgentSignal(request);
  return NextResponse.json({
    signal_id: 'sig_' + Date.now(),
    safety_gate_result: response.safety_status,
    escalation_created: response.escalation_created,
    agent_summary: response.assistant_response,
  });
}
