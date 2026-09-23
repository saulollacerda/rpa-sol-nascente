import { describe, expect, it, vi } from "vitest";
import { ErroApi, mensagemDeErro, obterConexao, reconectarWhatsApp, solicitar } from "./cliente";

function responder(status: number, corpo: unknown) {
  const fetch = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(corpo), { status, headers: { "Content-Type": "application/json" } }),
  );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("mensagens de erro da API", () => {
  it("detail em texto (HTTPException)", () => {
    expect(mensagemDeErro(422, { detail: "destinatário não informado" })).toBe(
      "destinatário não informado",
    );
  });

  it("detail em lista (validação do pydantic)", () => {
    const corpo = { detail: [{ loc: ["body", "ufs"], msg: "Value error, UF inválida: XX" }] };
    expect(mensagemDeErro(422, corpo)).toBe("ufs: UF inválida: XX");
  });

  it("corpo desconhecido", () => {
    expect(mensagemDeErro(500, null)).toBe("erro inesperado (HTTP 500)");
  });
});

describe("solicitar", () => {
  it("envia o corpo em JSON para POST /execucoes", async () => {
    const fetch = responder(202, { decisao: "CRIAR", execucao: { id: 7 } });
    const resposta = await solicitar({ data_base: "202607" } as never);

    const [url, init] = fetch.mock.calls[0];
    expect(url).toBe("/execucoes");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ data_base: "202607" });
    expect(resposta.decisao).toBe("CRIAR");
    expect(resposta.execucao.id).toBe(7);
  });

  it("erro vira ErroApi com a mensagem traduzida", async () => {
    responder(422, { detail: "destinatário não informado" });
    await expect(solicitar({} as never)).rejects.toEqual(
      new ErroApi(422, "destinatário não informado"),
    );
  });
});

describe("conexão do WhatsApp", () => {
  it("lê o status em GET /whatsapp/conexao", async () => {
    const fetch = responder(200, { situacao: "CONECTADO", conta: null, qr_code: null, mensagem: null });
    const conexao = await obterConexao();
    expect(fetch.mock.calls[0][0]).toBe("/whatsapp/conexao");
    expect(conexao.situacao).toBe("CONECTADO");
  });

  it("pede um QR code novo em POST /whatsapp/conexao/reconectar", async () => {
    const fetch = responder(202, null);
    await reconectarWhatsApp();
    const [url, init] = fetch.mock.calls[0];
    expect(url).toBe("/whatsapp/conexao/reconectar");
    expect(init.method).toBe("POST");
  });
});

describe("resposta que não é da API", () => {
  it("HTML com status 200 vira erro, não dado vazio", async () => {
    // Proxy do Vite sem a rota: o dev server devolve o index.html do painel.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("<!doctype html><html></html>", {
          status: 200,
          headers: { "Content-Type": "text/html" },
        }),
      ),
    );
    await expect(obterConexao()).rejects.toEqual(
      new ErroApi(200, "resposta inesperada do servidor"),
    );
  });

  it("corpo JSON null continua válido (POST sem retorno)", async () => {
    responder(202, null);
    await expect(reconectarWhatsApp()).resolves.toBeNull();
  });
});
