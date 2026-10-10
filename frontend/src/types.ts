export type Role = 'household' | 'picker' | 'recycler' | 'city'

export type MaterialCode =
  | 'PET_BOTTLE'
  | 'HARD_PLASTIC'
  | 'MILK_POUCH'
  | 'MULTILAYER_PACKET'
  | 'PAPER'
  | 'CARDBOARD'
  | 'METAL'
  | 'GLASS'
  | 'E_WASTE'
  | 'WET_ORGANIC'
  | 'SANITARY'
  | 'OTHER_LANDFILL'

export type Category = 'recyclable' | 'compostable' | 'landfill'

export interface ScanItem {
  name: string
  material: MaterialCode
  count: number
  estWeightKg: number
  brand: string | null
}

export interface Totals {
  recyclableKg: number
  compostableKg: number
  landfillKg: number
}

export type ScanStatus = 'pending' | 'bundled' | 'collected' | 'no_recyclables'

export interface Scan {
  userId: string
  scanId: string
  societyId: string
  societyName?: string | null
  imageKey: string | null
  imageUrl?: string | null
  createdAt: string
  items: ScanItem[]
  totals: Totals
  estValueRs: number
  eprPackets: number
  eprRs: number
  segregationScore: number
  tip: string
  status: ScanStatus
  bundleId?: string
  finalRs?: number
  eprCreditedRs?: number
  demo?: boolean
}

export interface User {
  userId: string
  name: string
  role: Role
  societyId?: string
  lat?: number
  lng?: number
  language?: 'en' | 'hi'
}

export interface Counters {
  scannedKg: number
  recyclableKg: number
  compostableKg: number
  landfillKg: number
  divertedKg: number
  householdPayoutRs: number
  pickerPayoutRs: number
  eprRs: number
  scanCount: number
  pickupCount: number
}

export interface Society {
  societyId: string
  name: string
  area: string
  lat: number
  lng: number
}

export interface Me {
  user: User
  stats: Counters
  wallet: Pick<Counters, 'householdPayoutRs' | 'eprRs' | 'divertedKg' | 'pickerPayoutRs' | 'pickupCount'>
  week?: Totals & { scans: number }
  avgScore?: number | null
  latestScan?: Scan | null
  pendingRs?: number
  society?: Society | null
}

export type BundleStatus = 'open' | 'accepted' | 'collected'

export interface Bundle {
  bundleId: string
  societyId: string
  societyName: string
  area: string
  lat: number | null
  lng: number | null
  scanRefs: { userId: string; scanId: string }[]
  householdCount: number
  materials: Partial<Record<MaterialCode, number>>
  totalKg: number
  valueRs: number
  pickerShareRs: number
  status: BundleStatus
  pickerId?: string
  createdAt: string
  collectedAt?: string
  pickerRs?: number
  householdRs?: number
  eprRs?: number
  routeOrder?: number
  distanceKmFromPrev?: number
}

export interface BundleList {
  bundles: Bundle[]
  totalRouteKm: number
  base: { lat: number; lng: number } | null
}

export interface Rate {
  material: MaterialCode
  displayEn: string
  displayHi: string
  rsPerKg: number
  updatedBy: string | null
  updatedAt: string | null
  isDemoRate: boolean
}

export interface CityStats {
  counters: Counters
  mountain: { divertedKg: number; targetKg: number; minFactor: number; heightFactor: number; illustrative: boolean }
  time: string
}

export interface LeaderRow {
  societyId: string
  name: string
  area: string
  divertedKg: number
  scannedKg: number
  householdPayoutRs: number
  eprRs: number
  scanCount: number
  pickupCount: number
  rank: number
}

export interface CoachPlan {
  plan: string
  toolsCalled: string[]
  checked: string[]
  onboarding: boolean
  language: 'en' | 'hi'
  model?: string
}

export interface UploadTicket {
  uploadUrl: string
  imageKey: string
  contentType: string
  expiresIn: number
}
