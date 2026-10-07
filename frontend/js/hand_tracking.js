/**
 * MediaPipe Hand Tracking & Gesture Control for 3D Earth (DNA Project Engine)
 * Replaces head gestures with full hand tracking:
 * 🖐️ OPEN_PALM  : Rotate / Pan Earth in 3D
 * 🤏 PINCH      : Zoom In / Zoom Out
 * ✊ FIST       : Freeze / Lock Camera
 * 👍 THUMBS_UP  : Reset to Global Earth View
 * ✌️ PEACE      : Fly Directly to Bangladesh
 * ☝️ POINT      : Laser Raycast Pointing
 */

import { FilesetResolver, HandLandmarker } from '/static/vendor/vision_bundle.mjs';

export const HAND_CONNECTIONS = [
    [0, 1], [1, 2], [2, 3], [3, 4],       // Thumb
    [0, 5], [5, 6], [6, 7], [7, 8],       // Index
    [9, 10], [10, 11], [11, 12],          // Middle
    [13, 14], [14, 15], [15, 16],         // Ring
    [0, 17], [17, 18], [18, 19], [19, 20],// Pinky
    [5, 9], [9, 13], [13, 17]             // Knuckle bar
];

export const GESTURES = {
    NONE: 'NONE',
    OPEN_PALM: 'OPEN_PALM',
    PINCH: 'PINCH',
    FIST: 'FIST',
    THUMBS_UP: 'THUMBS_UP',
    PEACE: 'PEACE',
    POINT: 'POINT'
};

function getDistance(p1, p2) {
    const dx = p1.x - p2.x;
    const dy = p1.y - p2.y;
    return Math.hypot(dx, dy);
}

function isFingerExtended(landmarks, tipIdx, pipIdx, mcpIdx) {
    const wrist = landmarks[0];
    const tipDist = getDistance(wrist, landmarks[tipIdx]);
    const pipDist = getDistance(wrist, landmarks[pipIdx]);
    const mcpDist = getDistance(wrist, landmarks[mcpIdx]);
    return tipDist > pipDist * 1.15 && tipDist > mcpDist * 1.25;
}

function isThumbExtended(landmarks) {
    const thumbTip = landmarks[4];
    const pinkyMcp = landmarks[17];
    const indexMcp = landmarks[5];
    const wrist = landmarks[0];
    const distToPinky = getDistance(thumbTip, pinkyMcp);
    const mcpToPinky = getDistance(indexMcp, pinkyMcp);
    const distToWrist = getDistance(thumbTip, wrist);
    const thumbMcpToWrist = getDistance(landmarks[2], wrist);
    return distToPinky > mcpToPinky * 0.85 && distToWrist > thumbMcpToWrist * 1.1;
}

function isThumbsUp(landmarks) {
    const wrist = landmarks[0];
    const thumbTip = landmarks[4];
    const thumbIp = landmarks[3];

    const indexExt = isFingerExtended(landmarks, 8, 6, 5);
    const middleExt = isFingerExtended(landmarks, 12, 10, 9);
    const ringExt = isFingerExtended(landmarks, 16, 14, 13);
    const pinkyExt = isFingerExtended(landmarks, 20, 18, 17);

    if (indexExt || middleExt || ringExt || pinkyExt) return false;
    return thumbTip.y < thumbIp.y && thumbTip.y < wrist.y - 0.08;
}

export function detectHandGesture(landmarks) {
    if (!landmarks || landmarks.length < 21) {
        return { gesture: GESTURES.NONE, details: {} };
    }

    const handScale = getDistance(landmarks[0], landmarks[9]) || 0.1;
    const thumbExt = isThumbExtended(landmarks);
    const indexExt = isFingerExtended(landmarks, 8, 6, 5);
    const middleExt = isFingerExtended(landmarks, 12, 10, 9);
    const ringExt = isFingerExtended(landmarks, 16, 14, 13);
    const pinkyExt = isFingerExtended(landmarks, 20, 18, 17);

    // Palm center (mirrored x for screen coordinates)
    const palmCenter = {
        x: (landmarks[0].x + landmarks[5].x + landmarks[9].x + landmarks[13].x + landmarks[17].x) / 5,
        y: (landmarks[0].y + landmarks[5].y + landmarks[9].y + landmarks[13].y + landmarks[17].y) / 5
    };

    // 1. Thumbs Up: Reset view
    if (isThumbsUp(landmarks)) {
        return { gesture: GESTURES.THUMBS_UP, palmCenter, handScale };
    }

    // 2. Pinch (Thumb tip 4 to Index tip 8)
    const pinchDistRaw = getDistance(landmarks[4], landmarks[8]);
    const normalizedPinch = pinchDistRaw / handScale;
    if (normalizedPinch < 0.32) {
        return {
            gesture: GESTURES.PINCH,
            pinchDistance: normalizedPinch,
            pinchCenter: {
                x: (landmarks[4].x + landmarks[8].x) / 2,
                y: (landmarks[4].y + landmarks[8].y) / 2
            },
            palmCenter,
            handScale
        };
    }

    // 3. Fist (All fingers curled)
    if (!indexExt && !middleExt && !ringExt && !pinkyExt && !thumbExt) {
        return { gesture: GESTURES.FIST, palmCenter, handScale };
    }

    // 4. Peace Sign (Index & Middle extended, Ring & Pinky curled)
    if (indexExt && middleExt && !ringExt && !pinkyExt) {
        return { gesture: GESTURES.PEACE, palmCenter, handScale };
    }

    // 5. Point (Index extended, others curled)
    if (indexExt && !middleExt && !ringExt && !pinkyExt) {
        return { gesture: GESTURES.POINT, tip: landmarks[8], palmCenter, handScale };
    }

    // 6. Open Palm (All extended)
    if (indexExt && middleExt && ringExt && pinkyExt) {
        return { gesture: GESTURES.OPEN_PALM, palmCenter, handScale };
    }

    return { gesture: GESTURES.NONE, palmCenter, handScale };
}

export class MediaPipeHandController {
    constructor(viewer, cameraController) {
        this.viewer = viewer;
        this.cameraController = cameraController;
        this.handLandmarker = null;
        this.video = null;
        this.stream = null;
        this.canvas = null;
        this.ctx = null;
        this.isActive = false;
        this.animationId = null;

        // Gesture state
        this.lastPalmCenter = null;
        this.lastPinchDist = null;
        this.lastActionTime = 0;

        // DOM elements
        this.hud = document.getElementById('webcam-hud');
        this.toggleBtn = document.getElementById('btn-toggle-webcam');
        this.gestureBadge = document.getElementById('hand-gesture-badge');
        this.statusText = document.getElementById('webcam-status-text');

        this._setupListeners();
    }

    _setupListeners() {
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => {
                if (this.isActive) {
                    this.stop();
                } else {
                    this.start();
                }
            });
        }
    }

    async initModel() {
        if (this.handLandmarker) return;

        // First try local wasm and model from DNA project
        let vision;
        try {
            vision = await FilesetResolver.forVisionTasks('/static/wasm');
        } catch (e) {
            console.warn('Local WASM fallback to CDN:', e);
            vision = await FilesetResolver.forVisionTasks(
                'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm'
            );
        }

        try {
            this.handLandmarker = await HandLandmarker.createFromOptions(vision, {
                baseOptions: {
                    modelAssetPath: '/static/models/hand_landmarker.task',
                    delegate: 'GPU'
                },
                runningMode: 'VIDEO',
                numHands: 1,
                minHandDetectionConfidence: 0.55,
                minHandPresenceConfidence: 0.55,
                minTrackingConfidence: 0.55
            });
        } catch (err) {
            console.warn('Local model fallback to CDN:', err);
            this.handLandmarker = await HandLandmarker.createFromOptions(vision, {
                baseOptions: {
                    modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
                    delegate: 'GPU'
                },
                runningMode: 'VIDEO',
                numHands: 1,
                minHandDetectionConfidence: 0.55,
                minHandPresenceConfidence: 0.55,
                minTrackingConfidence: 0.55
            });
        }
        console.log('✅ MediaPipe HandLandmarker loaded successfully!');
    }

    async start() {
        try {
            if (this.statusText) this.statusText.textContent = "Loading MediaPipe Hand AI...";
            this.toggleBtn.innerHTML = '<span>⏳</span> Starting Hand AI...';

            await this.initModel();

            // Setup video element
            this.video = document.getElementById('webcam-video');
            this.canvas = document.getElementById('webcam-canvas');
            if (!this.canvas) {
                this.canvas = document.createElement('canvas');
                this.canvas.id = 'webcam-canvas';
                this.canvas.className = 'webcam-overlay-canvas';
                this.video.parentElement.appendChild(this.canvas);
            }
            this.ctx = this.canvas.getContext('2d');

            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 320, height: 240, facingMode: 'user' }
            });
            this.stream = stream;
            this.video.srcObject = stream;
            await this.video.play();

            this.canvas.width = 320;
            this.canvas.height = 240;

            this.isActive = true;
            this.hud.classList.remove('hidden');
            this.toggleBtn.classList.add('active');
            this.toggleBtn.innerHTML = '<span>⏹️</span> Stop Hand Tracking';
            if (this.statusText) this.statusText.textContent = "Show your hand to control Earth";

            this._processLoop();
        } catch (err) {
            console.error('Hand tracking error:', err);
            alert('Failed to start Hand Tracking: ' + err.message);
            this.stop();
        }
    }

    stop() {
        this.isActive = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }

        if (this.stream) {
            this.stream.getTracks().forEach(t => t.stop());
            this.stream = null;
        }

        if (this.hud) this.hud.classList.add('hidden');
        if (this.toggleBtn) {
            this.toggleBtn.classList.remove('active');
            this.toggleBtn.innerHTML = '<span>🖐️</span> Hand Tracking (DNA Mode)';
        }
        this.lastPalmCenter = null;
        this.lastPinchDist = null;
    }

    _processLoop() {
        if (!this.isActive) return;

        if (this.video && this.video.readyState >= 2) {
            const startTimeMs = performance.now();
            const results = this.handLandmarker.detectForVideo(this.video, startTimeMs);

            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            if (results && results.landmarks && results.landmarks.length > 0) {
                const landmarks = results.landmarks[0];
                this._drawHandSkeleton(landmarks);

                const gestureData = detectHandGesture(landmarks);
                this._applyGestureToEarth(gestureData);
            } else {
                if (this.gestureBadge) {
                    this.gestureBadge.textContent = "WAITING FOR HAND";
                    this.gestureBadge.className = "gesture-badge waiting";
                }
                this.lastPalmCenter = null;
                this.lastPinchDist = null;
            }
        }

        this.animationId = requestAnimationFrame(() => this._processLoop());
    }

    _drawHandSkeleton(landmarks) {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        // Draw connections (mirrored horizontally)
        ctx.strokeStyle = '#00e5ff';
        ctx.lineWidth = 2.5;
        ctx.shadowColor = '#00e5ff';
        ctx.shadowBlur = 6;

        for (const [startIdx, endIdx] of HAND_CONNECTIONS) {
            const p1 = landmarks[startIdx];
            const p2 = landmarks[endIdx];

            ctx.beginPath();
            ctx.moveTo((1 - p1.x) * w, p1.y * h);
            ctx.lineTo((1 - p2.x) * w, p2.y * h);
            ctx.stroke();
        }
        ctx.shadowBlur = 0;

        // Draw joint landmarks
        ctx.fillStyle = '#00e676';
        for (let i = 0; i < landmarks.length; i++) {
            const p = landmarks[i];
            const x = (1 - p.x) * w;
            const y = p.y * h;

            ctx.beginPath();
            ctx.arc(x, y, i === 8 || i === 4 ? 5 : 3.5, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    _applyGestureToEarth(gestureData) {
        const { gesture, palmCenter, pinchDistance } = gestureData;
        const now = performance.now();

        // Update HUD Badge
        if (this.gestureBadge) {
            let label = "NO GESTURE";
            let cssClass = "none";

            switch (gesture) {
                case GESTURES.OPEN_PALM:
                    label = "🖐️ OPEN PALM • ROTATING EARTH";
                    cssClass = "palm";
                    break;
                case GESTURES.PINCH:
                    label = "🤏 PINCH • ZOOMING";
                    cssClass = "pinch";
                    break;
                case GESTURES.FIST:
                    label = "✊ FIST • ROTATION LOCKED";
                    cssClass = "fist";
                    break;
                case GESTURES.THUMBS_UP:
                    label = "👍 THUMBS UP • RESET EARTH";
                    cssClass = "thumb";
                    break;
                case GESTURES.PEACE:
                    label = "✌️ PEACE • FLY TO BANGLADESH";
                    cssClass = "peace";
                    break;
                case GESTURES.POINT:
                    label = "☝️ POINT • INSPECTING";
                    cssClass = "point";
                    break;
            }

            this.gestureBadge.textContent = label;
            this.gestureBadge.className = `gesture-badge ${cssClass}`;
        }

        // 1. FIST: Freeze all motion
        if (gesture === GESTURES.FIST) {
            this.lastPalmCenter = null;
            this.lastPinchDist = null;
            return;
        }

        // 2. THUMBS_UP: Reset to Whole Earth View
        if (gesture === GESTURES.THUMBS_UP) {
            if (now - this.lastActionTime > 2000) {
                this.cameraController.flyTo('global');
                this.lastActionTime = now;
            }
            this.lastPalmCenter = null;
            return;
        }

        // 3. PEACE SIGN: Fly directly to Bangladesh
        if (gesture === GESTURES.PEACE) {
            if (now - this.lastActionTime > 2000) {
                this.cameraController.flyTo('bangladesh');
                this.lastActionTime = now;
            }
            this.lastPalmCenter = null;
            return;
        }

        // 4. OPEN_PALM: Rotate & Pan Earth in real-time as your hand moves
        if (gesture === GESTURES.OPEN_PALM && palmCenter) {
            if (this.lastPalmCenter) {
                // Mirrored coordinates for intuitive control
                const deltaX = -(palmCenter.x - this.lastPalmCenter.x);
                const deltaY = palmCenter.y - this.lastPalmCenter.y;

                const rotateSpeed = 2.4;

                // Move camera based on hand direction
                if (Math.abs(deltaX) > 0.003) {
                    this.viewer.camera.rotate(Cesium.Cartesian3.UNIT_Z, deltaX * rotateSpeed);
                }
                if (Math.abs(deltaY) > 0.003) {
                    this.viewer.camera.rotate(this.viewer.camera.right, deltaY * rotateSpeed * 0.7);
                }
            }
            this.lastPalmCenter = { ...palmCenter };
            this.lastPinchDist = null;
            return;
        }

        // 5. PINCH: Zoom in/out based on pinch distance delta
        if (gesture === GESTURES.PINCH && pinchDistance !== undefined) {
            if (this.lastPinchDist !== null) {
                const deltaPinch = pinchDistance - this.lastPinchDist;
                const currentHeight = this.viewer.camera.positionCartographic.height;

                if (Math.abs(deltaPinch) > 0.012) {
                    if (deltaPinch > 0) {
                        // Opening fingers = Zoom In
                        this.viewer.camera.zoomIn(currentHeight * 0.08);
                    } else {
                        // Closing fingers = Zoom Out
                        this.viewer.camera.zoomOut(currentHeight * 0.08);
                    }
                }
            }
            this.lastPinchDist = pinchDistance;
            this.lastPalmCenter = null;
            return;
        }

        this.lastPalmCenter = null;
        this.lastPinchDist = null;
    }
}

window.MediaPipeHandController = MediaPipeHandController;
