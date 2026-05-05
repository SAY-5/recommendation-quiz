import { Link, useNavigate } from "react-router-dom";
import { clearAnswers } from "../lib/storage";

export default function LandingPage() {
  const navigate = useNavigate();

  function start(): void {
    clearAnswers();
    navigate("/quiz/1");
  }

  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-bean-100 sm:p-10">
      <h1 className="text-2xl font-semibold sm:text-3xl">Find your next coffee.</h1>
      <p className="mt-3 text-sm text-bean-700 sm:text-base">
        Twelve quick questions about how you brew, what you taste, and how strong you like it. We
        score 30 single-origins and blends and return the top three matches with reasons.
      </p>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={start}
          className="rounded-lg bg-bean-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-bean-900"
        >
          Start the quiz
        </button>
        <Link
          to="/quiz/1"
          className="text-sm font-medium text-bean-700 underline-offset-4 hover:underline"
        >
          Resume in progress
        </Link>
      </div>
    </section>
  );
}
