import { useEffect } from 'react'
import { MapContainer, Marker, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// A plain CSS marker avoids Leaflet's classic bundler issue where its
// default marker image URLs resolve relative to its own asset location.
const markerIcon = L.divIcon({
  className: '',
  html: '<div style="width:16px;height:16px;border-radius:9999px;background:#059669;border:3px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.4);"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})

interface LocationMapProps {
  latitude: number
  longitude: number
}

function Recenter({ latitude, longitude }: LocationMapProps) {
  const map = useMap()
  useEffect(() => {
    map.setView([latitude, longitude], map.getZoom())
  }, [latitude, longitude, map])
  return null
}

export function LocationMap({ latitude, longitude }: LocationMapProps) {
  return (
    <MapContainer
      center={[latitude, longitude]}
      zoom={11}
      scrollWheelZoom={false}
      className="h-64 w-full rounded-2xl"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Marker position={[latitude, longitude]} icon={markerIcon} />
      <Recenter latitude={latitude} longitude={longitude} />
    </MapContainer>
  )
}
