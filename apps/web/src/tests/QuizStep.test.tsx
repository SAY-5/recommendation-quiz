import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { QuizStep } from "../components/QuizStep";
import type { AnswerValue, Question } from "../lib/api";

const SINGLE: Question = {
  id: 1,
  slug: "roast_preference",
  prompt: "Which roast?",
  order: 1,
  kind: "single",
  options: [
    { value: "light", label: "Light", order: 1 },
    { value: "medium", label: "Medium", order: 2 },
    { value: "dark", label: "Dark", order: 3 },
  ],
};

const MULTI: Question = {
  id: 2,
  slug: "flavor_profile",
  prompt: "Which flavors?",
  order: 2,
  kind: "multi",
  options: [
    { value: "fruity", label: "Fruity", order: 1 },
    { value: "nutty", label: "Nutty", order: 2 },
  ],
};

describe("QuizStep", () => {
  it("renders prompt and options", () => {
    render(
      <QuizStep
        question={SINGLE}
        value={null}
        onChange={() => {}}
        onBack={null}
        onNext={() => {}}
        isLast={false}
        stepNumber={1}
        totalSteps={3}
      />,
    );
    expect(screen.getByText("Which roast?")).toBeInTheDocument();
    expect(screen.getByLabelText("Light")).toBeInTheDocument();
    expect(screen.getByLabelText("Medium")).toBeInTheDocument();
  });

  it("disables Next until a single-choice value is selected", () => {
    const onNext = vi.fn();
    render(
      <QuizStep
        question={SINGLE}
        value={null}
        onChange={() => {}}
        onBack={null}
        onNext={onNext}
        isLast={false}
        stepNumber={1}
        totalSteps={3}
      />,
    );
    const next = screen.getByRole("button", { name: /next/i });
    expect(next).toBeDisabled();
  });

  it("calls onChange with the selected value (single)", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <QuizStep
        question={SINGLE}
        value={null}
        onChange={onChange}
        onBack={null}
        onNext={() => {}}
        isLast={false}
        stepNumber={1}
        totalSteps={3}
      />,
    );
    await user.click(screen.getByLabelText("Light"));
    expect(onChange).toHaveBeenCalledWith("light");
  });

  it("supports multi-select toggling", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <QuizStep
        question={MULTI}
        value={[]}
        onChange={onChange}
        onBack={null}
        onNext={() => {}}
        isLast={false}
        stepNumber={1}
        totalSteps={2}
      />,
    );
    fireEvent.click(screen.getByLabelText("Fruity"));
    expect(onChange).toHaveBeenLastCalledWith(["fruity"]);

    rerender(
      <QuizStep
        question={MULTI}
        value={["fruity"]}
        onChange={onChange}
        onBack={null}
        onNext={() => {}}
        isLast={false}
        stepNumber={1}
        totalSteps={2}
      />,
    );
    fireEvent.click(screen.getByLabelText("Nutty"));
    expect(onChange).toHaveBeenLastCalledWith(["fruity", "nutty"]);

    fireEvent.click(screen.getByLabelText("Fruity"));
    expect(onChange).toHaveBeenLastCalledWith([]);
  });

  it("shows See recommendations on the last step", () => {
    render(
      <QuizStep
        question={SINGLE}
        value="medium"
        onChange={() => {}}
        onBack={() => {}}
        onNext={() => {}}
        isLast={true}
        stepNumber={3}
        totalSteps={3}
      />,
    );
    expect(screen.getByRole("button", { name: /see recommendations/i })).toBeEnabled();
  });

  it("renders Back when onBack is provided", () => {
    const onBack = vi.fn();
    render(
      <QuizStep
        question={SINGLE}
        value="light"
        onChange={() => {}}
        onBack={onBack}
        onNext={() => {}}
        isLast={false}
        stepNumber={2}
        totalSteps={3}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /back/i }));
    expect(onBack).toHaveBeenCalled();
  });

  it("renders all options for a single-choice question", () => {
    render(
      <QuizStep
        question={SINGLE}
        value={null}
        onChange={() => {}}
        onBack={null}
        onNext={() => {}}
        isLast={false}
        stepNumber={1}
        totalSteps={3}
      />,
    );
    for (const option of SINGLE.options) {
      expect(screen.getByLabelText(option.label)).toBeInTheDocument();
    }
  });

  it("validates: Next is disabled until at least one multi-choice option is selected", () => {
    const { rerender } = render(
      <QuizStep
        question={MULTI}
        value={[]}
        onChange={() => {}}
        onBack={null}
        onNext={() => {}}
        isLast={false}
        stepNumber={1}
        totalSteps={2}
      />,
    );
    expect(screen.getByRole("button", { name: /next/i })).toBeDisabled();
    rerender(
      <QuizStep
        question={MULTI}
        value={["fruity"]}
        onChange={() => {}}
        onBack={null}
        onNext={() => {}}
        isLast={false}
        stepNumber={1}
        totalSteps={2}
      />,
    );
    expect(screen.getByRole("button", { name: /next/i })).toBeEnabled();
  });

  it("advances on submit when Next is clicked with a valid selection", async () => {
    const user = userEvent.setup();
    const onNext = vi.fn();
    render(
      <QuizStep
        question={SINGLE}
        value="medium"
        onChange={() => {}}
        onBack={null}
        onNext={onNext}
        isLast={false}
        stepNumber={1}
        totalSteps={3}
      />,
    );
    await user.click(screen.getByRole("button", { name: /next/i }));
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it("preserves the previously chosen answer when navigating back to a step", () => {
    // Simulate the parent holding answer state; the user advances, comes back,
    // and the previously selected option is still rendered as checked.
    function Harness() {
      const [value, setValue] = useState<AnswerValue>("medium");
      return (
        <QuizStep
          question={SINGLE}
          value={value}
          onChange={(next) => setValue(next)}
          onBack={() => setValue(value)}
          onNext={() => {}}
          isLast={false}
          stepNumber={2}
          totalSteps={3}
        />
      );
    }
    render(<Harness />);
    const mediumRadio = screen.getByLabelText("Medium") as HTMLInputElement;
    expect(mediumRadio.checked).toBe(true);
    // Click Back; state on this step is unchanged.
    fireEvent.click(screen.getByRole("button", { name: /back/i }));
    expect((screen.getByLabelText("Medium") as HTMLInputElement).checked).toBe(true);
  });
});
