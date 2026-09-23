import { useState } from "react";

const NOME = "Sol Nascente Motos";

// Drop the file in frontend/public/logo.png; until then the slot keeps its size.
export function Logo() {
  const [semArquivo, setSemArquivo] = useState(false);

  if (semArquivo) return <span className="logo logo--vazio">{NOME}</span>;
  return <img className="logo" src="/logo.png" alt={NOME} onError={() => setSemArquivo(true)} />;
}
