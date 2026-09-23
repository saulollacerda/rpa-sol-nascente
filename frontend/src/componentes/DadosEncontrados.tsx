import type { DadosEncontrados as Dados, PerfilAdministradora, Relatorio } from "../api/tipos";
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

const seta = (antes: number, depois: number) => `${percentual(antes)} → ${percentual(depois)}`;
const razao = (parte: number, total: number) => (total ? (parte / total) * 100 : 0);

function ehRelatorioAtual(relatorio: Dados["relatorio"]): relatorio is Relatorio {
  return Array.isArray(relatorio.administradoras);
}

function tituloDoRecorte(ufs: string[]) {
  if (ufs.length === 0) return "Brasil";
  if (ufs.length === 1) return nomeUf(ufs[0]);
  return "UFs selecionadas";
}

function Mercado({ relatorio }: { relatorio: Relatorio }) {
  const m = relatorio.recorte;
  if (!m) return null;
  const titulo = tituloDoRecorte(relatorio.ufs);
  const contemplados = m.contemplados_lance + m.contemplados_sorteio;

  return (
    <section className="cartao-praca cartao-praca--nacional" aria-label={titulo}>
      <header>
        <h4>{titulo}</h4>
        <span className="meta">{m.administradoras} administradoras</span>
      </header>
      <div className="metricas">
        <Metrica rotulo="Consorciados ativos" valor={inteiro(m.ativos)} />
        <Metrica rotulo="Adesões no trimestre" valor={inteiro(m.adesoes)} />
        <Metrica
          rotulo="Contemplações"
          valor={inteiro(contemplados)}
          detalhe={`${percentual(razao(m.contemplados_lance, contemplados))} por lance`}
        />
        <Metrica
          rotulo="Taxa de exclusão"
          valor={percentual(razao(m.excluidos, m.ativos + m.excluidos))}
        />
      </div>
      {relatorio.posicoes_uf.length > 1 && (
        <ul className="concorrencia" aria-label="Share da escolhida por UF: carteira → adesões">
          {relatorio.posicoes_uf.map((p) => (
            <li key={p.uf}>
              <span>{nomeUf(p.uf)}</span>
              <span>{seta(p.alvo.share_carteira, p.alvo.share_adesoes)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Administradora({
  perfil,
  comRecorte,
}: {
  perfil: PerfilAdministradora;
  comRecorte: boolean;
}) {
  const { recorte, nacional } = perfil;
  return (
    <section className="cartao-praca" aria-label={perfil.nome_administradora}>
      <header>
        <h4>{perfil.nome_administradora}</h4>
      </header>
      <div className="metricas">
        {comRecorte && (
          <>
            <Metrica rotulo="Share da carteira" valor={percentual(recorte.share_carteira)} />
            <Metrica
              rotulo="Share das adesões"
              valor={percentual(recorte.share_adesoes)}
              detalhe={`${inteiro(recorte.adesoes)} adesões`}
            />
          </>
        )}
        {nacional && (
          <>
            <Metrica rotulo="🇧🇷 Inadimplência" valor={percentual(nacional.inadimplencia)} />
            <Metrica
              rotulo="🇧🇷 Taxa de administração"
              valor={percentual(nacional.taxa_administracao)}
            />
          </>
        )}
      </div>
    </section>
  );
}

export function DadosEncontrados({ dados }: { dados: Dados }) {
  const relatorio = dados.relatorio;
  if (!ehRelatorioAtual(relatorio)) return null;

  return (
    <div className="dados">
      <h3>Dados encontrados</h3>
      <p className="meta">
        {relatorio.data_base_uf && `UFs · ${rotuloDataBase(relatorio.data_base_uf)}`}
        {relatorio.data_base_uf && relatorio.data_base_nacional && " · "}
        {relatorio.data_base_nacional &&
          `🇧🇷 nacional · ${rotuloDataBase(relatorio.data_base_nacional)}`}
      </p>
      {!relatorio.recorte && (
        <p className="aviso aviso--neutro">Não há recorte por UF publicado até esta data-base.</p>
      )}

      <div className="cartoes">
        <Mercado relatorio={relatorio} />
        {relatorio.administradoras.map((a) => (
          <Administradora key={a.cnpj_raiz} perfil={a} comRecorte={relatorio.recorte !== null} />
        ))}
      </div>
    </div>
  );
}
