import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ErrorState } from "../components/ErrorState";
import { ProductCard } from "../components/ProductCard";
import { Spinner } from "../components/Spinner";
import { scoreAnswers, type Recommendation } from "../lib/api";
import { clearAnswers, loadAnswers } from "../lib/storage";

type Status = "loading" | "ready" | "error" | "empty";

export default function ResultsPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const stored = loadAnswers();
    const answers = Object.entries(stored)
      .filter(([, value]) => value !== null && value !== undefined)
      .map(([qid, value]) => ({ question_id: Number(qid), value }));

    if (answers.length === 0) {
      setStatus("empty");
      return;
    }

    let cancelled = false;
    scoreAnswers(answers)
      .then((data) => {
        if (cancelled) return;
        if (data.recommendations.length === 0) {
          setStatus("empty");
        } else {
          setRecommendations(data.recommendations);
          setStatus("ready");
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Could not score your answers.");
        setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") return <Spinner label="Scoring your answers…" />;
  if (status === "error") return <ErrorState message={error} />;
  if (status === "empty") {
    return (
      <section className="rounded-2xl bg-white p-6 text-center shadow-sm ring-1 ring-bean-100">
        <h1 className="text-xl font-semibold">No answers yet</h1>
        <p className="mt-2 text-sm text-bean-700">Take the quiz to get recommendations.</p>
        <Link
          to="/quiz/1"
          className="mt-4 inline-block rounded-lg bg-bean-700 px-4 py-2 text-sm font-semibold text-white hover:bg-bean-900"
        >
          Start the quiz
        </Link>
      </section>
    );
  }

  return (
    <section>
      <header className="mb-4">
        <h1 className="text-2xl font-semibold">Your top picks</h1>
        <p className="mt-1 text-sm text-bean-700">
          Ranked by how closely each coffee matches your preferences.
        </p>
      </header>
      <div className="space-y-4">
        {recommendations.map((rec, index) => (
          <ProductCard key={rec.product.id} recommendation={rec} rank={index + 1} />
        ))}
      </div>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link
          to="/quiz/1"
          className="rounded-lg px-4 py-2 text-sm font-medium text-bean-700 ring-1 ring-bean-100 hover:bg-bean-50"
        >
          Edit answers
        </Link>
        <button
          type="button"
          onClick={() => {
            clearAnswers();
            window.location.href = "/quiz/1";
          }}
          className="rounded-lg bg-bean-700 px-4 py-2 text-sm font-semibold text-white hover:bg-bean-900"
        >
          Start over
        </button>
      </div>
    </section>
  );
}
