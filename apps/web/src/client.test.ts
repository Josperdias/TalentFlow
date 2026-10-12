import { describe, expect, it } from 'vitest';
import { ApiError } from './api/client';
import { fitLabel, fmtMoney, JOB_STATUS } from './format';

describe('ApiError', () => {
  it('identifica conflito 409 com o snapshot atual', () => {
    const e = new ApiError(409, 'alterado', { current_version: 3, current: { title: 'x' } });
    expect(e.isConflict).toBe(true);
    expect(e.conflictSnapshot?.current_version).toBe(3);
  });
  it('não trata outros status como conflito', () => {
    expect(new ApiError(403, 'sem permissão').isConflict).toBe(false);
    expect(new ApiError(403, 'sem permissão').conflictSnapshot).toBeNull();
  });
});

describe('formatação', () => {
  it('classifica fit por faixa', () => {
    expect(fitLabel(80)).toBe('Alto'); expect(fitLabel(60)).toBe('Médio'); expect(fitLabel(10)).toBe('Baixo');
  });
  it('não exibe zero como valor monetário', () => { expect(fmtMoney(0)).toBe('—'); expect(fmtMoney(5000)).toContain('5.000'); });
  it('cobre todas as situações de vaga do servidor', () => {
    for (const s of ['open', 'approval', 'closed', 'archived']) expect(JOB_STATUS[s]).toBeDefined();
  });
});
