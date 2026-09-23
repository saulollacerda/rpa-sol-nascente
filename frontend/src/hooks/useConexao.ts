import { useCallback, useEffect, useState } from "react";
import { obterConexao, reconectarWhatsApp } from "../api/cliente";
import type { Conexao } from "../api/tipos";
import { vigiarConexao } from "../dominio/conexao";

export function useConexao() {
  const [conexao, setConexao] = useState<Conexao | null>(null);
  const [reconectando, setReconectando] = useState(false);
  // Muda a cada reconexão para reiniciar a vigília e ler o QR code novo na hora.
  const [ciclo, setCiclo] = useState(0);

  useEffect(() => vigiarConexao(obterConexao, setConexao), [ciclo]);

  const reconectar = useCallback(() => {
    setReconectando(true);
    reconectarWhatsApp()
      .catch(() => {})
      .finally(() => {
        setReconectando(false);
        setCiclo((c) => c + 1);
      });
  }, []);

  return { conexao, reconectando, reconectar };
}
