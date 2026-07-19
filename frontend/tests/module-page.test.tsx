import { render, screen } from "@testing-library/react";
import { ModulePage } from "@/components/common/module-page";
describe("placeholder module", () => {
  it("renders planned state", () => {
    render(
      <ModulePage title="Planned capability" capabilities={["Future work"]} />,
    );
    expect(
      screen.getByRole("heading", { name: "Planned capability" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Planned module")).toBeInTheDocument();
  });
});
