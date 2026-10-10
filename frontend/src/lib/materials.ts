import type { Category, MaterialCode } from '../types'

export const MATERIALS: Record<MaterialCode, { en: string; hi: string; category: Category; emoji: string }> = {
  PET_BOTTLE: { en: 'PET bottles', hi: 'प्लास्टिक बोतल', category: 'recyclable', emoji: '🧴' },
  HARD_PLASTIC: { en: 'Hard plastic', hi: 'सख्त प्लास्टिक', category: 'recyclable', emoji: '🪣' },
  MILK_POUCH: { en: 'Milk pouches', hi: 'दूध की थैली', category: 'recyclable', emoji: '🥛' },
  MULTILAYER_PACKET: { en: 'Chips / snack packets', hi: 'चिप्स के पैकेट', category: 'recyclable', emoji: '🍟' },
  PAPER: { en: 'Paper / newspaper', hi: 'कागज़', category: 'recyclable', emoji: '📰' },
  CARDBOARD: { en: 'Cardboard', hi: 'गत्ता', category: 'recyclable', emoji: '📦' },
  METAL: { en: 'Metal cans', hi: 'धातु', category: 'recyclable', emoji: '🥫' },
  GLASS: { en: 'Glass', hi: 'कांच', category: 'recyclable', emoji: '🫙' },
  E_WASTE: { en: 'E-waste', hi: 'ई-कचरा', category: 'recyclable', emoji: '🔋' },
  WET_ORGANIC: { en: 'Wet / kitchen waste', hi: 'गीला कचरा', category: 'compostable', emoji: '🥬' },
  SANITARY: { en: 'Sanitary waste', hi: 'सैनिटरी कचरा', category: 'landfill', emoji: '🚫' },
  OTHER_LANDFILL: { en: 'Other', hi: 'अन्य', category: 'landfill', emoji: '🗑️' },
}

export const EPR_MATERIALS: MaterialCode[] = ['MULTILAYER_PACKET', 'MILK_POUCH', 'PET_BOTTLE']

export const CATEGORY_STYLE: Record<Category, { label: string; bg: string; text: string; bar: string }> = {
  recyclable: { label: 'Recyclable', bg: 'bg-leaf-50', text: 'text-leaf', bar: 'bg-leaf' },
  compostable: { label: 'Could become compost', bg: 'bg-compost-50', text: 'text-compost', bar: 'bg-compost' },
  landfill: { label: 'To landfill', bg: 'bg-clay-50', text: 'text-clay', bar: 'bg-clay' },
}

export const material = (code: string) => MATERIALS[code as MaterialCode] ?? MATERIALS.OTHER_LANDFILL
