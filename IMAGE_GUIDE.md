# Image Guide for TruthMate - Fake News Detection Website

## Overview
This guide explains how to add attractive images related to fake news detection and AI throughout the website.

## Current Implementation

### ✅ What's Already Added:
1. **Animated Background Patterns**: CSS-based neural network patterns and particle effects
2. **Gradient Overlays**: Orange (#FF9900) and blue gradients suggesting AI/verification
3. **Image Placeholders**: Ready-to-replace placeholders in feature cards
4. **Hero Background Visual**: SVG-based AI neural network pattern

## Image Recommendations

### 1. Hero Section Background
**Location**: `templates/landing.html` - `.hero-bg-visual` div

**Recommended Images**:
- AI neural network visualization
- Fact-checking process diagram
- Verification shield/checkmark with AI elements
- Abstract tech pattern with orange accent

**How to Add**:
```html
<!-- Replace the .hero-bg-visual div with: -->
<div class="hero-bg-visual" style="background-image: url('/static/images/hero-ai-verification.png'); background-size: cover; background-position: center right; opacity: 0.2;"></div>
```

**Image Specs**:
- Size: 800x600px or larger
- Format: PNG with transparency or JPG
- Style: Dark theme, orange/blue accents
- Opacity: 0.15-0.25 for subtle effect

### 2. Feature Cards Images
**Location**: `templates/landing.html` - Each `.feature-image` div

**Recommended Images by Feature**:

#### Feature 1: Multi-format
- Image showing: Text, image, audio, video icons
- File: `feature-multi-format.png`
- Theme: Multiple media types with verification checkmarks

#### Feature 2: Explainable Reasoning
- Image showing: AI brain/neural network with reasoning paths
- File: `feature-ai-reasoning.png`
- Theme: Transparent AI decision-making process

#### Feature 3: User History
- Image showing: Dashboard/analytics with verification history
- File: `feature-history.png`
- Theme: Data visualization, charts, timeline

#### Feature 4: Secure
- Image showing: Shield/lock with AI verification
- File: `feature-security.png`
- Theme: Privacy protection, encrypted verification

**How to Add**:
```html
<!-- Replace placeholder with actual image -->
<div class="feature-image" style="background-image: url('/static/images/feature-multi-format.png'); background-size: cover; background-position: center;"></div>
```

**Image Specs**:
- Size: 400x180px
- Format: PNG with transparency
- Style: Dark theme, orange accent (#FF9900)
- Aspect Ratio: ~2.2:1

### 3. How It Works Page
**Location**: `templates/how_it_works.html`

**Recommended Images**:
- Step-by-step process visualization
- Pipeline diagram showing: Ingest → Extract → Cross-check → Reason → Return → Action
- File: `how-it-works-diagram.png`

**How to Add**:
```html
<!-- Add after hero-lead paragraph -->
<img src="{{ url_for('static', filename='images/how-it-works-diagram.png') }}" 
     alt="How TruthMate Works" 
     style="max-width: 100%; margin: 32px 0; border-radius: 12px; opacity: 0.9;">
```

### 4. Verify Page Background
**Location**: `templates/verify.html` - `.verify-section`

**Recommended Images**:
- Fact-checking interface mockup
- Verification process visualization
- AI analysis dashboard preview

**How to Add** (in CSS):
```css
.verify-section::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url('/static/images/verify-bg-pattern.png');
  background-size: cover;
  background-position: center;
  opacity: 0.05;
  z-index: 0;
}
```

### 5. Auth/Login Cards
**Location**: `templates/login.html`, `templates/signup.html`

**Recommended Images**:
- Secure verification badge
- Trust shield icon
- Minimal AI verification symbol

## Image Sources & Creation

### Free Image Resources:
1. **Unsplash** (https://unsplash.com)
   - Search: "AI neural network", "fact checking", "verification"
   - Filter: Dark theme, tech style

2. **Pexels** (https://pexels.com)
   - Search: "artificial intelligence", "data verification"
   - Filter: Dark backgrounds

3. **Freepik** (https://freepik.com)
   - Search: "AI verification", "fact check", "neural network"
   - Requires attribution

4. **Create Custom Images**:
   - Use Figma, Canva, or Adobe Illustrator
   - Use orange (#FF9900) as accent color
   - Dark backgrounds (#05060a, #0b0d13)
   - Add AI/verification icons and patterns

### AI Image Generation:
- **Midjourney**: "AI fact-checking system, dark theme, orange accents, neural network"
- **DALL-E**: "Professional fake news detection interface, dark UI, orange highlights"
- **Stable Diffusion**: "Verification dashboard, AI analysis, modern tech UI"

## File Structure

Create the following directory structure:
```
SatyaAI/
  static/
    images/
      hero-ai-verification.png
      feature-multi-format.png
      feature-ai-reasoning.png
      feature-history.png
      feature-security.png
      how-it-works-diagram.png
      verify-bg-pattern.png
      auth-verification-badge.png
```

## CSS Classes Available

### Background Patterns (Already Implemented):
- `.hero-bg-visual` - Hero section background
- `.feature-image` - Feature card images
- Body background with animated particles
- Card hover effects with glow

### Custom Image Classes:
```css
/* Add to styles.css if needed */
.custom-bg-image {
  background-image: url('/static/images/your-image.png');
  background-size: cover;
  background-position: center;
  opacity: 0.15;
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
```

## Best Practices

1. **File Size**: Optimize images (use TinyPNG or similar)
   - Hero images: < 200KB
   - Feature images: < 100KB
   - Background patterns: < 50KB

2. **Format**:
   - Use PNG for images with transparency
   - Use JPG for photos (smaller file size)
   - Use SVG for simple icons/patterns

3. **Dark Theme Compatibility**:
   - All images should work on dark backgrounds
   - Use subtle opacity (0.1-0.3) for backgrounds
   - Ensure text remains readable over images

4. **Responsive Design**:
   - Images should scale well on mobile
   - Use `background-size: cover` for full coverage
   - Test on different screen sizes

5. **Performance**:
   - Lazy load images below the fold
   - Use WebP format for better compression
   - Consider using CSS gradients for simple patterns

## Quick Start

1. **Create images directory**:
   ```bash
   mkdir -p SatyaAI/static/images
   ```

2. **Add your images** to `SatyaAI/static/images/`

3. **Update templates** with image paths:
   ```html
   <img src="{{ url_for('static', filename='images/your-image.png') }}" alt="Description">
   ```

4. **Update CSS** if needed for background images

5. **Test** on different devices and screen sizes

## Current Placeholder System

The website currently uses:
- SVG data URIs for neural network patterns
- CSS gradients for backgrounds
- Emoji placeholders in feature cards
- Animated particle effects

All of these can be replaced with actual images following the guide above.

## Support

For questions or issues with images:
1. Check file paths are correct
2. Ensure images are in `static/images/` directory
3. Verify Flask static file serving is configured
4. Check browser console for 404 errors

