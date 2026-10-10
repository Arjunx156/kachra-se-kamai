import { afterEach, describe, expect, it, vi } from 'vitest'

vi.stubEnv('VITE_API_URL', 'https://api.example.test/')

const { api, ApiError, uploadToS3 } = await import('./api')

function mockFetch(impl: (...args: unknown[]) => Promise<unknown>) {
  const fn = vi.fn(impl)
  vi.stubGlobal('fetch', fn)
  return fn
}

afterEach(() => vi.unstubAllGlobals())

describe('api client', () => {
  it('unwraps the ok envelope and builds the URL', async () => {
    const f = mockFetch(async () => ({ status: 200, json: async () => ({ ok: true, data: { status: 'ok' } }) }))
    await expect(api.me('u_priya')).resolves.toEqual({ status: 'ok' })
    expect(f).toHaveBeenCalledWith('https://api.example.test/me?userId=u_priya', expect.objectContaining({ method: 'GET' }))
  })

  it('sends JSON bodies', async () => {
    const f = mockFetch(async () => ({ status: 200, json: async () => ({ ok: true, data: {} }) }))
    await api.accept('b_1', 'u_ramesh')
    const [, init] = f.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({ pickerId: 'u_ramesh' })
  })

  it('turns error envelopes into ApiError with code and message', async () => {
    mockFetch(async () => ({ status: 422, json: async () => ({ ok: false, error: { code: 'NOT_A_BIN', message: 'Not a bin' } }) }))
    const err = await api.createScan('u', 'k').catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err.code).toBe('NOT_A_BIN')
    expect(err.status).toBe(422)
  })

  it('reports network failures in friendly words', async () => {
    mockFetch(async () => {
      throw new TypeError('Failed to fetch')
    })
    await expect(api.city()).rejects.toMatchObject({ code: 'NETWORK' })
  })

  it('reports non-JSON replies', async () => {
    mockFetch(async () => ({ status: 502, json: async () => JSON.parse('<html>') }))
    await expect(api.city()).rejects.toMatchObject({ code: 'BAD_RESPONSE' })
  })

  it('uploads to S3 with the signed content type', async () => {
    const f = mockFetch(async () => ({ ok: true }))
    await uploadToS3('https://s3.example/put', new Blob(['x']), 'image/jpeg')
    const [, init] = f.mock.calls[0] as [string, RequestInit]
    expect(init.headers).toEqual({ 'Content-Type': 'image/jpeg' })
    mockFetch(async () => ({ ok: false, status: 403 }))
    await expect(uploadToS3('u', new Blob(['x']), 'image/jpeg')).rejects.toMatchObject({ code: 'UPLOAD_FAILED' })
  })
})
