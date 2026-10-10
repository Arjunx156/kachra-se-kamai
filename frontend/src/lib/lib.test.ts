import { describe, expect, it } from 'vitest'
import { fitWithin } from './compressImage'
import { isToday, kg, rs } from './format'
import { material, MATERIALS } from './materials'

describe('fitWithin', () => {
  it('scales the long edge down to 1280 keeping aspect ratio', () => {
    expect(fitWithin(4000, 3000)).toEqual({ width: 1280, height: 960 })
    expect(fitWithin(3000, 4000)).toEqual({ width: 960, height: 1280 })
  })

  it('never upscales small images', () => {
    expect(fitWithin(800, 600)).toEqual({ width: 800, height: 600 })
    expect(fitWithin(1280, 720)).toEqual({ width: 1280, height: 720 })
  })
})

describe('format', () => {
  it('formats rupees with two decimals in Indian style', () => {
    expect(rs(1234.5)).toBe('₹1,234.50')
    expect(rs(undefined)).toBe('₹0.00')
  })

  it('shows grams under one kilo and kg above', () => {
    expect(kg(0.25)).toBe('250 g')
    expect(kg(1.5)).toBe('1.5 kg')
    expect(kg(0)).toBe('0 kg')
  })

  it('detects today', () => {
    const now = new Date(2026, 9, 10, 18)
    expect(isToday(new Date(2026, 9, 10, 9).toISOString(), now)).toBe(true)
    expect(isToday(new Date(2026, 9, 9, 23).toISOString(), now)).toBe(false)
    expect(isToday(undefined, now)).toBe(false)
  })
})

describe('materials', () => {
  it('matches the backend category table', () => {
    const recyclable = Object.entries(MATERIALS).filter(([, m]) => m.category === 'recyclable').map(([c]) => c)
    expect(recyclable).toHaveLength(9)
    expect(MATERIALS.WET_ORGANIC.category).toBe('compostable')
    expect(MATERIALS.SANITARY.category).toBe('landfill')
  })

  it('falls back to OTHER_LANDFILL for unknown codes', () => {
    expect(material('SPACESHIP').category).toBe('landfill')
  })
})
