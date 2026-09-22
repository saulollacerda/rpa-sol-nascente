import type { Execucao } from "../api/tipos";
import { dataHora, rotuloDataBase, telefone } from "../dominio/formatacao";
import { SeloStatus } from "./SeloStatus";

interface Props {
  execucoes: Execucao[];
  selecionada?: number;
  onSelecionar: (id: number) => void;
}

export function Historico({ execucoes, selecionada, onSelecionar }: Props) {
  if (execucoes.length === 0) return <p className="vazio">Nenhuma execução ainda.</p>;

  return (
    <div className="tabela-rolavel">
      <table className="historico">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Solicitada em</th>
            <th scope="col">Data-base</th>
            <th scope="col">Praças</th>
            <th scope="col">Destinatário</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          {execucoes.map((e) => (
            <tr key={e.id} aria-selected={e.id === selecionada}>
              <td>
                <button
                  type="button"
                  className="link"
                  aria-label={`Ver execução ${e.id}`}
                  onClick={() => onSelecionar(e.id)}
                >
                  #{e.id}
                </button>
              </td>
              <td>{dataHora(e.criado_em)}</td>
              <td>{rotuloDataBase(e.parametros.data_base)}</td>
              <td>{e.parametros.ufs.join(", ")}</td>
              <td>{telefone(e.destinatario)}</td>
              <td>
                <SeloStatus status={e.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
