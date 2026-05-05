import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Spinner } from "./components/Spinner";

const QuizPage = lazy(() => import("./pages/QuizPage"));
const ResultsPage = lazy(() => import("./pages/ResultsPage"));
const LandingPage = lazy(() => import("./pages/LandingPage"));

export function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Suspense fallback={<Spinner label="Loading…" />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/quiz" element={<Navigate to="/quiz/1" replace />} />
            <Route path="/quiz/:step" element={<QuizPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </BrowserRouter>
  );
}
