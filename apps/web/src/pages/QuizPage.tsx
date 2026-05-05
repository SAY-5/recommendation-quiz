import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ErrorState } from "../components/ErrorState";
import { QuizStep } from "../components/QuizStep";
import { Spinner } from "../components/Spinner";
import { fetchQuestions, type Question } from "../lib/api";
import { loadAnswers, saveAnswers, type AnswersMap } from "../lib/storage";

export default function QuizPage() {
  const { step } = useParams<{ step: string }>();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<AnswersMap>(() => loadAnswers());
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState<string>("");

  const stepIndex = useMemo(() => {
    const parsed = Number.parseInt(step ?? "1", 10);
    if (Number.isNaN(parsed) || parsed < 1) return 0;
    return parsed - 1;
  }, [step]);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    fetchQuestions()
      .then((data) => {
        if (cancelled) return;
        setQuestions(data);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Could not load questions.");
        setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    saveAnswers(answers);
  }, [answers]);

  if (status === "loading") {
    return <Spinner label="Loading quiz…" />;
  }

  if (status === "error") {
    return (
      <ErrorState
        message={error}
        onRetry={() => {
          setStatus("loading");
          fetchQuestions()
            .then((data) => {
              setQuestions(data);
              setStatus("ready");
            })
            .catch((err: unknown) => {
              setError(err instanceof Error ? err.message : "Could not load questions.");
              setStatus("error");
            });
        }}
      />
    );
  }

  if (questions.length === 0) {
    return (
      <ErrorState message="The quiz has no questions yet. Please run the seed command on the API." />
    );
  }

  const safeStepIndex = Math.min(Math.max(stepIndex, 0), questions.length - 1);
  const question = questions[safeStepIndex];
  if (!question) {
    return <ErrorState message="Step not found." />;
  }
  const isLast = safeStepIndex === questions.length - 1;

  return (
    <QuizStep
      question={question}
      value={answers[question.id] ?? null}
      onChange={(next) => setAnswers((prev) => ({ ...prev, [question.id]: next }))}
      onBack={safeStepIndex > 0 ? () => navigate(`/quiz/${safeStepIndex}`) : null}
      onNext={() => {
        if (isLast) {
          navigate("/results");
        } else {
          navigate(`/quiz/${safeStepIndex + 2}`);
        }
      }}
      isLast={isLast}
      stepNumber={safeStepIndex + 1}
      totalSteps={questions.length}
    />
  );
}
