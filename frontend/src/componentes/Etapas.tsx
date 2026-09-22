import type { Status } from "../api/tipos";
import { estadoDasEtapas } from "../dominio/etapas";

const MARCA = { feito: "✓", atual: "", pendente: "", falhou: "✕", interrompido: "–" };

export function Etapas({ status }: { status: Status }) {
  return (
    <ol className="etapas" aria-label="Etapas">
      {estadoDasEtapas(status).map((etapa) => (
        <li key={etapa.rotulo} className={`etapa etapa--${etapa.estado}`} data-estado={etapa.estado}>
          <span className="etapa__marca" aria-hidden="true">
            {MARCA[etapa.estado]}
          </span>
          <span className="etapa__rotulo">{etapa.rotulo}</span>
        </li>
      ))}
    </ol>
  );
}
