"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";

export default function ReasoningPage() {
  const [runs, setRuns] = useState<any[]>([]);
  const [continuity, setContinuity] = useState<any>(null);

  const fetchData = () => {
    fetch('/api/agent/runs').then(r => r.json()).then(setRuns);
    fetch('/api/continuity?active=true').then(r => r.json()).then(setContinuity);
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agent Reasoning</h1>
          <p className="text-gray-500 text-sm mt-1">Judge Panel — Technical Depth & Transparency</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>Refresh</Button>
      </div>

      {continuity && (
        <Card className="border-indigo-200 shadow-sm bg-indigo-50/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg text-indigo-900">Active Continuity Packet</CardTitle>
            <CardDescription>Post-escalation rules modifying current agent behavior</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside text-sm text-indigo-800 space-y-1">
              {continuity.future_response_rules_json.map((rule: string, i: number) => (
                <li key={i}>{rule}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <h2 className="text-lg font-semibold mt-8 mb-4">Execution Trace</h2>
      <div className="space-y-4">
        {runs.map(run => (
          <Card key={run.id} className="border-gray-200 font-mono text-sm shadow-sm">
            <CardHeader className="py-3 bg-gray-50 border-b border-gray-100 flex flex-row items-center justify-between space-y-0">
              <span className="font-semibold text-gray-700">Turn: {new Date(run.created_at).toLocaleTimeString()}</span>
              <div className="flex gap-2">
                <Badge variant="outline" className="bg-white">{run.phase}</Badge>
                <Badge variant="secondary">{run.mode}</Badge>
              </div>
            </CardHeader>
            <CardContent className="py-3 grid gap-3">
              <div>
                <span className="text-gray-500 font-semibold block mb-1">SELECTED_ACTION:</span>
                <span className="text-indigo-600 font-bold">{run.selected_action}</span>
              </div>
              
              <div>
                <span className="text-gray-500 font-semibold block mb-1">EVIDENCE:</span>
                <ul className="list-disc list-inside text-gray-700 space-y-0.5">
                  {run.evidence_json.map((e: string, i: number) => <li key={i}>{e}</li>)}
                </ul>
              </div>

              {run.response_constraints_json && run.response_constraints_json.length > 0 && (
                <div>
                  <span className="text-gray-500 font-semibold block mb-1">CONSTRAINTS APPLIED:</span>
                  <ul className="list-disc list-inside text-amber-700 space-y-0.5">
                    {run.response_constraints_json.map((c: string, i: number) => <li key={i}>{c}</li>)}
                  </ul>
                </div>
              )}

              <div>
                <span className="text-gray-500 font-semibold block mb-1">SAFETY_STATUS:</span>
                <span className={run.safety_status === 'safe' ? 'text-green-600' : 'text-red-600 font-bold'}>
                  {run.safety_status.toUpperCase()}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
        {runs.length === 0 && <p className="text-gray-500 text-sm">No agent runs recorded yet.</p>}
      </div>
    </div>
  );
}
