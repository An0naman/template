# 🖼️ Custom Background Image Feature

## Overview

The theme system now supports custom high-resolution background images that can be displayed behind your entire application. This feature allows you to personalize your app with beautiful wallpapers, landscapes, or custom designs.

## Features

### ✨ Key Capabilities

- **Upload Custom Images**: Upload high-resolution images (PNG, JPG, JPEG, WEBP, GIF)
- **Opacity Control**: Adjust background opacity (0-100%) for readability
- **Blur Effect**: Add blur effect (0-20px) for a softer look
- **Size Options**: Cover, Contain, or Auto sizing
- **Position Control**: Center, Top, Bottom, Left, Right, and corner positions
- **Parallax Effect**: Fixed background option for scrolling effects
- **Preview**: Real-time preview of all settings changes

## How to Use

### 1. Access Background Settings

1. Navigate to **Maintenance** → **System Configuration** → **System Theme**
2. Scroll to the **Background Image** section
3. Click to expand the section

### 2. Upload a Background Image

1. Click **Enable Background Image** toggle
2. Click **Upload Background Image** or drag a file
3. Select your image file (recommended: 1920x1080 or higher resolution)
4. The image will be automatically uploaded and applied

### 3. Customize Settings

Adjust the following settings to get the perfect look:

- **Opacity**: Control transparency (50% is recommended for readability)
- **Blur**: Add blur effect for a softer appearance
- **Size**:
  - **Cover**: Fills entire screen (recommended)
  - **Contain**: Fits entire image within screen
  - **Auto**: Uses original image size
- **Position**: Choose where the image is anchored
- **Parallax**: Enable for fixed background effect when scrolling

### 4. Save Your Settings

Click **Save Theme Settings** at the bottom of the page to apply changes globally.

## Using AI to Generate Background Images

### Option 1: ChatGPT / DALL-E

1. Visit [ChatGPT](https://chat.openai.com)
2. Use prompts like:
   - "Generate a minimalist abstract wallpaper in blue and purple tones"
   - "Create a nature-inspired background with mountains and sunset"
   - "Design a geometric pattern wallpaper in dark mode colors"
3. Download the generated image
4. Upload it to the Background Image section

### Option 2: Midjourney

1. Use Discord with Midjourney bot
2. Example prompts:
   - `/imagine abstract tech wallpaper, dark blue gradient, 4k --ar 16:9`
   - `/imagine minimalist landscape, mountains, soft colors --ar 16:9`
3. Download and upload to your app

### Option 3: Other AI Services

- **Stable Diffusion** (via [DreamStudio](https://beta.dreamstudio.ai/))
- **Bing Image Creator** (free, powered by DALL-E)
- **Adobe Firefly**
- **Leonardo.ai**

### Recommended Prompts

For best results with AI image generators, use prompts like:

```
High-resolution wallpaper, [your theme], clean, modern, [colors], 
ultra detailed, 4k, suitable for application background, subtle, professional
```

Examples:
- "High-resolution wallpaper, abstract geometric patterns, blue and teal gradient, clean, modern, ultra detailed, 4k, suitable for application background, subtle, professional"
- "High-resolution wallpaper, nature landscape with mountains, sunset colors, clean, modern, warm tones, ultra detailed, 4k, suitable for application background, subtle, professional"
- "High-resolution wallpaper, minimalist tech design, dark mode, purple and pink accents, clean, modern, ultra detailed, 4k, suitable for application background, subtle, professional"

## Best Practices

### Image Selection

✅ **DO:**
- Use high-resolution images (1920x1080 or higher)
- Choose images with subtle details
- Use images that complement your theme colors
- Consider readability - keep opacity around 30-60%

❌ **DON'T:**
- Use busy or cluttered images
- Use very bright images at high opacity
- Use images with important details that will be covered by content

### Performance Tips

- **File Size**: Try to keep images under 5MB
- **Format**: WebP offers best compression for quality
- **Resolution**: 1920x1080 is sufficient for most displays
- **Color Depth**: 24-bit color is recommended

### Accessibility

- Ensure sufficient contrast between background and text
- Test with dark mode enabled/disabled
- Use blur or low opacity for better readability
- Consider users with visual impairments

## API Reference

### Upload Background Image

```bash
POST /api/upload_background
Content-Type: multipart/form-data

# Form data:
image: <file>
```

**Response:**
```json
{
  "success": true,
  "url": "/static/uploads/backgrounds/background_20250118_120000.png",
  "filename": "background_20250118_120000.png"
}
```

### Delete Background Image

```bash
DELETE /api/delete_background/<filename>
```

**Response:**
```json
{
  "success": true,
  "message": "Background image deleted"
}
```

### Save Background Settings

Background settings are saved as part of theme settings:

```bash
POST /api/theme_settings
Content-Type: application/json

{
  "background_image": {
    "enabled": true,
    "url": "/static/uploads/backgrounds/image.png",
    "opacity": 50,
    "blur": 5,
    "size": "cover",
    "position": "center",
    "parallax": true
  }
}
```

## Technical Details

### Supported Formats

- PNG (Portable Network Graphics)
- JPG/JPEG (Joint Photographic Experts Group)
- WEBP (Web Picture format) - Recommended
- GIF (Graphics Interchange Format)

### Storage Location

Background images are stored in:
```
app/static/uploads/backgrounds/
```

### CSS Implementation

The background is applied using CSS pseudo-element:

```css
body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url('...');
    background-size: cover;
    background-position: center;
    opacity: 0.5;
    z-index: -1;
}
```

## Troubleshooting

### Image Not Showing

1. Check if background is enabled
2. Verify opacity is not set to 0
3. Ensure file was uploaded successfully
4. Check browser console for errors
5. Try clearing browser cache

### Performance Issues

1. Reduce image file size
2. Convert to WebP format
3. Reduce blur amount
4. Use lower resolution image

### Readability Issues

1. Increase opacity (make image more transparent)
2. Add blur effect
3. Choose a less busy image
4. Adjust theme colors for better contrast

## Future Enhancements

Planned features for future releases:

- [ ] Multiple background images with rotation
- [ ] Gradient overlays
- [ ] Image filters (brightness, contrast, saturation)
- [ ] Time-based background changes
- [ ] Direct AI image generation integration
- [ ] Background image library/gallery
- [ ] Image cropping tool
- [ ] Animated backgrounds (GIF support)

## Feedback

Have suggestions or found a bug? Please open an issue on GitHub or contact the maintainer.

---

**Note**: The AI chatbot in the theme settings can help answer questions about background images and suggest color schemes, but cannot directly generate images. Use external AI image generation services and upload the results.
