# Public Images Directory

This directory contains static image assets that are served directly by the web server without being processed by the build system.

## Usage

Images placed in this directory can be referenced in your HTML or CSS using absolute paths:

```html
<!-- In HTML -->
<img src="/images/logo.png" alt="Logo" />
```

```css
/* In CSS */
.background {
  background-image: url('/images/background.jpg');
}
```

## When to use this directory

- For larger images that don't need processing
- For images that need to be accessible via direct URL
- For images referenced in public HTML files
- For favicon and other browser-specific images

## Subdirectories

- `/images/ui/` - UI elements like buttons, icons, and decorative elements 