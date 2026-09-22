import type { Status } from "../api/tipos";
import { rotuloStatus } from "../dominio/formatacao";

export function SeloStatus({ status, anunciar = false }: { status: Status; anunciar?: boolean }) {
  const { rotulo, tom } = rotuloStatus(status);
  return (
    <span className={`selo selo--${tom}`} role={anunciar ? "status" : undefined}>
      {rotulo}
    </span>
  );
}
