// ============================================================
// Aftermath AI — Mock Agent Adapter
// ============================================================
// Deterministic responses for demo-critical moments.
// Implements AgentAdapter so the real Claude agent can replace it.

import type { AgentAdapter, AgentContext } from './adapter';
import type {
  AgentTurnRequest, AgentTurnResponse, AgentSignalRequest,
  AgentMode, AgentPhase, SafetyStatus,
} from '../types';
import { evaluateSafety } from './safety-gate';

export class MockAgentAdapter implements AgentAdapter {

  async processTurn(request: AgentTurnRequest, context: AgentContext): Promise<AgentTurnResponse> {
    const content = request.content.toLowerCase();

    // 1. Safety check first — always
    const safetyResult = evaluateSafety(request.content);
    if (safetyResult.status === 'crisis' || safetyResult.status === 'urgent') {
      return this.buildSafetyResponse(safetyResult.status, context);
    }

    // 2. If there's missing closure and student is talking about something else → detect it
    if (context.hasMissingClosure && !this.isTalkingAboutExam(content, context)) {
      return this.buildMissingClosureCheckIn(context);
    }

    // 3. If student acknowledges bad outcome → enter Aftermath Mode
    if (this.indicatesBadOutcome(content)) {
      return this.buildAftermathResponse(context);
    }

    // 4. If student says "I can't talk" or similar → respect it
    if (this.indicatesCannotTalk(content)) {
      return this.buildRespectBoundaryResponse(context);
    }

    // 5. If student says "I'm okay" or "fine" → gentle follow-up
    if (this.indicatesOkay(content)) {
      return this.buildGentleFollowup(context);
    }

    // 6. If student asks for help explicitly
    if (this.indicatesNeedHelp(content)) {
      return this.buildHelpResponse(context);
    }

    // 7. Continuity-aware response
    if (context.continuityRules.length > 0) {
      return this.buildContinuityAwareResponse(content, context);
    }

    // 8. Default supportive response
    return this.buildDefaultResponse(content, context);
  }

  async processSignal(request: AgentSignalRequest, context: AgentContext): Promise<AgentTurnResponse> {
    switch (request.signal_type) {
      case 'buddy_concern':
        return this.handleBuddyConcern(request, context);
      case 'missed_followup':
        return this.handleMissedFollowup(request, context);
      case 'safety_concern':
        return this.buildSafetyResponse('urgent', context);
      default:
        return this.buildDefaultSignalResponse(request);
    }
  }

  // --- Private: Response Builders ---

  private buildMissingClosureCheckIn(context: AgentContext): AgentTurnResponse {
    const examName = context.missingClosureExam || 'your recent exam';
    return {
      assistant_response: `Hey, I noticed ${examName} happened a while ago and we never talked about how it went. I'm not going to ask for a score — I just want to check in.\n\nHow are you holding up?`,
      phase: 'phase_2',
      mode: 'aftermath',
      safety_status: 'monitoring',
      selected_action: 'ASK_EVENT_CLOSURE',
      evidence: [
        'High-stakes exam date has passed',
        `Expected score existed (${context.exams.find(e => e.status === 'outcome_missing')?.expected_score || 'set'})`,
        'No outcome update received',
        'Student returned with unrelated query',
        'Missing closure detected',
      ],
      suggested_buttons: [
        "It went okay, I guess",
        "It didn't go well",
        "I can't talk about it",
        "I need help",
      ],
      escalation_created: false,
      continuity_updated: false,
    };
  }

  private buildAftermathResponse(context: AgentContext): AgentTurnResponse {
    return {
      assistant_response: `I hear you. That takes courage to share.\n\nI'm not going to rush into what went wrong or what to do next. Right now, the only thing that matters is that you're processing this.\n\nA bad exam result can feel like the whole world just shifted. That feeling is valid.\n\nBefore anything else — are you doing okay right now? I mean, are you safe and have someone around?`,
      phase: 'phase_2',
      mode: 'aftermath',
      safety_status: 'monitoring',
      selected_action: 'VALIDATE_AND_CHECK_SAFETY',
      evidence: [
        'Student reported bad outcome',
        'Aftermath Mode activated',
        'Emotional validation before action',
        'Safety check embedded naturally',
        'No productivity push',
      ],
      suggested_buttons: [
        "Yeah, I'm safe. Just upset.",
        "I'm alone right now",
        "I don't want to talk to anyone",
        "I need to talk to someone",
      ],
      escalation_created: false,
      continuity_updated: false,
    };
  }

  private buildSafetyResponse(severity: SafetyStatus, context: AgentContext): AgentTurnResponse {
    const isCrisis = severity === 'crisis';
    return {
      assistant_response: isCrisis
        ? `I hear you, and I want you to know that what you're feeling right now matters deeply.\n\nI'm not the right support for this moment — you deserve to talk to someone who can truly be there for you.\n\n📞 **iCall**: 9152987821\n📞 **Vandrevala Foundation**: 1860-2662-345\n📞 **AASRA**: 91-22-27546669\n\nThese are free, confidential, and available now.\n\nYou're not alone in this. Reaching out is the strongest thing you can do.`
        : `I can sense this is really heavy right now. You don't have to explain everything.\n\nWould it help to talk to someone you trust — a friend, family member, or counsellor? Sometimes just having someone near makes a difference.\n\nIf you want, I can let someone in your Care Circle know you could use some support. No details — just a gentle nudge.`,
      phase: 'phase_3',
      mode: 'safety',
      safety_status: severity,
      selected_action: isCrisis ? 'IMMEDIATE_HUMAN_HANDOFF' : 'SUGGEST_HUMAN_CONTACT',
      evidence: [
        `Safety Gate triggered: ${severity}`,
        isCrisis ? 'Crisis-level keywords detected' : 'Urgent-level concern detected',
        'Academic response blocked',
        'Human support recommended',
      ],
      suggested_buttons: isCrisis
        ? ["I'll call now", "Can you tell someone for me?", "I'm safe, just venting"]
        : ["Yes, let someone know", "I'll reach out myself", "I'm okay, just frustrated"],
      escalation_created: true,
      continuity_updated: true,
    };
  }

  private buildRespectBoundaryResponse(context: AgentContext): AgentTurnResponse {
    return {
      assistant_response: `That's completely okay. You don't owe anyone a recap right now.\n\nI'll be here whenever you're ready — no rush, no pressure. We can talk about anything, or nothing at all.\n\nJust know that this space is yours.`,
      phase: 'phase_2',
      mode: 'aftermath',
      safety_status: 'monitoring',
      selected_action: 'RESPECT_BOUNDARY',
      evidence: [
        'Student declined to discuss exam',
        'Boundary respected',
        'Maintaining availability',
        'No forced disclosure',
      ],
      suggested_buttons: [
        "Thanks. Maybe later.",
        "Can we talk about something else?",
        "Actually, I do want to talk",
      ],
      escalation_created: false,
      continuity_updated: false,
    };
  }

  private buildGentleFollowup(context: AgentContext): AgentTurnResponse {
    return {
      assistant_response: `Good to hear. I'll take your word for it.\n\nIf things change or you want to process anything later, I'm right here. No need to wait for a "good reason" to talk.\n\nAnything else on your mind today?`,
      phase: 'phase_1',
      mode: 'normal',
      safety_status: 'safe',
      selected_action: 'ACKNOWLEDGE_AND_CONTINUE',
      evidence: [
        'Student indicated they are okay',
        'Accepted without pushing',
        'Left door open for future',
      ],
      suggested_buttons: [
        "Tell me about my upcoming exams",
        "I want to study smart today",
        "Actually, I'm not really okay",
      ],
      escalation_created: false,
      continuity_updated: false,
    };
  }

  private buildHelpResponse(context: AgentContext): AgentTurnResponse {
    return {
      assistant_response: `I'm here. Let's take this one step at a time.\n\nYou don't need to have it all figured out. What feels like the most important thing right now?\n\nWe can talk through feelings, look at what's next, or I can help you connect with someone in your support circle.`,
      phase: 'phase_2',
      mode: 'aftermath',
      safety_status: 'concern',
      selected_action: 'OFFER_STRUCTURED_SUPPORT',
      evidence: [
        'Student explicitly asked for help',
        'Offering structured support options',
        'Not assuming the type of help needed',
      ],
      suggested_buttons: [
        "I just need to vent",
        "Help me think about next steps",
        "I want to talk to someone real",
        "What's my next exam?",
      ],
      escalation_created: false,
      continuity_updated: false,
    };
  }

  private buildContinuityAwareResponse(content: string, context: AgentContext): AgentTurnResponse {
    return {
      assistant_response: `Welcome back. I remember where we left off, and I want you to know there's no pressure here.\n\nHow are you feeling today? We can pick up from wherever you want, or start fresh.`,
      phase: 'phase_4',
      mode: 'normal',
      safety_status: 'monitoring',
      selected_action: 'CONTINUITY_AWARE_GREETING',
      evidence: [
        'Active continuity packet found',
        'Applying future response rules',
        ...context.continuityRules.map(r => `Rule: ${r}`),
      ],
      suggested_buttons: [
        "I'm doing better",
        "Still processing",
        "Let's focus on something new",
        "I need support",
      ],
      escalation_created: false,
      continuity_updated: false,
    };
  }

  private buildDefaultResponse(content: string, context: AgentContext): AgentTurnResponse {
    return {
      assistant_response: `I'm here and listening. Feel free to share what's on your mind — whether it's about exams, studying, or anything else.\n\nThis is your space.`,
      phase: 'phase_0',
      mode: 'normal',
      safety_status: 'safe',
      selected_action: 'DEFAULT_SUPPORTIVE',
      evidence: [
        'No specific trigger detected',
        'Default supportive response',
      ],
      suggested_buttons: [
        "How should I prepare today?",
        "I'm feeling stressed",
        "Tell me about my exams",
      ],
      escalation_created: false,
      continuity_updated: false,
    };
  }

  private handleBuddyConcern(request: AgentSignalRequest, context: AgentContext): AgentTurnResponse {
    const metadata = request.metadata || {};
    const safetyResult = evaluateSafety(
      request.content,
      metadata.urgency as 'low' | 'medium' | 'high' | 'critical',
      metadata.safety_status as SafetyStatus,
    );

    const isEscalation = safetyResult.should_create_escalation;

    return {
      assistant_response: isEscalation
        ? `A trusted person in your Care Circle has shared something they noticed. This isn't surveillance — it's someone who cares.\n\nI'm going to be extra gentle in our conversations. If you want to talk about anything, I'm here. No judgement, no pressure.`
        : `Someone in your support circle checked in about you. They care, and so do I.\n\nNothing has changed about our conversations — I just wanted you to know people are rooting for you.`,
      phase: 'phase_2',
      mode: isEscalation ? 'safety' : 'aftermath',
      safety_status: safetyResult.status,
      selected_action: isEscalation ? 'ESCALATION_FROM_BUDDY' : 'BUDDY_SIGNAL_NOTED',
      evidence: [
        'Buddy concern received',
        `Reported urgency: ${metadata.urgency || 'unknown'}`,
        `Safety gate result: ${safetyResult.status}`,
        `Triggered: ${safetyResult.triggered_keywords.join(', ') || 'none'}`,
        isEscalation ? 'Escalation created' : 'Signal noted, no escalation',
      ],
      suggested_buttons: [],
      escalation_created: isEscalation,
      continuity_updated: isEscalation,
    };
  }

  private handleMissedFollowup(request: AgentSignalRequest, context: AgentContext): AgentTurnResponse {
    return {
      assistant_response: '',  // Internal signal, no direct response to student
      phase: 'phase_1',
      mode: 'aftermath',
      safety_status: 'monitoring',
      selected_action: 'DETECT_MISSING_CLOSURE',
      evidence: [
        'System detected missed followup',
        request.content,
      ],
      suggested_buttons: [],
      escalation_created: false,
      continuity_updated: false,
    };
  }

  private buildDefaultSignalResponse(request: AgentSignalRequest): AgentTurnResponse {
    return {
      assistant_response: '',
      phase: 'phase_0',
      mode: 'normal',
      safety_status: 'safe',
      selected_action: 'SIGNAL_LOGGED',
      evidence: [`Signal type: ${request.signal_type}`, 'Logged for context'],
      suggested_buttons: [],
      escalation_created: false,
      continuity_updated: false,
    };
  }

  // --- Private: Content Analysis Helpers ---

  private isTalkingAboutExam(content: string, context: AgentContext): boolean {
    const examKeywords = ['exam', 'test', 'score', 'result', 'marks', 'grade', 'gmat', 'mock'];
    if (context.missingClosureExam) {
      examKeywords.push(...context.missingClosureExam.toLowerCase().split(' '));
    }
    return examKeywords.some(kw => content.includes(kw));
  }

  private indicatesBadOutcome(content: string): boolean {
    const badPhrases = [
      "didn't go well", "went badly", "went bad", "failed", "bombed",
      "messed up", "screwed up", "terrible", "horrible", "disaster",
      "awful", "worst", "very bad", "not good", "below", "didn't pass",
      "didn't make it", "way below", "much lower", "couldn't do it",
      "blanked out", "froze", "panicked", "couldn't answer",
    ];
    return badPhrases.some(phrase => content.includes(phrase));
  }

  private indicatesCannotTalk(content: string): boolean {
    const phrases = [
      "can't talk", "don't want to talk", "not now", "leave me alone",
      "can't discuss", "not ready", "later", "don't ask",
    ];
    return phrases.some(phrase => content.includes(phrase));
  }

  private indicatesOkay(content: string): boolean {
    const phrases = [
      "i'm okay", "i'm fine", "i'm good", "all good", "it's fine",
      "no worries", "i'm alright", "went okay", "it went ok",
    ];
    return phrases.some(phrase => content.includes(phrase));
  }

  private indicatesNeedHelp(content: string): boolean {
    const phrases = [
      "need help", "help me", "i need", "can you help", "support",
      "struggling", "don't know what to do", "lost",
    ];
    return phrases.some(phrase => content.includes(phrase));
  }
}
