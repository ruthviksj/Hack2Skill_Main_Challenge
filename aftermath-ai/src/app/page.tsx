import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#fafaf9] text-center p-6">
      <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl mb-6">
        Aftermath AI
      </h1>
      <p className="text-xl text-gray-600 mb-8 max-w-2xl">
        An exam-aware wellness companion that notices when important academic moments go unresolved.
      </p>
      
      <div className="flex flex-col sm:flex-row gap-4">
        <Link href="/app" className="inline-flex h-11 items-center justify-center rounded-md bg-indigo-600 px-8 text-sm font-medium text-white transition-colors hover:bg-indigo-700">
          Start Demo
        </Link>
      </div>

      <div className="mt-16 max-w-3xl text-left bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold mb-2">Hackathon Demo Flow:</h3>
        <ol className="list-decimal list-inside space-y-2 text-gray-600">
          <li>System detects a high-stakes exam has passed without the student reporting the outcome.</li>
          <li>Student sends an unrelated message to the AI.</li>
          <li>AI detects the "missing closure" and gently checks in without asking for the score.</li>
          <li>Student reports a bad outcome; AI enters Aftermath Mode.</li>
          <li>A study buddy submits a concern regarding the student.</li>
          <li>System triggers an escalation and generates a Continuity Packet for future conversations.</li>
        </ol>
      </div>
    </div>
  );
}
