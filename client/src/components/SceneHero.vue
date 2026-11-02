<!--
  SceneHero: dark page-header banner with an animated Three.js scene behind the content.
  Copy to src/components/SceneHero.vue. Requires `npm install three`.

  Usage (typically only the Dashboard / overview view):
    <SceneHero>
      <h2>Overview</h2>
      <p>Inventory health at a glance</p>
    </SceneHero>

  Design contract
  - The scene is DECORATION. It never carries data and is aria-hidden. Real content is in the slot.
  - `three` is loaded with a dynamic import, so it lands in its own chunk and does not block first paint.
  - The scene reads --color-accent from the design tokens, so it follows the app's brand color.
  - It pauses when scrolled offscreen or when the tab is hidden, renders one still frame under
    prefers-reduced-motion, and falls back to a CSS gradient if WebGL is unavailable.
  - Everything it creates is disposed on unmount (geometries, materials, renderer, listeners).
-->
<template>
  <section class="scene-hero" :class="{ 'no-webgl': fallback }">
    <div ref="host" class="scene-host" aria-hidden="true"></div>
    <div class="scene-shade" aria-hidden="true"></div>
    <div class="scene-content"><slot /></div>
  </section>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'

export default {
  name: 'SceneHero',
  props: {
    // Number of drifting nodes. 40 to 80 looks good; more costs frame time for little gain.
    density: { type: Number, default: 56 }
  },
  setup(props) {
    const host = ref(null)
    const fallback = ref(false)
    let teardown = null
    let disposed = false

    const webglAvailable = () => {
      try {
        const canvas = document.createElement('canvas')
        return !!(window.WebGLRenderingContext && (canvas.getContext('webgl2') || canvas.getContext('webgl')))
      } catch (e) {
        return false
      }
    }

    const start = async () => {
      const THREE = await import('three')
      if (disposed || !host.value) return

      const el = host.value
      const cssColor = (name, fallbackColor) => {
        const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
        return new THREE.Color(value || fallbackColor)
      }
      const accent = cssColor('--color-accent', '#2563eb')
      const light = new THREE.Color('#e2e8f0')

      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' })
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
      renderer.setClearColor(0x000000, 0)
      renderer.domElement.style.cssText = 'display:block;width:100%;height:100%'
      el.appendChild(renderer.domElement)

      const scene = new THREE.Scene()
      const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100)
      camera.position.z = 14

      // Drifting nodes joined by faint lines when they are close
      const N = props.density
      const LINK_DIST = 3.2
      const pos = new Float32Array(N * 3)
      const vel = new Float32Array(N * 3)
      const bounds = { x: 10, y: 4, z: 3 }
      for (let i = 0; i < N; i++) {
        pos[i * 3] = (Math.random() * 2 - 1) * bounds.x
        pos[i * 3 + 1] = (Math.random() * 2 - 1) * bounds.y
        pos[i * 3 + 2] = (Math.random() * 2 - 1) * bounds.z
        vel[i * 3] = (Math.random() - 0.5) * 0.35
        vel[i * 3 + 1] = (Math.random() - 0.5) * 0.25
        vel[i * 3 + 2] = (Math.random() - 0.5) * 0.15
      }

      const pointGeo = new THREE.BufferGeometry()
      pointGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
      const pointMat = new THREE.PointsMaterial({ color: light, size: 0.09, transparent: true, opacity: 0.85, depthWrite: false })
      const points = new THREE.Points(pointGeo, pointMat)
      scene.add(points)

      const maxSegments = (N * (N - 1)) / 2
      const linePos = new Float32Array(maxSegments * 6)
      const lineGeo = new THREE.BufferGeometry()
      lineGeo.setAttribute('position', new THREE.BufferAttribute(linePos, 3).setUsage(THREE.DynamicDrawUsage))
      const lineMat = new THREE.LineBasicMaterial({ color: accent, transparent: true, opacity: 0.35, depthWrite: false })
      const lines = new THREE.LineSegments(lineGeo, lineMat)
      scene.add(lines)

      // Centerpiece: two counter-rotating wireframe polyhedra
      const outerGeo = new THREE.IcosahedronGeometry(2.4, 1)
      const outerMat = new THREE.MeshBasicMaterial({ color: accent, wireframe: true, transparent: true, opacity: 0.6 })
      const outer = new THREE.Mesh(outerGeo, outerMat)
      const innerGeo = new THREE.IcosahedronGeometry(1.4, 0)
      const innerMat = new THREE.MeshBasicMaterial({ color: light, wireframe: true, transparent: true, opacity: 0.4 })
      const inner = new THREE.Mesh(innerGeo, innerMat)
      const centerpiece = new THREE.Group()
      centerpiece.add(outer, inner)
      scene.add(centerpiece)

      const updateLines = () => {
        let n = 0
        for (let i = 0; i < N; i++) {
          for (let j = i + 1; j < N; j++) {
            const dx = pos[i * 3] - pos[j * 3]
            const dy = pos[i * 3 + 1] - pos[j * 3 + 1]
            const dz = pos[i * 3 + 2] - pos[j * 3 + 2]
            if (dx * dx + dy * dy + dz * dz < LINK_DIST * LINK_DIST) {
              linePos[n++] = pos[i * 3]; linePos[n++] = pos[i * 3 + 1]; linePos[n++] = pos[i * 3 + 2]
              linePos[n++] = pos[j * 3]; linePos[n++] = pos[j * 3 + 1]; linePos[n++] = pos[j * 3 + 2]
            }
          }
        }
        lineGeo.setDrawRange(0, n / 3)
        lineGeo.attributes.position.needsUpdate = true
      }

      const resize = () => {
        const w = Math.max(el.clientWidth, 1)
        const h = Math.max(el.clientHeight, 1)
        renderer.setSize(w, h, false)
        camera.aspect = w / h
        camera.updateProjectionMatrix()
        // World-space size of the view at z = 0, to keep the scene framed at any width
        const viewH = 2 * Math.tan((camera.fov * Math.PI) / 360) * camera.position.z
        const viewW = viewH * camera.aspect
        bounds.x = viewW / 2 + 1
        bounds.y = viewH / 2 + 1
        centerpiece.position.set(viewW * 0.3, 0, 0)
        centerpiece.scale.setScalar(Math.min(1, viewW / 18))
      }

      // Gentle parallax toward the pointer
      const target = { x: 0, y: 0 }
      const onPointer = (e) => {
        target.x = (e.clientX / window.innerWidth - 0.5) * 2
        target.y = (e.clientY / window.innerHeight - 0.5) * 2
      }
      window.addEventListener('pointermove', onPointer, { passive: true })

      const reduceQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
      let animate = !reduceQuery.matches
      let inView = true
      let rafId = 0
      let last = performance.now()

      const renderFrame = () => renderer.render(scene, camera)

      const tick = (now) => {
        rafId = 0
        const dt = Math.min((now - last) / 1000, 0.05)
        last = now

        for (let i = 0; i < N; i++) {
          for (let k = 0; k < 3; k++) {
            const idx = i * 3 + k
            pos[idx] += vel[idx] * dt
            const limit = k === 0 ? bounds.x : k === 1 ? bounds.y : bounds.z
            if (pos[idx] > limit) pos[idx] = -limit
            else if (pos[idx] < -limit) pos[idx] = limit
          }
        }
        pointGeo.attributes.position.needsUpdate = true
        updateLines()

        outer.rotation.x += dt * 0.18
        outer.rotation.y += dt * 0.24
        inner.rotation.x -= dt * 0.3
        inner.rotation.y -= dt * 0.22

        camera.position.x += (target.x * 0.8 - camera.position.x) * 0.04
        camera.position.y += (-target.y * 0.5 - camera.position.y) * 0.04
        camera.lookAt(0, 0, 0)

        renderFrame()
        schedule()
      }

      const schedule = () => {
        if (rafId || !animate || !inView || document.hidden || disposed) return
        last = performance.now()
        rafId = requestAnimationFrame(tick)
      }

      const stop = () => {
        if (rafId) cancelAnimationFrame(rafId)
        rafId = 0
      }

      const onVisibility = () => (document.hidden ? stop() : schedule())
      document.addEventListener('visibilitychange', onVisibility)

      const io = new IntersectionObserver(([entry]) => {
        inView = entry.isIntersecting
        if (inView) schedule()
        else stop()
      })
      io.observe(el)

      const ro = new ResizeObserver(() => {
        resize()
        if (!animate) { updateLines(); renderFrame() }
      })
      ro.observe(el)

      const onReduceChange = () => {
        animate = !reduceQuery.matches
        if (animate) schedule()
        else { stop(); renderFrame() }
      }
      reduceQuery.addEventListener('change', onReduceChange)

      resize()
      updateLines()
      renderFrame()
      schedule()

      teardown = () => {
        stop()
        io.disconnect()
        ro.disconnect()
        window.removeEventListener('pointermove', onPointer)
        document.removeEventListener('visibilitychange', onVisibility)
        reduceQuery.removeEventListener('change', onReduceChange)
        pointGeo.dispose(); pointMat.dispose()
        lineGeo.dispose(); lineMat.dispose()
        outerGeo.dispose(); outerMat.dispose()
        innerGeo.dispose(); innerMat.dispose()
        renderer.dispose()
        renderer.forceContextLoss()
        renderer.domElement.remove()
      }
    }

    onMounted(() => {
      if (!webglAvailable()) {
        fallback.value = true
        return
      }
      start().catch((err) => {
        console.warn('SceneHero: 3D scene unavailable, using fallback', err)
        fallback.value = true
      })
    })

    onBeforeUnmount(() => {
      disposed = true
      if (teardown) teardown()
    })

    return { host, fallback }
  }
}
</script>

<style scoped>
.scene-hero {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  margin-bottom: var(--space-6);
  border-radius: var(--radius-lg);
  background: var(--sidebar-bg);
  color: var(--sidebar-text-strong);
}
/* Used when WebGL is missing or fails: same banner, static gradient */
.scene-hero.no-webgl {
  background:
    radial-gradient(60% 120% at 85% 50%, color-mix(in srgb, var(--color-accent) 45%, transparent), transparent 70%),
    var(--sidebar-bg);
}

.scene-host,
.scene-shade {
  position: absolute;
  inset: 0;
  z-index: 0;
}
/* Keeps the text side calm so contrast never depends on the animation */
.scene-shade {
  z-index: 1;
  background: linear-gradient(90deg, var(--sidebar-bg) 0%, color-mix(in srgb, var(--sidebar-bg) 70%, transparent) 40%, transparent 75%);
  pointer-events: none;
}

.scene-content {
  position: relative;
  z-index: 2;
  padding: var(--space-8);
  min-height: 160px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 640px;
}
.scene-content :slotted(h2) {
  margin: 0 0 var(--space-1);
  font-size: var(--text-3xl);
  line-height: var(--leading-tight);
  letter-spacing: -0.02em;
  color: var(--sidebar-text-strong);
}
.scene-content :slotted(p) {
  margin: 0;
  color: #cbd5e1; /* 11:1 on --sidebar-bg */
}

@media (max-width: 900px) {
  .scene-content { padding: var(--space-6) var(--space-4); min-height: 120px; }
}
</style>
