import type { Conexao } from "../api/tipos";
import { rotuloConexao } from "../dominio/conexao";

interface Props {
  conexao: Conexao | null;
  reconectando: boolean;
  onReconectar: () => void;
}

export function ConexaoWhatsApp({ conexao, reconectando, onReconectar }: Props) {
  const { rotulo, tom } = conexao
    ? rotuloConexao(conexao.situacao)
    : { rotulo: "Verificando…", tom: "neutro" };

  return (
    <div className="conexao">
      <div className="acompanhamento__topo">
        <h2 id="titulo-whatsapp">WhatsApp</h2>
        <span className={`selo selo--${tom}`} role="status">
          {rotulo}
        </span>
      </div>

      {conexao?.situacao === "CONECTADO" && conexao.conta && (
        <p className="meta">Enviando como {conexao.conta}</p>
      )}

      {conexao?.situacao === "AGUARDANDO_QR" && conexao.qr_code && (
        <>
          <img
            className="conexao__qr"
            src={conexao.qr_code}
            alt="QR code para conectar o WhatsApp"
            width={220}
            height={220}
          />
          <ol className="conexao__passos">
            <li>Abra o WhatsApp no celular que vai enviar os relatórios.</li>
            <li>
              Toque em <strong>Dispositivos conectados</strong> → <strong>Conectar dispositivo</strong>.
            </li>
            <li>Aponte a câmera para o código.</li>
          </ol>
        </>
      )}

      {conexao?.situacao === "INICIANDO" && (
        <p className="meta">Preparando o QR code…</p>
      )}

      {conexao?.situacao === "DESCONECTADO" && (
        <>
          <p className="meta">O QR code venceu ou o celular desconectou.</p>
          <button
            type="button"
            className="botao-secundario"
            onClick={onReconectar}
            disabled={reconectando}
          >
            {reconectando ? "Gerando…" : "Gerar QR code"}
          </button>
        </>
      )}

      {conexao?.situacao === "INDISPONIVEL" && (
        <p className="aviso aviso--erro" role="alert">
          {conexao.mensagem ?? "o serviço de WhatsApp não respondeu"}
        </p>
      )}
    </div>
  );
}
