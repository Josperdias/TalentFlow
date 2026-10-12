export interface AppConfig {
  /** Base da API. "/api/v1" (mesma origem, via proxy reverso) ou URL absoluta https://api.exemplo.com.br/api/v1 */
  apiBaseUrl: string;
  publicWebUrl?: string;
  /** Página de downloads (GitHub Releases) dos apps Android e Windows. */
  downloadsUrl?: string;
}

export let config: AppConfig = { apiBaseUrl: '/api/v1' };

/** Lê config.json (público, sem segredos) na inicialização, para permitir ajuste sem recompilar. */
export async function loadConfig(): Promise<void> {
  try {
    const res = await fetch('config.json', { cache: 'no-store' });
    if (res.ok) {
      const data = (await res.json()) as Partial<AppConfig>;
      if (typeof data.apiBaseUrl === 'string' && data.apiBaseUrl.trim()) {
        config = { ...config, ...data, apiBaseUrl: data.apiBaseUrl.replace(/\/+$/, '') };
      }
    }
  } catch {
    /* mantém o padrão; o diagnóstico de API mostrará o problema real */
  }
}
