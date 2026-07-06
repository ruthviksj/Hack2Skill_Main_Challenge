import { redirect } from "next/navigation";

export default function Home() {
  // Skip the landing page and go straight to the main app.
  redirect("/app");
}
