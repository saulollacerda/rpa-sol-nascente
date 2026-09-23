import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Logo } from "./Logo";

describe("logo", () => {
  it("mostra a imagem de public/logo.png", () => {
    render(<Logo />);
    expect(screen.getByRole("img", { name: "Sol Nascente Motos" })).toHaveAttribute(
      "src",
      "/logo.png",
    );
  });

  it("sem o arquivo, reserva o espaço com o nome da loja", () => {
    render(<Logo />);
    fireEvent.error(screen.getByRole("img"));
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText("Sol Nascente Motos")).toBeInTheDocument();
  });
});
