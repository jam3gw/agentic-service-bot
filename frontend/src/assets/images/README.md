# Assets Images Directory

This directory contains image assets that will be processed by the build system (Vite) during the build process.

## Usage

Images placed in this directory should be imported in your components:

```tsx
// In a React component
import logoImage from '@/assets/images/logo.png';

function Logo() {
  return <img src={logoImage} alt="Logo" />;
}
```

## When to use this directory

- For images that need to be optimized during build
- For smaller UI elements and icons
- For images that are imported directly in your code
- For images that might change based on build configuration

## Advantages

- Images are optimized during build
- Automatic hashing for cache busting
- TypeScript support with proper typing
- Tree-shaking (unused images won't be included in the build)
- Can be processed with plugins (e.g., SVG to React components) 