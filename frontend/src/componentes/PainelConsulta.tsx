import { useMemo, useState, type FormEvent } from "react";
import type { Opcoes, Solicitacao } from "../api/tipos";
import { rotuloDataBase } from "../dominio/formatacao";
import {
  administradorasDoSegmento,
  alternarUf,
  estadoInicial,
  montarSolicitacao,
  validar,
  type Erros,
  type Formulario,
} from "../dominio/formulario";

interface Props {
  opcoes: Opcoes;
  enviando: boolean;
  onEnviar: (solicitacao: Solicitacao) => void;
}

export function PainelConsulta({ opcoes, enviando, onEnviar }: Props) {
  const [form, setForm] = useState<Formulario>(() => estadoInicial(opcoes.padrao));
  const [erros, setErros] = useState<Erros>({});

  const administradoras = useMemo(
    () => administradorasDoSegmento(opcoes.administradoras, form.segmento),
    [opcoes.administradoras, form.segmento],
  );

  const atualizar = (parcial: Partial<Formulario>) => setForm((f) => ({ ...f, ...parcial }));

  const mudarSegmento = (segmento: number) =>
    setForm((f) => {
      const continua = administradorasDoSegmento(opcoes.administradoras, segmento).some(
        (a) => a.cnpj === f.cnpj,
      );
      // Administradora que não atua no novo segmento deixa de fazer sentido.
      return { ...f, segmento, cnpj: continua ? f.cnpj : "" };
    });

  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    const encontrados = validar(form);
    setErros(encontrados);
    if (Object.keys(encontrados).length === 0) onEnviar(montarSolicitacao(form));
  };

  return (
    <form className="painel" onSubmit={enviar} noValidate>
      <div className="campo">
        <label htmlFor="data-base">Data-base</label>
        <select
          id="data-base"
          value={form.dataBase}
          onChange={(e) => atualizar({ dataBase: e.target.value })}
        >
          {opcoes.data_bases.map((d) => (
            <option key={d} value={d}>
              {rotuloDataBase(d)}
            </option>
          ))}
        </select>
        <small>Praças usam o trimestre mais recente até esta data.</small>
        {erros.dataBase && <p className="erro-campo">{erros.dataBase}</p>}
      </div>

      <div className="campo">
        <label htmlFor="segmento">Segmento</label>
        <select
          id="segmento"
          value={form.segmento}
          onChange={(e) => mudarSegmento(Number(e.target.value))}
        >
          {opcoes.segmentos.map((s) => (
            <option key={s.codigo} value={s.codigo}>
              {s.codigo} · {s.nome}
            </option>
          ))}
        </select>
      </div>

      <div className="campo">
        <label htmlFor="administradora">Administradora</label>
        <select
          id="administradora"
          value={form.cnpj}
          onChange={(e) => atualizar({ cnpj: e.target.value })}
        >
          <option value="">Escolha a administradora</option>
          {administradoras.map((a) => (
            <option key={a.cnpj} value={a.cnpj}>
              {a.nome}
            </option>
          ))}
        </select>
        {erros.cnpj && <p className="erro-campo">{erros.cnpj}</p>}
      </div>

      <fieldset className="campo">
        <legend>Praças</legend>
        <div className="fichas">
          {opcoes.ufs.map((uf) => (
            <button
              key={uf.sigla}
              type="button"
              className="ficha"
              aria-pressed={form.ufs.includes(uf.sigla)}
              title={uf.sigla}
              onClick={() => atualizar({ ufs: alternarUf(form.ufs, uf.sigla) })}
            >
              {uf.nome}
            </button>
          ))}
        </div>
        {erros.ufs && <p className="erro-campo">{erros.ufs}</p>}
      </fieldset>

      <div className="linha">
        <div className="campo">
          <label htmlFor="top">Concorrentes</label>
          <input
            id="top"
            type="number"
            min={0}
            max={10}
            value={form.topConcorrentes}
            onChange={(e) => atualizar({ topConcorrentes: Number(e.target.value) })}
          />
          <small>No ranking de cada praça.</small>
          {erros.topConcorrentes && <p className="erro-campo">{erros.topConcorrentes}</p>}
        </div>

        <div className="campo">
          <label htmlFor="destinatario">WhatsApp do destinatário</label>
          <input
            id="destinatario"
            type="tel"
            inputMode="tel"
            placeholder="+55 86 99999-0000"
            value={form.destinatario}
            onChange={(e) => atualizar({ destinatario: e.target.value })}
          />
          <small>Em branco: usa o número configurado no servidor.</small>
          {erros.destinatario && <p className="erro-campo">{erros.destinatario}</p>}
        </div>
      </div>

      <button type="submit" className="botao-principal" disabled={enviando}>
        {enviando ? "Gerando…" : "Gerar e enviar relatório"}
      </button>
    </form>
  );
}
