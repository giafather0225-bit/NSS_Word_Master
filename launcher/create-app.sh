#!/bin/bash
# ═══════════════════════════════════════════
# GIA.app Bundle Creator
# Usage: bash launcher/create-app.sh
# Result: ~/Desktop/GIA.app
# ═══════════════════════════════════════════

APP_DIR="$HOME/Documents/GitHub/NSS_Word_Master"
APP_NAME="GIA"
APP_PATH="$HOME/Desktop/$APP_NAME.app"
ICON_SOURCE="$APP_DIR/frontend/static/img/GIA_512.png"

echo "🔨 Creating $APP_NAME.app..."

# Remove existing app
rm -rf "$APP_PATH"

# Create .app bundle structure
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Info.plist
cat > "$APP_PATH/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleName</key>
    <string>GIA</string>
    <key>CFBundleDisplayName</key>
    <string>GIA Learning</string>
    <key>CFBundleIdentifier</key>
    <string>com.gia.learning</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# Executable script
cat > "$APP_PATH/Contents/MacOS/launch" << SCRIPT
#!/bin/bash
exec "$APP_DIR/launcher/gia-launch.sh"
SCRIPT
chmod +x "$APP_PATH/Contents/MacOS/launch"

# Icon: PNG → ICNS
if [ -f "$ICON_SOURCE" ]; then
  ICONSET_DIR=$(mktemp -d)/GIA.iconset
  mkdir -p "$ICONSET_DIR"

  sips -z 16 16     "$ICON_SOURCE" --out "$ICONSET_DIR/icon_16x16.png"      2>/dev/null
  sips -z 32 32     "$ICON_SOURCE" --out "$ICONSET_DIR/icon_16x16@2x.png"   2>/dev/null
  sips -z 32 32     "$ICON_SOURCE" --out "$ICONSET_DIR/icon_32x32.png"      2>/dev/null
  sips -z 64 64     "$ICON_SOURCE" --out "$ICONSET_DIR/icon_32x32@2x.png"   2>/dev/null
  sips -z 128 128   "$ICON_SOURCE" --out "$ICONSET_DIR/icon_128x128.png"    2>/dev/null
  sips -z 256 256   "$ICON_SOURCE" --out "$ICONSET_DIR/icon_128x128@2x.png" 2>/dev/null
  sips -z 256 256   "$ICON_SOURCE" --out "$ICONSET_DIR/icon_256x256.png"    2>/dev/null
  sips -z 512 512   "$ICON_SOURCE" --out "$ICONSET_DIR/icon_256x256@2x.png" 2>/dev/null
  sips -z 512 512   "$ICON_SOURCE" --out "$ICONSET_DIR/icon_512x512.png"    2>/dev/null
  sips -z 1024 1024 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_512x512@2x.png" 2>/dev/null

  iconutil -c icns "$ICONSET_DIR" -o "$APP_PATH/Contents/Resources/AppIcon.icns" 2>/dev/null

  if [ $? -eq 0 ]; then
    echo "✅ App icon created from GIA_Logo.png"
  else
    echo "⚠️ Icon conversion failed. App will use default icon."
  fi

  rm -rf "$(dirname "$ICONSET_DIR")"
else
  echo "⚠️ GIA_Logo.png not found. App will use default icon."
fi

echo ""
echo "✅ $APP_NAME.app created at ~/Desktop/"
echo ""
echo "📋 Next steps:"
echo "   1. Double-click GIA.app on your Desktop"
echo "   2. If macOS blocks it: System Settings → Privacy → Open Anyway"
echo "   3. Optionally drag GIA.app to your Dock"
echo ""
echo "💡 To stop the server: $APP_DIR/launcher/gia-stop.sh"
