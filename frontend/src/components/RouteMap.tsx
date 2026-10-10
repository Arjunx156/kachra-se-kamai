import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect } from 'react'
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from 'react-leaflet'
import { rs } from '../lib/format'
import type { Bundle } from '../types'

const DELHI: [number, number] = [28.6139, 77.209]

function numberIcon(n: number | string, color: string): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div style="background:${color};color:#fff;width:34px;height:34px;border-radius:9999px;display:flex;align-items:center;justify-content:center;font:700 16px 'Baloo 2',sans-serif;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3)">${n}</div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  })
}

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap()
  useEffect(() => {
    if (points.length > 1) map.fitBounds(L.latLngBounds(points), { padding: [36, 36] })
    else if (points.length === 1) map.setView(points[0], 13)
  }, [map, points])
  return null
}

interface Props {
  bundles: Bundle[]
  base: { lat: number; lng: number } | null
}

export default function RouteMap({ bundles, base }: Props) {
  const stops = bundles.filter((b) => b.lat !== null && b.lng !== null)
  const points: [number, number][] = [...(base ? [[base.lat, base.lng] as [number, number]] : []), ...stops.map((b) => [b.lat!, b.lng!] as [number, number])]
  return (
    <MapContainer center={DELHI} zoom={11} scrollWheelZoom={false} className="h-72 w-full md:h-96">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {base && (
        <Marker position={[base.lat, base.lng]} icon={numberIcon('🏠', '#334155')}>
          <Popup>Your base</Popup>
        </Marker>
      )}
      {stops.map((b) => (
        <Marker key={b.bundleId} position={[b.lat!, b.lng!]} icon={numberIcon(b.routeOrder ?? '•', b.status === 'accepted' ? '#F2A900' : '#1F5F3F')}>
          <Popup>
            <strong>{b.societyName}</strong>
            <br />
            {b.totalKg} kg · your share {rs(b.pickerShareRs)}
          </Popup>
        </Marker>
      ))}
      {points.length > 1 && <Polyline positions={points} pathOptions={{ color: '#1F5F3F', weight: 4, dashArray: '8 8', opacity: 0.7 }} />}
      <FitBounds points={points} />
    </MapContainer>
  )
}
