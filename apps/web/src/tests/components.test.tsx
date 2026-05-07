import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { ErrorState } from "../components/ErrorState";
import { Layout } from "../components/Layout";
import { Spinner } from "../components/Spinner";

describe("ErrorState", () => {
  it("renders the message and a retry button when onRetry is provided", () => {
    const onRetry = vi.fn();
    render(<ErrorState message="Network is down" onRetry={onRetry} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Network is down")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(onRetry).toHaveBeenCalled();
  });

  it("hides the retry button when onRetry is omitted", () => {
    render(<ErrorState message="Bad seed" />);
    expect(screen.queryByRole("button", { name: /try again/i })).not.toBeInTheDocument();
  });
});

describe("Layout", () => {
  it("renders the header link, the children, and the footer", () => {
    render(
      <MemoryRouter>
        <Layout>
          <p data-testid="content">child content</p>
        </Layout>
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: /coffee quiz/i })).toBeInTheDocument();
    expect(screen.getByTestId("content")).toHaveTextContent("child content");
    expect(screen.getByText(/open source under mit/i)).toBeInTheDocument();
  });
});

describe("Spinner", () => {
  it("renders the default label", () => {
    render(<Spinner />);
    expect(screen.getByRole("status")).toHaveTextContent(/loading/i);
  });

  it("renders a custom label", () => {
    render(<Spinner label="Crunching numbers" />);
    expect(screen.getByText("Crunching numbers")).toBeInTheDocument();
  });
});
