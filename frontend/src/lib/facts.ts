/**
 * Real-world figures shown in the UI. Every entry is cited; nothing here is a demo value.
 * If a figure cannot be cited, it must not be added.
 */
export const FACTS = {
  qutubHeightM: {
    value: 72.5,
    text: 'Qutub Minar is 72.5 m tall',
    source: 'UNESCO World Heritage Centre, Qutb Minar and its Monuments',
    url: 'https://whc.unesco.org/en/list/233',
  },
  ghazipurHeightM: {
    value: 65,
    text: 'Ghazipur landfill was reported at 65 m in 2018',
    source: 'Business Today, 3 Sep 2018',
    url: 'https://www.businesstoday.in/latest/economy-politics/story/east-delhi-ghazipur-garbage-dump-now-almost-as-tall-as-qutub-minar-110974-2018-09-03',
  },
  delhiWasteTpd: {
    value: 11852,
    text: 'Delhi generates 11,852 tonnes of waste a day and processes 7,611',
    source: 'CPCB affidavit to the NGT, reported 1 Jan 2026',
    url: 'https://madhyamamonline.com/amp/india/delhi-processes-only-64-of-daily-waste-rest-dumped-at-bhalswa-ghazipur-landfills-cpcb-tells-ngt-1482173',
  },
} as const
