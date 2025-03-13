import React from 'react';
import './ImageExample.css';
// Import an image from the assets directory
// Note: You'll need to replace this with an actual image file
import assetImage from '../assets/images/placeholder.txt';

/**
 * Example component demonstrating how to use images from both the public directory
 * and the assets directory
 */
const ImageExample: React.FC = () => {
    return (
        <div className="image-example">
            <h2>Image Usage Examples</h2>

            <div className="example-section">
                <h3>Images from public directory</h3>
                <p>
                    Images in the public directory are served as static files and referenced with absolute paths:
                </p>
                <div className="image-container">
                    {/* This references an image from the public directory */}
                    <img
                        src="/images/ui/example.jpg"
                        alt="Example from public directory"
                        className="public-image"
                    />
                    <p className="caption">
                        <code>src="/images/ui/example.jpg"</code>
                    </p>
                </div>
            </div>

            <div className="example-section">
                <h3>Images from assets directory</h3>
                <p>
                    Images in the assets directory are imported and processed by the build system:
                </p>
                <div className="image-container">
                    {/* This uses an imported image from the assets directory */}
                    <img
                        src={assetImage}
                        alt="Example from assets directory"
                        className="asset-image"
                    />
                    <p className="caption">
                        <code>import assetImage from '../assets/images/example.jpg';</code>
                    </p>
                </div>
            </div>

            <div className="notes">
                <h3>When to use each approach:</h3>
                <ul>
                    <li>
                        <strong>Public directory:</strong> For static images that don't need processing,
                        images referenced in CSS, or images that need direct URL access.
                    </li>
                    <li>
                        <strong>Assets directory:</strong> For images that should be optimized during build,
                        smaller UI elements, or images imported directly in components.
                    </li>
                </ul>
            </div>
        </div>
    );
};

export default ImageExample; 