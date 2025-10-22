# Wretched Mobile Theme

A mobile-first base theme for Wretched & Alone games, optimized for touch interfaces and small screens.

## Overview

The **wretched_mobile** theme is designed specifically for mobile gameplay, prioritizing:
- **Touch-friendly interfaces** with 44px minimum touch targets
- **Single-column layout** that stacks vertically
- **Performance optimization** with minimal animations and effects
- **System fonts** for instant loading
- **High contrast** for outdoor readability
- **Full-width design** to maximize screen space

## Key Features

### 📱 Mobile-First Design
- Single-column layout (no side-by-side panels)
- Stacked components for vertical scrolling
- Full-width containers to maximize space
- Responsive card grid that adapts to screen width

### 👆 Touch-Optimized
- Minimum 44px touch targets for all interactive elements
- Large, clear buttons with generous padding (16px × 24px)
- Touch-friendly dice (60px) and cards (80px × 112px)
- Visual feedback on tap (scale animations)
- No hover effects (optimized for touch)

### ⚡ Performance
- **System fonts** instead of Google Fonts for instant loading
- **Solid colors** instead of complex gradients
- **Minimal animations** - only essential feedback
- **No textures or overlays** to reduce rendering
- **Reduced motion** support for accessibility
- **Faster animation durations** (0.2s vs 0.3s)

### 🎨 Visual Design
- **Dark theme** (#1a1a1a background) for battery life and OLED screens
- **High contrast** text (#ffffff on dark) for readability
- **Bright accent colors** (#4a9eff blue) for clear touch targets
- **Simplified borders** (1px instead of 3px)
- **Compact spacing** to fit more content on screen

### ♿ Accessibility
- High contrast mode enabled by default
- 16px minimum font size (prevents iOS zoom on input)
- Focus indicators with 3px width
- Screen reader labels
- Keyboard navigation support
- Respects `prefers-reduced-motion`

## Usage

### For New Games

```bash
# Create a new game
python3 cli/wretched.py new my-mobile-game

# Copy the mobile theme
cp templates/wretched_mobile.yaml my-mobile-game/theme.yaml

# Build
python3 cli/wretched.py build my-mobile-game
```

### For Existing Games

```bash
# Backup current theme
cp my-game/theme.yaml my-game/theme-desktop.yaml

# Use mobile theme
cp templates/wretched_mobile.yaml my-game/theme.yaml

# Build
python3 cli/wretched.py build my-game
```

### Hybrid Approach (Responsive)

You can create a theme that inherits from `wretched_mobile` and adds desktop enhancements:

```yaml
theme:
  name: "My Responsive Theme"
  base: "wretched_mobile"
  description: "Mobile-first with desktop enhancements"

  # Override for desktop
  layout:
    container_max_width: "1400px"  # Wider on desktop

  # Add desktop-specific media queries in custom_css
```

## Technical Specifications

### Layout
- **Grid**: Single column (`1fr`)
- **Max width**: `100%` (full screen)
- **Gap**: `16px`
- **Panel padding**: `16px` (vs 25px desktop)
- **Border radius**: `8px` (vs 12px desktop)

### Typography
- **Font stack**: System fonts (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto`)
- **Base size**: `1em` (16px) - prevents iOS zoom
- **H1**: `2em` (32px) - smaller than desktop
- **Line height**: `1.6` - comfortable for reading

### Touch Targets
- **Buttons**: `44px` minimum height (iOS/Android standard)
- **Dice**: `60px` × `60px`
- **Cards**: `80px` × `112px` (smaller to fit more on screen)
- **Close buttons**: `44px` × `44px`
- **Tab buttons**: `44px` height, `120px` min width

### Colors
- **Background**: `#1a1a1a` (dark)
- **Panels**: `#2a2a2a`
- **Borders**: `#444444`
- **Accent**: `#4a9eff` (bright blue)
- **Text**: `#ffffff` (white)
- **Success**: `#4ade80` (green)
- **Warning**: `#fbbf24` (amber)
- **Danger**: `#ef4444` (red)

### Performance Optimizations
```css
/* Prevent text size adjustment */
-webkit-text-size-adjust: 100%;

/* Smooth scrolling */
-webkit-overflow-scrolling: touch;

/* Disable tap highlight */
-webkit-tap-highlight-color: rgba(74, 158, 255, 0.2);

/* Optimize touch actions */
touch-action: manipulation;
```

## Customization

### Adjusting Touch Target Sizes

If you need larger/smaller targets:

```yaml
components:
  buttons:
    padding: "20px 30px"  # Larger

  dice:
    size: "70px"  # Bigger dice
```

### Changing Colors

The mobile theme uses a dark palette by default:

```yaml
colors:
  primary: "#1a1a1a"     # Background
  accent_primary: "#4a9eff"  # Interactive elements
```

For a light theme:

```yaml
colors:
  primary: "#ffffff"
  secondary: "#f5f5f5"
  text_primary: "#1a1a1a"
  accent_primary: "#2563eb"
```

### Adding Desktop Enhancements

Use media queries in `custom_css`:

```yaml
custom_css: |
  /* Mobile first (already defined) */

  /* Desktop enhancements */
  @media (min-width: 1024px) {
    .game-panel {
      display: grid;
      grid-template-columns: 400px 1fr;
      gap: 24px;
    }

    .container {
      max-width: 1400px;
      margin: 0 auto;
    }
  }
```

## Best Practices

### DO ✅
- **Test on real devices** - emulators don't capture touch behavior perfectly
- **Use system fonts** - they load instantly and look native
- **Keep touch targets ≥44px** - iOS and Android guidelines
- **Minimize animations** - they drain battery and can lag
- **Use high contrast** - important for outdoor play
- **Test in portrait and landscape** - both orientations should work

### DON'T ❌
- **Don't use hover effects** - they don't work on touch
- **Don't use tiny fonts** - minimum 16px for body text
- **Don't rely on complex gradients** - they impact performance
- **Don't use external fonts** - they slow load time
- **Don't forget to disable zoom on inputs** - `font-size: 16px !important`
- **Don't overcrowd the screen** - mobile users scroll easily

## Mobile vs Desktop Comparison

| Feature | Desktop Theme | Mobile Theme |
|---------|--------------|--------------|
| Layout | 2-column grid | Single column stack |
| Touch targets | 12-15px padding | 16-24px padding (44px min) |
| Fonts | Google Fonts | System fonts |
| Font size | 1.1em (17.6px) | 1em (16px) |
| Animations | Full effects | Minimal |
| Panel padding | 25px | 16px |
| Border width | 3px | 1px |
| Dice size | 80px | 60px |
| Card size | 100px × 140px | 80px × 112px |
| Background | Gradients + overlays | Solid colors |

## Testing

### Testing Checklist

- [ ] Test on iPhone (Safari)
- [ ] Test on Android (Chrome)
- [ ] Test in portrait orientation
- [ ] Test in landscape orientation
- [ ] Test with large text size (accessibility)
- [ ] Test with reduced motion enabled
- [ ] Verify no horizontal scrolling
- [ ] Check all buttons are easily tappable
- [ ] Ensure text is readable in bright sunlight
- [ ] Verify cards can be easily selected
- [ ] Check modal dialogs work properly
- [ ] Test journal typing and scrolling

### Browser DevTools Testing

1. Open Chrome DevTools
2. Click device toggle (Ctrl/Cmd + Shift + M)
3. Select a mobile device (iPhone 12, Galaxy S21, etc.)
4. Test in both portrait and landscape
5. Throttle network to "Fast 3G" to test loading
6. Enable "Show media queries" to see breakpoints

### Real Device Testing

Use browser developer tools remote debugging:

**iOS (Safari)**:
1. Enable Web Inspector on device (Settings > Safari > Advanced)
2. Connect device to Mac
3. Open Safari > Develop > [Your Device]

**Android (Chrome)**:
1. Enable Developer Options and USB Debugging
2. Connect device to computer
3. Open chrome://inspect in desktop Chrome
4. Click "Inspect" on your device

## Known Limitations

1. **No advanced typography** - System fonts only (no custom fonts)
2. **Simplified styling** - Minimal gradients and effects
3. **Single column layout** - No side-by-side panels
4. **Reduced animations** - Less visual polish
5. **Dark theme only** - Light theme requires customization

These are intentional tradeoffs for better mobile performance.

## Performance Metrics

Target metrics for mobile theme:

- **Initial load**: <1 second on 4G
- **Time to interactive**: <2 seconds
- **File size**: <100KB (HTML + CSS + JS)
- **Lighthouse score**: >90 on mobile
- **Frame rate**: 60fps for animations

## Future Enhancements

Potential improvements for future versions:

- [ ] PWA (Progressive Web App) support
- [ ] Offline mode with Service Worker
- [ ] Haptic feedback on interactions
- [ ] Voice input for journal
- [ ] Dark/light theme toggle
- [ ] Font size adjustment controls
- [ ] Swipe gestures for card navigation
- [ ] Native app wrapper (Capacitor/Cordova)

## Examples

### Games Well-Suited for Mobile Theme

- **Quick play sessions** - Games designed for 15-30 minute sessions
- **Commute games** - Play during travel
- **Outdoor games** - High contrast helps in sunlight
- **Casual audiences** - Mobile-first players
- **Accessibility focus** - Vision or motor impairments

### Games That May Need Desktop Theme

- **Complex mechanics** - Require multiple panels visible
- **Heavy reading** - Long story text more comfortable on desktop
- **Reference-heavy** - Need card reference open while playing
- **Multi-hour sessions** - Desktop ergonomics better for long play

## Support

### Troubleshooting

**Text too small on iOS:**
```css
/* Ensure minimum 16px font size */
body { font-size: 16px; }
input, textarea { font-size: 16px !important; }
```

**Buttons hard to tap:**
```css
/* Increase touch target */
button {
  min-height: 44px;
  min-width: 44px;
  padding: 16px 24px;
}
```

**Lag on animations:**
```yaml
animations:
  enabled: false  # Disable entirely
```

**Horizontal scrolling issue:**
```css
body, html {
  overflow-x: hidden;
  max-width: 100vw;
}
```

## Credits

**Design Principles:**
- iOS Human Interface Guidelines
- Material Design Touch Target Guidelines
- Web Content Accessibility Guidelines (WCAG)

**Created for:**
- Wretched & Alone Game Generator
- Mobile-first solo RPG experiences

## License

This theme is part of the Wretched & Alone Game Generator and can be freely used and modified for your games.

---

**Ready to build mobile-first?**

```bash
cp templates/wretched_mobile.yaml my-game/theme.yaml
python3 cli/wretched.py build my-game
```

Happy mobile gaming! 📱🎲
