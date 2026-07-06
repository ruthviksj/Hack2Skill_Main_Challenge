"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, CalendarClock, MessageSquareHeart } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const [exams, setExams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetch('/api/exams').then(r => r.json()).then(data => {
      setExams(data);
      setLoading(false);
    });
  }, []);

  const missingClosure = exams.filter(e => e.status === 'outcome_missing');
  const upcoming = exams.filter(e => e.status === 'upcoming');

  const handleReset = async () => {
    await fetch('/api/demo/reset', { method: 'POST' });
    window.location.reload();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Today</h1>
        <Button variant="outline" size="sm" onClick={handleReset}>Reset Demo</Button>
      </div>

      {loading ? (
        <div className="text-gray-500 text-sm">Loading...</div>
      ) : (
        <>
          {missingClosure.length > 0 && (
            <Alert className="bg-indigo-50 border-indigo-200">
              <AlertCircle className="h-4 w-4 text-indigo-600" />
              <AlertTitle className="text-indigo-900 font-semibold">Unresolved Event</AlertTitle>
              <AlertDescription className="text-indigo-800 mt-1">
                Your {missingClosure[0].name} happened a while ago. We never closed the loop.
                <div className="mt-3">
                  <Button onClick={() => router.push('/companion')} size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
                    Check in with AI
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          )}

          <h2 className="text-lg font-semibold text-gray-800 mt-6 mb-3">Quick Check-in</h2>
          <div className="grid grid-cols-3 gap-2">
            {['Doing great', 'Just okay', 'Struggling'].map((mood) => (
              <Button key={mood} variant="outline" className="h-16 flex flex-col items-center justify-center bg-white hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 transition-all text-gray-600 font-normal">
                {mood}
              </Button>
            ))}
          </div>

          <h2 className="text-lg font-semibold text-gray-800 mt-6 mb-3">Upcoming Milestones</h2>
          {upcoming.length > 0 ? (
            upcoming.map(exam => (
              <Card key={exam.id} className="border-gray-100 shadow-sm">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{exam.name}</CardTitle>
                  <CardDescription>{new Date(exam.exam_date).toLocaleDateString()}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center text-sm text-gray-500">
                    <CalendarClock className="w-4 h-4 mr-2" />
                    Expected Score: {exam.expected_score}
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card className="border-dashed border-gray-200 shadow-none bg-gray-50/50">
              <CardContent className="flex flex-col items-center justify-center py-8 text-center">
                <CalendarClock className="w-8 h-8 text-gray-400 mb-3" />
                <p className="text-sm text-gray-500 max-w-[200px]">Add an upcoming exam so the companion knows what moments matter.</p>
                <Button onClick={() => router.push('/exams')} variant="outline" size="sm" className="mt-4">
                  Add Exam
                </Button>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
