// ============================================================
// Aftermath AI — Real Agent Adapter
// ============================================================
// Bridges the Next.js app with the Python rule-based WellnessAgent.
// Spawns a child process to run agent_bridge.py with DB context.

import { spawn } from 'child_process';
import path from 'path';
import { db } from '../db';
import type { AgentAdapter, AgentContext } from './adapter';
import type {
  AgentTurnRequest, AgentTurnResponse, AgentSignalRequest,
  AgentMode, AgentPhase, SafetyStatus,
} from '../types';

export class RealAgentAdapter implements AgentAdapter {

  async processTurn(request: AgentTurnRequest, context: AgentContext): Promise<AgentTurnResponse> {
    const rawSignal = {
      type: request.input_type === 'chat' ? 'student_chat' : 'journal_entry',
      student_id: request.user_id,
      text: request.content,
      timestamp: new Date().toISOString(),
    };

    const pythonResult = await this.runPythonAgent(request.user_id, rawSignal);
    return this.mapPythonResult(pythonResult);
  }

  async processSignal(request: AgentSignalRequest, context: AgentContext): Promise<AgentTurnResponse> {
    // Map signal type from TS vocabulary to Python vocabulary
    let pythonSignalType: string = request.signal_type;
    if (request.signal_type === 'buddy_concern') {
      pythonSignalType = 'buddy_report';
    } else if (request.signal_type === 'journal') {
      pythonSignalType = 'journal_entry';
    } else if (request.signal_type === 'chat') {
      pythonSignalType = 'student_chat';
    }

    const rawSignal = {
      type: pythonSignalType,
      student_id: request.user_id,
      text: request.content,
      timestamp: new Date().toISOString(),
      payload: request.metadata || {},
    };

    const pythonResult = await this.runPythonAgent(request.user_id, rawSignal);
    return this.mapPythonResult(pythonResult);
  }

  // --- Private: Python Process Spawning ---

  private runPythonAgent(userId: string, rawSignal: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const scriptPath = path.join(process.cwd(), 'wellness_agent', 'agent_bridge.py');
      
      const dbState = {
        exams: db.exams.filter(e => e.user_id === userId),
        care_circle_members: db.care_circle_members.filter(c => c.user_id === userId),
        chat_messages: db.chat_messages.filter(m => m.user_id === userId),
        signals: db.signals.filter(s => s.user_id === userId),
        continuity_packets: db.continuity_packets.filter(c => c.user_id === userId),
      };

      const inputPayload = {
        raw_signal: rawSignal,
        db_state: dbState,
      };

      const py = spawn('python', [scriptPath]);
      
      let stdoutData = '';
      let stderrData = '';
      
      py.stdout.on('data', (data) => {
        stdoutData += data.toString();
      });
      
      py.stderr.on('data', (data) => {
        stderrData += data.toString();
      });
      
      py.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python agent exited with code ${code}. Stderr: ${stderrData}`));
          return;
        }
        try {
          const result = JSON.parse(stdoutData.trim());
          if (result.error) {
            reject(new Error(`Python agent error: ${result.error}`));
          } else {
            resolve(result);
          }
        } catch (err) {
          reject(new Error(`Failed to parse Python agent output: ${stdoutData}. Error: ${err}`));
        }
      });
      
      py.stdin.write(JSON.stringify(inputPayload));
      py.stdin.end();
    });
  }

  // --- Private: Result Mapping ---

  private mapPythonResult(res: any): AgentTurnResponse {
    // 1. Map phase name: e.g. "phase_1_elevated_stress" -> "phase_1"
    const pyPhase = res.support_state?.phase || 'phase_0_stable';
    let phase: AgentPhase = 'phase_0';
    if (pyPhase.includes('phase_1')) phase = 'phase_1';
    else if (pyPhase.includes('phase_2')) phase = 'phase_2';
    else if (pyPhase.includes('phase_3')) phase = 'phase_3';
    else if (pyPhase.includes('phase_4')) phase = 'phase_4';

    // 2. Map mode overlay:
    const pyMode = res.support_state?.mode || 'normal';
    let mode: AgentMode = 'normal';
    if (pyMode === 'protect_next_paper') {
      mode = 'protect_next_paper';
    } else if (pyMode.includes('safety') || pyMode.includes('stabilization') || pyMode.includes('reentry')) {
      mode = 'safety';
    } else if (pyMode.includes('aftermath') || pyMode.includes('post_exam') || pyMode.includes('containment')) {
      mode = 'aftermath';
    }

    // 3. Map safety risk level:
    const pyRisk = res.safety?.risk_level || 'none';
    let safetyStatus: SafetyStatus = 'safe';
    if (pyRisk === 'acute') safetyStatus = 'crisis';
    else if (pyRisk === 'elevated') safetyStatus = 'concern';
    
    // Check if safety override or escalation triggers higher status
    if (res.safety?.override) safetyStatus = 'crisis';
    if (res.escalation?.level === 'urgent') safetyStatus = 'crisis';

    // 4. Suggested buttons based on the current mode and state:
    let suggestedButtons: string[] = [];
    if (mode === 'safety') {
      suggestedButtons = res.safety?.override 
        ? ["I'll call now", "Can you tell someone for me?", "I'm safe, just venting"]
        : ["Yes, let someone know", "I'll reach out myself", "I'm okay, just frustrated"];
    } else if (pyMode === 'aftermath_missing_closure') {
      suggestedButtons = ["It went okay, I guess", "It didn't go well", "I can't talk about it", "I need help"];
    } else if (mode === 'aftermath') {
      suggestedButtons = ["Yeah, I'm safe. Just upset.", "I'm alone right now", "I don't want to talk to anyone", "I need to talk to someone"];
    } else {
      suggestedButtons = ["How should I prepare today?", "I'm feeling stressed", "Tell me about my exams"];
    }

    return {
      assistant_response: res.response || "I am here with you.",
      phase,
      mode,
      safety_status: safetyStatus,
      selected_action: res.next_action || 'DEFAULT_SUPPORTIVE',
      evidence: res.evidence || res.support_state?.evidence || [],
      suggested_buttons: suggestedButtons,
      escalation_created: !!res.escalation?.escalate,
      continuity_updated: !!res.escalation?.escalate || (res.continuity_packet?.do_not_say && res.continuity_packet.do_not_say.length > 0),
    };
  }
}
