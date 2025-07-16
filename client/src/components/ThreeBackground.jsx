import React, { useEffect, forwardRef } from "react"
import * as THREE from "three"
import { useTheme } from "../context/ThemeProvider"

const ThreeBackground = forwardRef(({ className = "absolute inset-0 z-0 opacity-20" }, ref) => {
  const { isDark } = useTheme()

  useEffect(() => {
    if (!ref?.current) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })

    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    ref.current.appendChild(renderer.domElement)

    // Simple nodes - black and white only
    const nodes = []
    const connections = []

    const nodeGeometry = new THREE.SphereGeometry(0.02, 12, 12)
    const nodeMaterial = new THREE.MeshBasicMaterial({
      color: isDark ? 0xffffff : 0x000000,
      transparent: true,
      opacity: 0.6,
    })

    // Create minimal grid pattern
    for (let i = 0; i < 20; i++) {
      const node = new THREE.Mesh(nodeGeometry, nodeMaterial)
      const position = new THREE.Vector3(
        (Math.random() - 0.5) * 15,
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 8,
      )

      node.position.copy(position)
      nodes.push({ core: node, originalPosition: position.clone() })
      scene.add(node)
    }

    // Simple connections
    const lineMaterial = new THREE.LineBasicMaterial({
      color: isDark ? 0xffffff : 0x000000,
      transparent: true,
      opacity: 0.1,
    })

    nodes.forEach((nodeA, i) => {
      nodes.forEach((nodeB, j) => {
        if (i !== j && nodeA.core.position.distanceTo(nodeB.core.position) < 5) {
          const geometry = new THREE.BufferGeometry().setFromPoints([nodeA.core.position, nodeB.core.position])
          const line = new THREE.Line(geometry, lineMaterial)
          connections.push({ line, nodeA: nodeA.core, nodeB: nodeB.core })
          scene.add(line)
        }
      })
    })

    camera.position.z = 8

    const animate = (time) => {
      requestAnimationFrame(animate)

      const t = time * 0.0003

      // Subtle floating motion
      nodes.forEach((node, i) => {
        const { core, originalPosition } = node
        core.position.y = originalPosition.y + Math.sin(t + i) * 0.1
        core.position.x = originalPosition.x + Math.cos(t + i * 0.5) * 0.05

        // Subtle opacity changes
        core.material.opacity = 0.4 + Math.sin(t * 2 + i) * 0.2
      })

      // Update connections
      connections.forEach((connection) => {
        const { line, nodeA, nodeB } = connection
        line.geometry.setFromPoints([nodeA.position, nodeB.position])
      })

      // Very subtle rotation
      scene.rotation.y = t * 0.02

      renderer.render(scene, camera)
    }

    animate(0)

    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
      renderer.setSize(window.innerWidth, window.innerHeight)
    }

    window.addEventListener("resize", handleResize)

    return () => {
      window.removeEventListener("resize", handleResize)
      if (ref.current && renderer.domElement) {
        ref.current.removeChild(renderer.domElement)
      }
      renderer.dispose()
    }
  }, [isDark, ref])

  return <div ref={ref} className={className} />
})

ThreeBackground.displayName = "ThreeBackground"

export default ThreeBackground