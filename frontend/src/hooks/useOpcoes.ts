import { useCallback, useEffect, useState } from "react";
import { ErroApi, obterOpcoes } from "../api/cliente";
import type { Opcoes } from "../api/tipos";

export function useOpcoes() {
  const [opcoes, setOpcoes] = useState<Opcoes | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  const carregar = useCallback(() => {
    setCarregando(true);
    setErro(null);
    obterOpcoes()
      .then(setOpcoes)
      .catch((e: unknown) => setErro(e instanceof ErroApi ? e.message : "falha inesperada"))
      .finally(() => setCarregando(false));
  }, []);

  useEffect(carregar, [carregar]);

  return { opcoes, erro, carregando, recarregar: carregar };
}
