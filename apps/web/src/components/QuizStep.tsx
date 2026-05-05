import { useMemo } from "react";
import type { AnswerValue, Question } from "../lib/api";

interface QuizStepProps {
  question: Question;
  value: AnswerValue;
  onChange: (next: AnswerValue) => void;
  onBack: (() => void) | null;
  onNext: () => void;
  isLast: boolean;
  stepNumber: number;
  totalSteps: number;
}

export function QuizStep({
  question,
  value,
  onChange,
  onBack,
  onNext,
  isLast,
  stepNumber,
  totalSteps,
}: QuizStepProps) {
  const isMulti = question.kind === "multi";
  const selected = useMemo(() => normaliseSelection(value, isMulti), [value, isMulti]);
  const canAdvance = isMulti ? selected.length > 0 : selected.length === 1;

  function toggle(optionValue: string): void {
    if (isMulti) {
      const next = selected.includes(optionValue)
        ? selected.filter((v) => v !== optionValue)
        : [...selected, optionValue];
      onChange(next);
    } else {
      onChange(optionValue);
    }
  }

  return (
    <section
      aria-labelledby={`q-${question.id}`}
      className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-bean-100 sm:p-8"
    >
      <p className="text-xs uppercase tracking-wider text-bean-500">
        Question {stepNumber} of {totalSteps}
      </p>
      <h1 id={`q-${question.id}`} className="mt-1 text-xl font-semibold sm:text-2xl">
        {question.prompt}
      </h1>

      <ul className="mt-6 grid gap-2 sm:grid-cols-2">
        {question.options.map((option) => {
          const checked = selected.includes(option.value);
          return (
            <li key={option.value}>
              <label
                className={[
                  "flex cursor-pointer items-center gap-3 rounded-xl border p-3 text-sm transition",
                  checked
                    ? "border-bean-700 bg-bean-100 ring-2 ring-bean-700"
                    : "border-bean-100 bg-bean-50 hover:border-bean-500",
                ].join(" ")}
              >
                <input
                  type={isMulti ? "checkbox" : "radio"}
                  name={`question-${question.id}`}
                  value={option.value}
                  checked={checked}
                  onChange={() => toggle(option.value)}
                  className="h-4 w-4 accent-bean-700"
                />
                <span className="font-medium">{option.label}</span>
              </label>
            </li>
          );
        })}
      </ul>

      <div className="mt-8 flex items-center justify-between gap-3">
        {onBack ? (
          <button
            type="button"
            onClick={onBack}
            className="rounded-lg px-4 py-2 text-sm font-medium text-bean-700 ring-1 ring-bean-100 hover:bg-bean-50"
          >
            Back
          </button>
        ) : (
          <span />
        )}
        <button
          type="button"
          onClick={onNext}
          disabled={!canAdvance}
          className="rounded-lg bg-bean-700 px-5 py-2 text-sm font-semibold text-white shadow-sm transition enabled:hover:bg-bean-900 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLast ? "See recommendations" : "Next"}
        </button>
      </div>
    </section>
  );
}

function normaliseSelection(value: AnswerValue, isMulti: boolean): string[] {
  if (value === null || value === undefined) return [];
  if (Array.isArray(value)) return value.map(String);
  if (isMulti) return [String(value)];
  return [String(value)];
}
