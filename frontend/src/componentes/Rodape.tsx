import { Logo } from "./Logo";

/**
 * Ported from CRM-LEADS-SOLNASCENTE (src/components/publico/Rodape.tsx).
 * Items without `href` render as plain text, not dead links: this panel has no
 * public pages yet. Fill `href` once they exist.
 */
type Item = { texto: string; href?: string };

const COLUNAS: { titulo: string; itens: Item[] }[] = [
  {
    titulo: "Motos",
    itens: [
      { texto: "CG 160 Fan" },
      { texto: "CG 160 Titan" },
      { texto: "Biz 125" },
      { texto: "Pop 110i" },
    ],
  },
  {
    titulo: "Serviços",
    itens: [
      { texto: "Consórcio" },
      { texto: "Financiamento" },
      { texto: "Peças e acessórios" },
      { texto: "Revisão e pós-venda" },
    ],
  },
  {
    titulo: "Sol Nascente",
    itens: [
      { texto: "Unidade Teresina" },
      { texto: "Unidade Timon" },
      { texto: "Trabalhe conosco" },
      { texto: "Contato" },
    ],
  },
];

export function Rodape() {
  return (
    <footer className="rodape">
      <div className="rodape__principal">
        <div>
          <Logo />
          <p className="rodape__redes-titulo">Siga nas redes sociais</p>
          <div className="rodape__redes">
            <Facebook />
            <Instagram />
            <Youtube />
          </div>
        </div>

        <div className="rodape__colunas">
          {COLUNAS.map((coluna) => (
            <div key={coluna.titulo}>
              <h2 className="rodape__coluna-titulo">{coluna.titulo}</h2>
              <ul className="rodape__lista">
                {coluna.itens.map((item) => (
                  <li key={item.texto}>
                    {item.href ? <a href={item.href}>{item.texto}</a> : item.texto}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="rodape__barra">
        <p className="rodape__lema">Desacelere. Seu bem maior é a vida.</p>
        <p className="rodape__legal">
          <span>Fonte dos dados: Banco Central do Brasil</span>
          <span>Política de privacidade</span>
          <span>Termos de uso</span>
          <span>© {new Date().getFullYear()} Sol Nascente Motos</span>
        </p>
      </div>
    </footer>
  );
}

function Facebook() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-label="Facebook" role="img">
      <path d="M14.5 8.5h2.2V5.6c-.4-.05-1.7-.16-3.2-.16-3.2 0-5.3 1.9-5.3 5.4V13H5.5v3.3h2.7V24h3.4v-7.7h2.7l.4-3.3h-3.1v-1.8c0-1 .3-1.7 1.9-1.7z" />
    </svg>
  );
}

function Instagram() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      aria-label="Instagram"
      role="img"
    >
      <rect x="2.5" y="2.5" width="19" height="19" rx="5" />
      <circle cx="12" cy="12" r="4.2" />
      <circle cx="17.4" cy="6.6" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  );
}

function Youtube() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-label="YouTube" role="img">
      <path d="M22.5 7.4a2.8 2.8 0 0 0-1.9-2C18.9 5 12 5 12 5s-6.9 0-8.6.4a2.8 2.8 0 0 0-1.9 2C1.1 9.1 1.1 12 1.1 12s0 2.9.4 4.6a2.8 2.8 0 0 0 1.9 2c1.7.4 8.6.4 8.6.4s6.9 0 8.6-.4a2.8 2.8 0 0 0 1.9-2c.4-1.7.4-4.6.4-4.6s0-2.9-.4-4.6zM9.8 15.3V8.7l5.7 3.3z" />
    </svg>
  );
}
