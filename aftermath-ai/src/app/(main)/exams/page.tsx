"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";

export default function ExamsPage() {
  const [exams, setExams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchExams = () => {
    fetch('/api/exams').then(r => r.json()).then(data => {
      setExams(data);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchExams();
  }, []);

  const simulatePassed = async (id: string) => {
    await fetch(`/api/exams/${id}/simulate-passed`, { method: 'POST' });
    fetchExams();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Exams</h1>
        <Button size="sm">Add Exam</Button>
      </div>

      <div className="space-y-4">
        {loading ? <p className="text-sm text-gray-500">Loading...</p> : exams.map(exam => (
          <Card key={exam.id} className="border-gray-100 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500" />
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{exam.name}</CardTitle>
                  <CardDescription>{format(new Date(exam.exam_date), "MMM d, yyyy")}</CardDescription>
                </div>
                <Badge variant={exam.status === 'outcome_missing' ? 'destructive' : 'secondary'} className="capitalize">
                  {exam.status.replace('_', ' ')}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-gray-600 mb-4">
                <span className="font-medium text-gray-900">Target:</span> {exam.expected_score}
              </div>
              
              {exam.status === 'upcoming' && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border-indigo-200"
                  onClick={() => simulatePassed(exam.id)}
                >
                  [Demo] Simulate Exam Passed
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
