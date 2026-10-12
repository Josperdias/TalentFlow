# ADR 0002: clientes nativos, contrato OpenAPI e autenticação

- Estado: aceito (2026-10-12)
- Decisão:
  - **Site** React/TypeScript compilado (Vite), `HashRouter` + `base: './'`: funciona na raiz ou em subpasta de qualquer servidor
    estático sem regras de reescrita. Mesma origem com proxy `/api` usa **cookie HttpOnly + CSRF**; API em outro domínio usa Bearer.
  - **Android** Kotlin + Jetpack Compose; **Windows** C# + WinUI 3 (unpackaged, self-contained). Sem WebView, Electron, Capacitor,
    Cordova ou TWA (verificação automática `scripts/check-native-policy.sh` no CI).
  - Lógica de rede compartilhada **por especificação**, não por código: `:core` (Kotlin) e `TalentFlow.Core` (C#) implementam o mesmo
    contrato e passam nos **mesmos cenários contra a API real** (login, isolamento, sincronização, conflito, refresh).
  - Login nativo: formulário nativo -> `/auth/token` -> access token (15 min) + refresh token opaco rotativo (30 dias) com detecção de
    reuso. Tokens em **Android Keystore (AES-GCM)** e **DPAPI** do Windows. O fluxo OAuth 2.0 Authorization Code + PKCE via navegador do
    sistema, previsto na missão, **não foi implementado** (documentado em STATUS).
  - Sem geração automática de SDK a partir do OpenAPI nesta versão: modelos escritos à mão, protegidos por testes de integração e por
    verificação de deriva do contrato (`packages/contracts/openapi.json`).
- Consequências: custo de manter três clientes alinhados manualmente; mitigado por testes reais e pelo contrato versionado.
