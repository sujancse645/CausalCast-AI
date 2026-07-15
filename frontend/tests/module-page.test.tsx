import { render, screen } from "@testing-library/react";
import ForecastsPage from "@/app/forecasts/page";
describe("placeholder module", () => {
  it("renders planned state", () => {
    render(<ForecastsPage />);
    expect(
      screen.getByRole("heading", { name: "Revenue Forecasts" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Planned module")).toBeInTheDocument();
  });
});
