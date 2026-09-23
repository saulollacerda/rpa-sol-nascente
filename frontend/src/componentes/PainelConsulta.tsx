import { useMemo, useState, type FormEvent } from "react";
import type { Opcoes, Solicitacao } from "../api/tipos";
import { rotuloDataBase } from "../dominio/formatacao";
import {
  administradorasDoSegmento,
  alternarUf,
  estadoInicial,
  MAX_CONCORRENTES,
  montarSolicitacao,
  validar,
  type Erros,
  type Formulario,
  validarTelefone,
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

  // Without a default number on the server, an empty field has nowhere to send to.
  const destinatarioObrigatorio = !opcoes.padrao.tem_destinatario_padrao;

  // Once a field shows an error, it is re-checked on every change so the error clears on fix.
  const atualizar = (parcial: Partial<Formulario>) => {
    const novo = { ...form, ...parcial };
    setForm(novo);
    const comErro = Object.keys(erros) as (keyof Formulario)[];
    if (comErro.length === 0) return;
    const encontrados = validar(novo, destinatarioObrigatorio);
    setErros(Object.fromEntries(comErro.map((campo) => [campo, encontrados[campo]])));
  };

  const conferirTelefone = (destinatario: string) =>
    setErros((e) => ({
      ...e,
      destinatario: validarTelefone(destinatario, destinatarioObrigatorio),
    }));

  const mudarSegmento = (segmento: number) => {
    const continua = administradorasDoSegmento(opcoes.administradoras, segmento).some(
      (a) => a.cnpj === form.cnpj,
    );
    // Administradora que não atua no novo segmento deixa de fazer sentido.
    atualizar({ segmento, cnpj: continua ? form.cnpj : "" });
  };

  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    const encontrados = validar(form, destinatarioObrigatorio);
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
          aria-invalid={Boolean(erros.dataBase)}
          onChange={(e) => atualizar({ dataBase: e.target.value })}
        >
          <option value="">Escolha a data-base</option>
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
          value={form.segmento || ""}
          aria-invalid={Boolean(erros.segmento)}
          onChange={(e) => mudarSegmento(Number(e.target.value))}
        >
          <option value="">Escolha o segmento</option>
          {opcoes.segmentos.map((s) => (
            <option key={s.codigo} value={s.codigo}>
              {s.codigo} · {s.nome}
            </option>
          ))}
        </select>
        {erros.segmento && <p className="erro-campo">{erros.segmento}</p>}
      </div>

      <div className="campo">
        <label htmlFor="administradora">Administradora</label>
        <select
          id="administradora"
          value={form.cnpj}
          aria-invalid={Boolean(erros.cnpj)}
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
            max={MAX_CONCORRENTES}
            step={1}
            value={form.topConcorrentes}
            onChange={(e) => atualizar({ topConcorrentes: Number(e.target.value) })}
          />
          <small>As maiores em adesões nas UFs.</small>
          {erros.topConcorrentes && <p className="erro-campo">{erros.topConcorrentes}</p>}
        </div>

        <div className="campo">
          <label htmlFor="destinatario">WhatsApp do destinatário</label>
          <input
            id="destinatario"
            type="tel"
            inputMode="tel"
            placeholder="Insira seu número de telefone"
            maxLength={20}
            value={form.destinatario}
            aria-invalid={Boolean(erros.destinatario)}
            onChange={(e) => atualizar({ destinatario: e.target.value })}
            onBlur={(e) => conferirTelefone(e.target.value)}
          />
          {erros.destinatario && (
            <p className="erro-campo" role="alert">
              {erros.destinatario}
            </p>
          )}
        </div>
      </div>

      <button type="submit" className="botao-principal" disabled={enviando}>
        {enviando ? "Gerando…" : "Gerar e enviar relatório"}
      </button>
    </form>
  );
}
