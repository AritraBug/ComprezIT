# Image Compressor

## Overview
This is a Flask-based web application that allows users to compress images with adjustable quality, resizing, and optional filters. The app supports batch compression, EXIF data removal, and multiple image formats, making it a versatile tool for optimizing images for web use and storage efficiency.

## Features
- **Single & Batch Image Compression**: Compress individual images or multiple images at once.
- **Quality Control**: Adjust the compression quality of images.
- **Resize Options**: Resize images by percentage or specific dimensions.
- **Format Conversion**: Convert images to different formats (JPEG, PNG, WEBP, etc.).
- **Filters & Enhancements**: Apply blur, sharpen, contour, emboss, and other filters.
- **EXIF Data Handling**: Option to retain or remove metadata from images.
- **Auto Cleanup**: Automatically deletes old files after 24 hours to save space.

## Installation
### Prerequisites
Ensure you have Python installed (>=3.7) along with `pip`.

### Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/image-compressor.git
   cd image-compressor
   ```
2. Create a virtual environment (optional but recommended):
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Run the application:
   ```sh
   python app.py
   ```
5. Open your browser and go to:
   ```sh
   http://127.0.0.1:5000/
   ```

## API Endpoints
| Endpoint                   | Method | Description |
|----------------------------|--------|-------------|
| `/`                        | GET    | Home Page |
| `/compress`                | POST   | Compress an uploaded image |
| `/batch_compress`          | POST   | Compress multiple images in batch mode |
| `/batch_download/<batch_id>/<filename>` | GET | Download compressed images in batch |
| `/get_exif/<filename>`      | GET    | Retrieve EXIF metadata of an image |
| `/uploads/<filename>`      | GET    | View the uploaded image |
| `/compressed/<filename>`   | GET    | View/download compressed image |
| `/cleanup`                 | POST   | Clean old files (older than 24 hours) |

## Configuration
- The application stores images in:
  - `uploads/` (Original images)
  - `compressed/` (Compressed images)
  - `batch_results/` (Batch compression results)
- Change maximum upload size in `app.py`:
  ```python
  app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload size
  ```

## Contributing
Feel free to fork the repository and submit pull requests with improvements or new features.

## License
This project is licensed under the MIT License. See `LICENSE` for details.

## Contact
For any questions or support, contact: info.aritrasarkhel@gmail.com

