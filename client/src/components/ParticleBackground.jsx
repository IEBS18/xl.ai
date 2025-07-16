import React, { useEffect, forwardRef } from "react"
import * as THREE from "three"
import { useTheme } from "../context/ThemeProvider"

const ParticleBackground = forwardRef(({ className = "absolute inset-0 z-0 opacity-30" }, ref) => {
  const { isDark } = useTheme()

  useEffect(() => {
    if (!ref?.current) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(
      75,
      ref.current.clientWidth / ref.current.clientHeight,
      0.1,
      1000,
    )
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })

    renderer.setSize(ref.current.clientWidth, ref.current.clientHeight)
    ref.current.appendChild(renderer.domElement)

    const particleGeometry = new THREE.BufferGeometry()
    const particleCount = 50
    const positions = new Float32Array(particleCount * 3)

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 15
      positions[i * 3 + 1] = (Math.random() - 0.5) * 10
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10
    }

    particleGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3))

    const particleMaterial = new THREE.PointsMaterial({
      size: 0.02,
      color: isDark ? 0xffffff : 0x000000,
      transparent: true,
      opacity: 0.3,
    })

    const particles = new THREE.Points(particleGeometry, particleMaterial)
    scene.add(particles)

    camera.position.z = 8

    const animate = (time) => {
      requestAnimationFrame(animate)

      const t = time * 0.0005

      const positions = particles.geometry.attributes.position.array
      for (let i = 0; i < particleCount; i++) {
        positions[i * 3 + 1] += Math.sin(t + i * 0.1) * 0.001

        if (positions[i * 3 + 1] > 5) positions[i * 3 + 1] = -5
        if (positions[i * 3 + 1] < -5) positions[i * 3 + 1] = 5
      }
      particles.geometry.attributes.position.needsUpdate = true

      particles.rotation.y = t * 0.05

      renderer.render(scene, camera)
    }

    animate(0)

    return () => {
      if (ref.current && renderer.domElement) {
        ref.current.removeChild(renderer.domElement)
      }
      renderer.dispose()
    }
  }, [isDark, ref])

  return <div ref={ref} className={className} />
})

ParticleBackground.displayName = "ParticleBackground"

export default ParticleBackground