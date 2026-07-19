import { AiAssistant } from "@/components/rag/ai-assistant";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ streamRagChat: vi.fn() }));

vi.mock("@/lib/api", () => ({
  streamRagChat: mocks.streamRagChat,
}));

describe("AI Assistant", () => {
  beforeEach(() => {
    mocks.streamRagChat.mockReset();
  });

  it("streams a grounded answer, renders citations, and clears history", async () => {
    mocks.streamRagChat.mockImplementation(async (_request, receive) => {
      receive({ type: "token", content: "The API " });
      receive({ type: "token", content: "uses FastAPI." });
      receive({ type: "sources", sources: ["docs/API.md"] });
      receive({ type: "done" });
    });
    const user = userEvent.setup();
    render(<AiAssistant />);

    await user.type(
      screen.getByLabelText("Ask a question about the project"),
      "What API is used?",
    );
    await user.click(screen.getByRole("button", { name: "Ask" }));

    expect(
      await screen.findByText("The API uses FastAPI."),
    ).toBeInTheDocument();
    expect(screen.getByText("docs/API.md")).toBeInTheDocument();
    expect(mocks.streamRagChat).toHaveBeenCalledWith(
      { question: "What API is used?" },
      expect.any(Function),
    );

    await user.click(screen.getByRole("button", { name: "Clear chat" }));
    expect(screen.getByText("Ask about CausalCast AI")).toBeInTheDocument();
  });

  it("submits with Enter and displays service errors", async () => {
    mocks.streamRagChat.mockRejectedValue(
      new Error("Document index is unavailable"),
    );
    render(<AiAssistant />);
    const input = screen.getByLabelText("Ask a question about the project");

    fireEvent.change(input, { target: { value: "Explain Tourism metrics" } });
    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Document index is unavailable",
      ),
    );
  });
});
