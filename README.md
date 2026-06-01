# Gesture Media Controller🎵🖐️⚡

An advanced human-computer interaction (HCI) interface that bridges computer vision with native OS media endpoints. Built using Python, OpenCV, and the modern Google MediaPipe Tasks API, this engine provides seamless, perspective-immune, and accidental-trigger-proof control over Spotify, YouTube, or any active media source on Windows.

### 🎮 Controlled Layout & Mechanics:
* 🫰 **The Finger Snap (Thumb + Middle Touch):** Instant Play / Pause toggle.
* ⏩ **Two-Finger Pointer Right (Index + Middle Tight Grouping):** Skip to Next Track.
* ⏪ **Two-Finger Pointer Left (Index + Middle Tight Grouping):** Skip to Previous Track.
* 🔊 **Gun Reticle Up (Thumb Extended + Index Up):** Continuously ramp up master volume.
* 🔉 **Gun Reticle Down (Thumb Extended + Index Down):** Continuously ramp down master volume.

---

### 🚀 Advanced Engineering Upgrades

#### 📐 1. Perspective-Immune Angle Tracking (`math.atan2`)
Basic coordinate tracking fails when a hand tilts or moves away from a flat 2D webcam plane due to foreshortening distortions. To fix this, this architecture discards unstable pixel-distance metrics. Instead, it utilizes Arc Tangent trigonometry to map the exact **geometric slope angles** of the index finger bone relative to the horizon. This keeps tracking completely locked in, regardless of hand orientation or distance from the camera lens.

#### 🛡️ 2. Multi-Frame Hold Validation (Anti-Glitch Engine)
Rapid transitions (like executing a finger snap) cause the hand to briefly pass through intermediate states that mimic other gestures. To prevent accidental song skips, the engine enforces a strict **Validation Hold Buffer**. Commands require a deliberate, consecutive frame hold threshold (e.g., 4 consecutive frames or ~0.13s for track skips) before firing keyboard inputs. If a shape breaks for even a single frame during transition, its counter instantly resets to zero.

#### 🛑 3. Rest-Safe Ergonomics (Zero "Midas Touch" Triggers)
Traditional vision apps suffer from accidental triggers during resting hand postures. This control deck maps operations exclusively to complex, non-standard hand shapes that do not occur during natural hand rest intervals. You can casually rest your chin on your hand, gesture while speaking, or leave your hand open in front of the lens without triggering system overrides.

---

### 📦 Prerequisites & Local Initialization

1. Place the `hand_landmarker.task` file inside your root project folder.
2. Install the necessary system emulation and math dependencies via command line:
```bash
pip install opencv-python mediapipe pynput numpy
