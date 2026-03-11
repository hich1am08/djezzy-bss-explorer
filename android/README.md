# Djezzy BSS Mobile — Android App

## Quick Start (Web Version)
```
cd site_configs
python run.py
```
Open on phone: `http://YOUR_PC_IP:5000/android/index.html`

## Build Installable APK

### Prerequisites
1. **Android Studio** — Download: https://developer.android.com/studio
2. During install, also install **Android SDK** (default option)

### Build Steps
**Option A — One-Click Script:**
```
build_apk.bat
```

**Option B — Manual:**
```
npx cap sync android
cd android
.\gradlew.bat assembleDebug
```
APK output: `android/app/build/outputs/apk/debug/app-debug.apk`

### Distribute
1. Rename the APK to `DjezzyBSS.apk`
2. Send to colleagues via WhatsApp, email, or Google Drive
3. They install it on their phone (enable "Install from unknown sources" if prompted)
4. On first launch, enter the Flask server IP: `http://YOUR_IP:5000`
5. Login with their credentials

## File Structure
```
android/
├── index.html          # Mobile web UI
├── styles.css          # Mobile CSS
├── app.js              # Mobile JS logic
├── www/                # Copy for Capacitor
├── capacitor.config.json
├── build_apk.bat       # One-click build
├── android/            # Native Android project
│   ├── app/src/main/
│   │   ├── AndroidManifest.xml
│   │   └── assets/public/  # Web assets (after sync)
│   └── gradlew.bat
├── node_modules/
└── package.json
```
