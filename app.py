import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageFilter, ImageEnhance, ExifTags
import time
import zipfile
import io
import uuid
import shutil


app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for flash messages

# Configure upload and compressed folders
UPLOAD_FOLDER = 'uploads'
COMPRESSED_FOLDER = 'compressed'
BATCH_FOLDER = 'batch_results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)
os.makedirs(BATCH_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['COMPRESSED_FOLDER'] = COMPRESSED_FOLDER
app.config['BATCH_FOLDER'] = BATCH_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_formatted(size_in_bytes):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} GB"

def compress_image(input_path, output_path, quality=85, resize_percentage=100, format=None, 
                  apply_filter=None, brightness=1.0, contrast=1.0, saturation=1.0,
                  remove_exif=False, resize_dimensions=None):
    """Compress and modify image using PIL/Pillow"""
    try:
        # Check if the input file exists
        if not os.path.exists(input_path):
            return {'success': False, 'error': f"Input file not found: {input_path}"}
        
        # Open the image
        img = Image.open(input_path)
        
        # Get original file size and dimensions
        original_size = os.path.getsize(input_path)
        original_width, original_height = img.size
        
        # Get and preserve EXIF data if needed
        exif_data = None
        if 'exif' in img.info and not remove_exif:
            try:
                exif_data = img.info.get('exif')
            except Exception as e:
                print(f"Warning: Could not extract EXIF data: {str(e)}")
        
        # Apply resize if specified
        if resize_percentage != 100:
            new_width = int(original_width * resize_percentage / 100)
            new_height = int(original_height * resize_percentage / 100)
            img = img.resize((new_width, new_height), Image.LANCZOS)
        elif resize_dimensions:
            try:
                width, height = map(int, resize_dimensions.split('x'))
                img = img.resize((width, height), Image.LANCZOS)
            except Exception as e:
                print(f"Warning: Could not resize to specified dimensions: {str(e)}")
        
        # Apply filters if specified
        if apply_filter:
            if apply_filter == 'blur':
                img = img.filter(ImageFilter.BLUR)
            elif apply_filter == 'sharpen':
                img = img.filter(ImageFilter.SHARPEN)
            elif apply_filter == 'contour':
                img = img.filter(ImageFilter.CONTOUR)
            elif apply_filter == 'emboss':
                img = img.filter(ImageFilter.EMBOSS)
            elif apply_filter == 'edge_enhance':
                img = img.filter(ImageFilter.EDGE_ENHANCE)
            elif apply_filter == 'smooth':
                img = img.filter(ImageFilter.SMOOTH)
            elif apply_filter == 'grayscale':
                img = img.convert('L').convert('RGB')  # Convert to grayscale
        
        # Apply enhancements
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(saturation)
        
        # Determine output format
        output_format = format.upper() if format else img.format
        
        # Handle cases where the format is JPEG but the extension is JPG
        if output_format == 'JPG':
            output_format = 'JPEG'
        
        # Set save parameters for different formats
        save_params = {}
        
        # Format-specific parameters
        if output_format == 'JPEG':
            save_params['quality'] = quality
            save_params['optimize'] = True
            if exif_data and not remove_exif:
                save_params['exif'] = exif_data
        elif output_format == 'PNG':
            save_params['optimize'] = True
        elif output_format == 'WEBP':
            save_params['quality'] = quality
        
        # Make sure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the image with the specified parameters and format
        img.save(output_path, format=output_format, **save_params)
        
        # Get compressed file size
        compressed_size = os.path.getsize(output_path)
        compressed_width, compressed_height = img.size
        
        # Calculate compression ratio
        compression_ratio = (1 - (compressed_size / original_size)) * 100
        
        return {
            'success': True,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'saved': original_size - compressed_size,
            'compression_ratio': compression_ratio,
            'original_dimensions': f"{original_width}x{original_height}",
            'compressed_dimensions': f"{compressed_width}x{compressed_height}",
            'original_size_formatted': get_file_size_formatted(original_size),
            'compressed_size_formatted': get_file_size_formatted(compressed_size),
            'saved_formatted': get_file_size_formatted(original_size - compressed_size)
        }
    except Exception as e:
        import traceback
        print(f"Error in compress_image: {str(e)}")
        print(traceback.format_exc())
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/batch')
def batch():
    return render_template('batch.html')

@app.route('/advanced')
def advanced():
    return render_template('advanced.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/compress', methods=['POST'])
def compress():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        # Secure the filename to prevent security issues
        filename = secure_filename(file.filename)
        
        # Add timestamp to ensure unique filenames
        name, ext = os.path.splitext(filename)
        timestamp = int(time.time())
        unique_filename = f"{name}_{timestamp}{ext}"
        
        # Save the original file
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(original_path)
        
        try:
            # Get parameters from form
            quality = int(request.form.get('quality', 85))
            resize_percentage = int(request.form.get('resize_percentage', 100))
            output_format = request.form.get('format', '').lower()
            apply_filter = request.form.get('filter', None)
            brightness = float(request.form.get('brightness', 1.0))
            contrast = float(request.form.get('contrast', 1.0))
            saturation = float(request.form.get('saturation', 1.0))
            remove_exif = 'remove_exif' in request.form
            resize_dimensions = request.form.get('resize_dimensions', None)
            
            # Create output filename with new extension if format changed
            if output_format and output_format != ext[1:].lower():
                compressed_filename = f"{name}_compressed_{timestamp}.{output_format}"
            else:
                compressed_filename = f"{name}_compressed_{timestamp}{ext}"
                output_format = ext[1:].lower()  # Use original format if none specified
                
            compressed_path = os.path.join(app.config['COMPRESSED_FOLDER'], compressed_filename)
            
            # Compress the image with all specified parameters
            result = compress_image(
                original_path, 
                compressed_path, 
                quality=quality,
                resize_percentage=resize_percentage,
                format=output_format,
                apply_filter=apply_filter,
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                remove_exif=remove_exif,
                resize_dimensions=resize_dimensions
            )
            
            if result['success']:
                return render_template('result.html', 
                                      original_filename=unique_filename,
                                      compressed_filename=compressed_filename,
                                      original_size=result['original_size'],
                                      compressed_size=result['compressed_size'],
                                      saved=result['saved'],
                                      compression_ratio=result['compression_ratio'],
                                      original_dimensions=result['original_dimensions'],
                                      compressed_dimensions=result['compressed_dimensions'],
                                      original_size_formatted=result['original_size_formatted'],
                                      compressed_size_formatted=result['compressed_size_formatted'],
                                      saved_formatted=result['saved_formatted'])
            else:
                flash(f"Error compressing image: {result['error']}")
                return redirect(url_for('index'))
        except Exception as e:
            # Log the error for debugging
            print(f"Error during compression: {str(e)}")
            flash(f"Error during compression: {str(e)}")
            return redirect(url_for('index'))
    
    flash('File type not allowed. Please upload a valid image file (png, jpg, jpeg, gif, webp, bmp, tiff)')
    return redirect(url_for('index'))

@app.route('/batch_compress', methods=['POST'])
def batch_compress():
    if 'files[]' not in request.files:
        return jsonify({'success': False, 'error': 'No files part'})
    
    files = request.files.getlist('files[]')
    
    if not files or files[0].filename == '':
        return jsonify({'success': False, 'error': 'No selected files'})
    
    # Create a unique batch folder
    batch_id = str(uuid.uuid4())
    batch_path = os.path.join(app.config['BATCH_FOLDER'], batch_id)
    os.makedirs(batch_path, exist_ok=True)
    
    # Get parameters from form
    quality = int(request.form.get('quality', 85))
    resize_percentage = int(request.form.get('resize_percentage', 100))
    output_format = request.form.get('format', '').lower()
    
    results = []
    valid_files = []
    
    # Process each file
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            
            # Save original
            original_path = os.path.join(batch_path, filename)
            file.save(original_path)
            
            # Determine output format and filename
            actual_output_format = output_format or ext[1:].lower()
            if actual_output_format != ext[1:].lower():
                compressed_filename = f"{name}_compressed.{actual_output_format}"
            else:
                compressed_filename = f"{name}_compressed{ext}"
                
            compressed_path = os.path.join(batch_path, compressed_filename)
            
            # Compress the image
            result = compress_image(
                original_path, 
                compressed_path, 
                quality=quality,
                resize_percentage=resize_percentage,
                format=actual_output_format
            )
            
            if result['success']:
                result['filename'] = filename
                result['compressed_filename'] = compressed_filename
                results.append(result)
                valid_files.append((compressed_filename, compressed_path))
            else:
                results.append({
                    'success': False,
                    'filename': filename,
                    'error': result['error']
                })
    
    # Create zip file if there are valid compressed files
    if valid_files:
        zip_filename = f"compressed_images_{batch_id}.zip"
        zip_path = os.path.join(batch_path, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_name, file_path in valid_files:
                zipf.write(file_path, arcname=file_name)
                
        # Return batch summary and zip download link
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'zip_filename': zip_filename,
            'total_files': len(files),
            'successful_files': len(valid_files),
            'results': results
        })
    
    return jsonify({
        'success': False,
        'error': 'No files were successfully compressed',
        'results': results
    })

@app.route('/batch_download/<batch_id>/<filename>')
def batch_download(batch_id, filename):
    batch_path = os.path.join(app.config['BATCH_FOLDER'], batch_id)
    return send_from_directory(batch_path, filename)

@app.route('/get_exif/<filename>')
def get_exif(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        img = Image.open(file_path)
        
        exif_data = {}
        if hasattr(img, '_getexif') and img._getexif() is not None:
            exif = {
                ExifTags.TAGS[k]: v
                for k, v in img._getexif().items()
                if k in ExifTags.TAGS
            }
            
            # Filter and format exif data to be more readable
            for key, value in exif.items():
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8')
                    except:
                        value = str(value)
                exif_data[key] = str(value)
        
        return jsonify(exif_data)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/compressed/<filename>')
def compressed_file(filename):
    return send_from_directory(app.config['COMPRESSED_FOLDER'], filename)

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """API endpoint to clean up old files"""
    try:
        # Define cutoff time (files older than 24 hours)
        cutoff_time = time.time() - (24 * 60 * 60)
        
        # Clean upload folder
        clean_folder(app.config['UPLOAD_FOLDER'], cutoff_time)
        
        # Clean compressed folder
        clean_folder(app.config['COMPRESSED_FOLDER'], cutoff_time)
        
        # Clean batch folder
        for batch_id in os.listdir(app.config['BATCH_FOLDER']):
            batch_path = os.path.join(app.config['BATCH_FOLDER'], batch_id)
            if os.path.isdir(batch_path):
                # Check if folder is older than cutoff
                if os.path.getmtime(batch_path) < cutoff_time:
                    shutil.rmtree(batch_path)
        
        return jsonify({"success": True, "message": "Cleanup completed successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def clean_folder(folder_path, cutoff_time):
    """Remove files older than cutoff time from folder"""
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            if os.path.getmtime(file_path) < cutoff_time:
                os.remove(file_path)

if __name__ == '__main__':
    app.run(debug=True)