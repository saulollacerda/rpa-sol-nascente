import type { Concorrente, DadosEncontrados as Dados } from "../api/tipos";
import { inteiro, nomeUf, percentual, rotuloDataBase } from "../dominio/formatacao";

function Metrica({ rotulo, valor, detalhe }: { rotulo: string; valor: string; detalhe?: string }) {
  return (
    <div className="metrica">
      <span className="metrica__rotulo">{rotulo}</span>
      <strong className="metrica__valor">{valor}</strong>
      {detalhe && <span className="metrica__detalhe">{detalhe}</span>}
    </div>
  );
}

function Concorrencia({ concorrentes }: { concorrentes: Concorrente[] }) {
  if (concorrentes.length === 0) return null;
  return (
    <ul className="concorrencia" aria-label="Concorrência">
      {concorrentes.map((c) => (
        <li key={c.cnpj_raiz}>
          <span>{c.nome_administradora}</span>
          <span>{percentual(c.share)}</span>
        </li>
      ))}
    </ul>
  );
}

export function DadosEncontrados({ dados }: { dados: Dados }) {
  const { pracas, nacional, ufs_sem_resultado, recorte_uf_indisponivel } = dados.relatorio;

  return (
    <div className="dados">
      <h3>Dados encontrados</h3>

      {pracas.length > 0 && dados.data_base_uf && (
        <p className="meta">Praças · data-base {rotuloDataBase(dados.data_base_uf)}</p>
      )}
      {recorte_uf_indisponivel && (
        <p className="aviso aviso--neutro">Não há recorte por UF publicado até esta data-base.</p>
      )}
      {ufs_sem_resultado.length > 0 && (
        <p className="aviso aviso--neutro">
          Sem atuação neste segmento em: {ufs_sem_resultado.map(nomeUf).join(", ")}
        </p>
      )}

      <div className="cartoes">
        {pracas.map((p) => (
          <section key={p.uf} className="cartao-praca" aria-label={nomeUf(p.uf)}>
            <header>
              <h4>{nomeUf(p.uf)}</h4>
              <span className="meta">{p.administradoras_na_praca} administradoras</span>
            </header>
            <div className="metricas">
              <Metrica rotulo="Participação" valor={percentual(p.share)} />
              <Metrica rotulo="Ativos" valor={inteiro(p.ativos)} detalhe={`de ${inteiro(p.ativos_praca)}`} />
              <Metrica rotulo="Adesões no trimestre" valor={inteiro(p.adesoes_no_trimestre)} />
              <Metrica
                rotulo="Contemplados"
                valor={inteiro(p.contemplados_lance_no_trimestre + p.contemplados_sorteio_no_trimestre)}
                detalhe={`${inteiro(p.contemplados_lance_no_trimestre)} lance · ${inteiro(p.contemplados_sorteio_no_trimestre)} sorteio`}
              />
            </div>
            <Concorrencia concorrentes={p.concorrentes} />
          </section>
        ))}

        {nacional && (
          <section className="cartao-praca cartao-praca--nacional" aria-label="Brasil">
            <header>
              <h4>Brasil</h4>
              <span className="meta">data-base {rotuloDataBase(nacional.data_base)}</span>
            </header>
            <div className="metricas">
              <Metrica rotulo="Participação" valor={percentual(nacional.share)} />
              <Metrica
                rotulo="Cotas ativas"
                valor={inteiro(nacional.cotas_ativas)}
                detalhe={`de ${inteiro(nacional.cotas_ativas_mercado)}`}
              />
              <Metrica rotulo="Taxa de administração" valor={percentual(nacional.taxa_administracao)} />
              <Metrica rotulo="Grupos ativos" valor={inteiro(nacional.grupos_ativos)} />
            </div>
            <Concorrencia concorrentes={nacional.concorrentes} />
          </section>
        )}
      </div>
    </div>
  );
}
