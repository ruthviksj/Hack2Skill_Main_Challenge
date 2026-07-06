"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function CareCirclePage() {
  const [members, setMembers] = useState<any[]>([]);
  const [escalations, setEscalations] = useState<any[]>([]);
  const [concern, setConcern] = useState("");
  const [urgency, setUrgency] = useState("medium");
  const [selectedBuddy, setSelectedBuddy] = useState<string | null>(null);

  const fetchData = () => {
    fetch('/api/care-circle').then(r => r.json()).then(setMembers);
    fetch('/api/escalations').then(r => r.json()).then(setEscalations);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const submitConcern = async () => {
    if (!concern || !selectedBuddy) return;
    await fetch('/api/buddy/concern', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        buddy_id: selectedBuddy,
        observed_behavior: concern,
        urgency,
      })
    });
    setConcern("");
    setSelectedBuddy(null);
    fetchData();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-10">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Care Circle</h1>
        <p className="text-gray-500 text-sm mt-1">Trusted people who can help the system notice when you need support.</p>
      </div>

      <div className="grid gap-4">
        {members.map(member => (
          <Card key={member.id} className="border-gray-100 shadow-sm">
            <CardContent className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-xl">
                  {member.avatar_emoji}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 leading-none mb-1">{member.name}</h3>
                  <p className="text-sm text-gray-500">{member.relationship}</p>
                </div>
              </div>
              
              {member.role === 'buddy' && (
                <Dialog open={selectedBuddy === member.id} onOpenChange={(open) => !open && setSelectedBuddy(null)}>
                  {/* @ts-ignore */}
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" onClick={() => setSelectedBuddy(member.id)} className="text-xs">
                      Simulate Concern
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                      <DialogTitle>Submit Concern (As Buddy)</DialogTitle>
                      <DialogDescription>
                        This simulates a buddy submitting a concern about the student.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                      <div className="grid gap-2">
                        <Label>What did you notice?</Label>
                        <Textarea 
                          placeholder="e.g. He said everything is useless now." 
                          value={concern}
                          onChange={e => setConcern(e.target.value)}
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>Urgency</Label>
                        <div className="flex gap-2">
                          {['medium', 'high', 'critical'].map(u => (
                            <Button 
                              key={u} 
                              variant={urgency === u ? 'default' : 'outline'} 
                              size="sm"
                              className={urgency === u ? 'bg-indigo-600' : ''}
                              onClick={() => setUrgency(u)}
                            >
                              {u}
                            </Button>
                          ))}
                        </div>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button onClick={submitConcern} disabled={!concern}>Submit Signal</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {escalations.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Support History</h2>
          <div className="space-y-4">
            {escalations.map(esc => (
              <Card key={esc.id} className="border-red-100 bg-red-50/30">
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-base text-red-900">Safety Escalation</CardTitle>
                    <Badge variant="outline" className="bg-red-100 text-red-800 border-red-200">
                      {esc.severity}
                    </Badge>
                  </div>
                  <CardDescription className="text-red-700/80">
                    {new Date(esc.created_at).toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-800">{esc.summary}</p>
                  <p className="text-sm font-medium mt-2 text-red-800">Action: {esc.recommended_action}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
