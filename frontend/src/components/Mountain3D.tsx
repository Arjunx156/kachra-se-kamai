import { Html, OrbitControls } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'
import { FACTS } from '../lib/facts'

/** Scene units are metres. The mound starts at Ghazipur's reported height (2018) next to a Qutub-like tower. */
const H0 = FACTS.ghazipurHeightM.value
const TOWER_H = FACTS.qutubHeightM.value
const MOUND_RADIUS = 95
const TOWER_X = -125

// Deterministic pseudo-noise so the mound looks the same on every render.
function noise(x: number, z: number): number {
  return (
    Math.sin(x * 0.09) * Math.cos(z * 0.07) * 0.5 +
    Math.sin(x * 0.23 + z * 0.17) * 0.25 +
    Math.cos(x * 0.51 - z * 0.43) * 0.12
  )
}

function hash(x: number, z: number): number {
  const s = Math.sin(x * 12.9898 + z * 78.233) * 43758.5453
  return s - Math.floor(s)
}

const DIRT = [new THREE.Color('#6B5440'), new THREE.Color('#7D6650'), new THREE.Color('#5E5A52'), new THREE.Color('#8B7A62')]
const LITTER = [new THREE.Color('#3B82C4'), new THREE.Color('#E8E2D4'), new THREE.Color('#D9577A'), new THREE.Color('#E0B53A')]

/** Unit-height landfill mound (height 0..1). Flat-topped, terraced, with litter speckles. */
function useMoundGeometry(): THREE.BufferGeometry {
  return useMemo(() => {
    const g = new THREE.PlaneGeometry(MOUND_RADIUS * 2.3, MOUND_RADIUS * 2.3, 110, 110)
    g.rotateX(-Math.PI / 2)
    const pos = g.attributes.position
    const colors: number[] = []
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i)
      const z = pos.getZ(i)
      const r = Math.hypot(x * 1.0, z * 1.25) / MOUND_RADIUS
      const wobble = 1 + noise(x, z) * 0.12
      const t = THREE.MathUtils.smoothstep(1.0 * wobble, 0.28, r) // 0 at edge, 1 on plateau
      const terraces = Math.round(t * 6) / 6
      const h = Math.max(0, THREE.MathUtils.lerp(t, terraces, 0.35) + noise(x * 2, z * 2) * 0.03 * t)
      pos.setY(i, h)
      const speck = hash(x, z)
      const c = h > 0.02 && speck > 0.93 ? LITTER[Math.floor(speck * 1000) % LITTER.length] : DIRT[Math.floor(hash(z, x) * DIRT.length)]
      colors.push(c.r, c.g, c.b)
    }
    g.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
    g.computeVertexNormals()
    return g
  }, [])
}

function Mound({ heightFactor }: { heightFactor: number }) {
  const ref = useRef<THREE.Mesh>(null)
  const geometry = useMoundGeometry()
  useFrame((_, dt) => {
    if (!ref.current) return
    const target = H0 * heightFactor
    const current = ref.current.scale.y
    ref.current.scale.y = THREE.MathUtils.damp(current, target, 2.2, dt)
  })
  return (
    <mesh ref={ref} geometry={geometry} scale={[1, H0, 1]} castShadow receiveShadow>
      <meshStandardMaterial vertexColors flatShading roughness={1} />
    </mesh>
  )
}

/** A Qutub Minar-like tower from basic shapes: five tapering storeys with balconies (14.3 m base, 2.75 m top). */
function Tower() {
  const storeys = useMemo(() => {
    const fractions = [0.33, 0.22, 0.18, 0.14, 0.13]
    const out: { y: number; h: number; r0: number; r1: number }[] = []
    let y = 0
    fractions.forEach((f) => {
      const h = TOWER_H * f
      const r0 = THREE.MathUtils.lerp(7.16, 1.38, y / TOWER_H)
      const r1 = THREE.MathUtils.lerp(7.16, 1.38, (y + h) / TOWER_H)
      out.push({ y, h, r0, r1 })
      y += h
    })
    return out
  }, [])
  return (
    <group position={[TOWER_X, 0, 10]}>
      {storeys.map((s, i) => (
        <group key={i}>
          <mesh position={[0, s.y + s.h / 2, 0]} castShadow>
            <cylinderGeometry args={[s.r1, s.r0, s.h, 16, 1]} />
            <meshStandardMaterial color={i < 3 ? '#B5533C' : '#D9C6A5'} flatShading roughness={0.9} />
          </mesh>
          <mesh position={[0, s.y + s.h, 0]}>
            <cylinderGeometry args={[s.r1 + 1.1, s.r1 + 0.6, 0.9, 16]} />
            <meshStandardMaterial color="#8E3F2C" flatShading />
          </mesh>
        </group>
      ))}
      <Html position={[0, TOWER_H + 8, 0]} center distanceFactor={260} zIndexRange={[10, 0]}>
        <div className="whitespace-nowrap rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-slate shadow">Qutub Minar · 72.5 m</div>
      </Html>
    </group>
  )
}

function Gulls() {
  const group = useRef<THREE.Group>(null)
  const birds = useMemo(() => Array.from({ length: 6 }, (_, i) => ({ r: 40 + i * 9, speed: 0.25 + i * 0.04, y: H0 + 12 + i * 3, phase: i * 1.3 })), [])
  useFrame(({ clock }) => {
    group.current?.children.forEach((child, i) => {
      const b = birds[i]
      const t = clock.elapsedTime * b.speed + b.phase
      child.position.set(Math.cos(t) * b.r, b.y + Math.sin(t * 3) * 1.5, Math.sin(t) * b.r)
      child.rotation.y = -t
      child.rotation.z = Math.sin(clock.elapsedTime * 8 + i) * 0.4
    })
  })
  return (
    <group ref={group}>
      {birds.map((_, i) => (
        <mesh key={i}>
          <coneGeometry args={[1.2, 4, 3]} />
          <meshStandardMaterial color="#F4F1EA" flatShading />
        </mesh>
      ))}
    </group>
  )
}

function Scene({ heightFactor, compact }: { heightFactor: number; compact: boolean }) {
  return (
    <>
      <color attach="background" args={['#F6EFE0']} />
      <fog attach="fog" args={['#F6EFE0', 320, 620]} />
      <hemisphereLight args={['#FFF4DD', '#6B5440', 0.9]} />
      <directionalLight position={[120, 180, 80]} intensity={1.4} castShadow />
      <mesh rotation-x={-Math.PI / 2} position={[0, -0.2, 0]} receiveShadow>
        <circleGeometry args={[420, 48]} />
        <meshStandardMaterial color="#C9BC97" roughness={1} />
      </mesh>
      <Mound heightFactor={heightFactor} />
      <Tower />
      {!compact && <Gulls />}
      <OrbitControls
        enablePan={false}
        enableZoom={false}
        autoRotate
        autoRotateSpeed={compact ? 0.6 : 0.35}
        enableRotate={!compact}
        target={[-25, 28, 0]}
        minPolarAngle={0.6}
        maxPolarAngle={1.35}
      />
    </>
  )
}

interface Props {
  heightFactor: number
  compact?: boolean
  className?: string
}

/** Illustrative landfill mountain that shrinks (to 50% minimum) as kg are diverted on the platform. */
export default function Mountain3D({ heightFactor, compact = false, className = '' }: Props) {
  const clamped = Math.min(1, Math.max(0.5, heightFactor))
  return (
    <div className={`relative overflow-hidden rounded-3xl ${className}`} role="img" aria-label={`Illustrative landfill mountain at ${Math.round(clamped * 100)}% of its starting height, next to Qutub Minar for scale`}>
      <Canvas shadows dpr={[1, 1.75]} camera={{ position: [170, 95, 210], fov: compact ? 42 : 38, near: 1, far: 1500 }}>
        <Scene heightFactor={clamped} compact={compact} />
      </Canvas>
    </div>
  )
}
