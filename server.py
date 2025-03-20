from flask import Flask, request, jsonify, render_template_string, send_from_directory, url_for
from flask_cors import CORS
import os
import shutil
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":    
        if "file" not in request.files:
            return "No file part" 

        file = request.files["file"]
        if file.filename == "":
            return "No selected file"

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{datetime.now().timestamp()}_{filename}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
            file.save(filepath)
            return render_template_string(HTML_TEMPLATE, image_url=url_for('uploaded_file', filename=unique_filename))

    return render_template_string(HTML_TEMPLATE, image_url=None)

@app.route("/api/upload", methods=["POST"])
def api_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().timestamp()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        return jsonify({
            "message": "File uploaded successfully",
            "viewer_url": url_for('viewer_page', filename=unique_filename, _external=True),
            "direct_url": url_for('uploaded_file', filename=unique_filename, _external=True)
        }), 200

    return jsonify({"error": "Invalid file type"}), 400

@app.route('/viewer/<filename>')
def viewer_page(filename):
    image_url = url_for('uploaded_file', filename=filename)
    return render_template_string(HTML_TEMPLATE, image_url=image_url)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/process_stitched_image', methods=["POST"])
def process_stitched_image():
    if "filepath" not in request.json:
        return {"error": "Filepath is required"}, 400

    input_path = request.json["filepath"]
    if not os.path.exists(input_path):
        return {"error": "File does not exist"}, 404

    output_filename = "stitched_latest.jpg"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    shutil.copy(input_path, output_path)

    return {"message": "Image processed successfully", "url": url_for('uploaded_file', filename=output_filename)}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, shrink-to-fit=no">
    <title>360° Scrollable Panorama</title>
    <style>
        * { touch-action: none; box-sizing: border-box; }
        body { margin: 0; overflow: hidden; width: 100vw; height: 100vh; }
        canvas { width: 100% !important; height: 100% !important; }
        .upload-form { 
            position: absolute; z-index: 10; padding: 10px; 
            background: rgba(0,0,0,0.5); width: 100%; max-width: 400px;
            left: 50%; transform: translateX(-50%); text-align: center;
        }
        .upload-form input[type="file"] { width: 100%; margin-bottom: 10px; }
        .upload-form button {
            width: 100%; padding: 12px; background: #2c3e50; 
            color: white; border: none; border-radius: 5px;
        }
        .controls {
            position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
            z-index: 20; display: flex; flex-wrap: wrap; justify-content: center;
            gap: 5px; max-width: 95%;
        }
        .controls button {
            background: linear-gradient(145deg, #2c3e50, #34495e); color: white;
            border: none; padding: 12px; margin: 0; font-size: 16px; cursor: pointer;
            border-radius: 8px; box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3);
            flex: 1 1 auto; min-width: 60px;
        }
        @media (min-width: 768px) { .controls button { padding: 15px; font-size: 18px; min-width: 80px; } }
        @media (max-width: 480px) { 
            .controls { bottom: 10px; gap: 3px; }
            .controls button { padding: 10px; font-size: 14px; min-width: 50px; }
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    {% if not image_url %}
    <form class="upload-form" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept="image/*">
        <button type="submit">Upload</button>
    </form>
    {% endif %}

    {% if image_url %}
    <div class="controls">
        <button ontouchstart="startMoving('w')" ontouchend="stopMoving('w')" onmousedown="startMoving('w')" onmouseup="stopMoving('w')">↑</button>
        <button ontouchstart="startMoving('a')" ontouchend="stopMoving('a')" onmousedown="startMoving('a')" onmouseup="stopMoving('a')">←</button>
        <button ontouchstart="startMoving('s')" ontouchend="stopMoving('s')" onmousedown="startMoving('s')" onmouseup="stopMoving('s')">↓</button>
        <button ontouchstart="startMoving('d')" ontouchend="stopMoving('d')" onmousedown="startMoving('d')" onmouseup="stopMoving('d')">→</button>
        <button ontouchstart="startMoving('arrowup')" ontouchend="stopMoving('arrowup')" onmousedown="startMoving('arrowup')" onmouseup="stopMoving('arrowup')">⤒</button>
        <button ontouchstart="startMoving('arrowdown')" ontouchend="stopMoving('arrowdown')" onmousedown="startMoving('arrowdown')" onmouseup="stopMoving('arrowdown')">⤓</button>
        <button ontouchstart="startMoving('+')" ontouchend="stopMoving('+')" onmousedown="startMoving('+')" onmouseup="stopMoving('+')">+</button>
        <button ontouchstart="startMoving('-')" ontouchend="stopMoving('-')" onmousedown="startMoving('-')" onmouseup="stopMoving('-')">-</button>
    </div>
    {% endif %}

    <script>
        let scene, camera, renderer, sphere;
        let moveSpeed = 0.5, zoomSpeed = 1.0, rotationSpeed = 0.005, verticalSpeed = 0.5;
        let keys = {}, isDragging = false, previousMousePosition = { x: 0, y: 0 };

        function init() {
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
            renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);

            new THREE.TextureLoader().load("{{ image_url }}", texture => {
                texture.wrapS = THREE.RepeatWrapping;
                texture.repeat.x = -1;
                sphere = new THREE.Mesh(
                    new THREE.SphereGeometry(500, 60, 40),
                    new THREE.MeshBasicMaterial({ map: texture, side: THREE.BackSide })
                );
                scene.add(sphere);
                animate();
            });

            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });

            // Event listeners for controls
            document.addEventListener('keydown', e => keys[e.key.toLowerCase()] = true);
            document.addEventListener('keyup', e => keys[e.key.toLowerCase()] = false);
            document.addEventListener('mousedown', e => {
                isDragging = true;
                previousMousePosition = { x: e.clientX, y: e.clientY };
            });
            document.addEventListener('mousemove', e => {
                if (!isDragging) return;
                const deltaX = e.clientX - previousMousePosition.x;
                const deltaY = e.clientY - previousMousePosition.y;
                sphere.rotation.y += deltaX * rotationSpeed;
                sphere.rotation.x += deltaY * rotationSpeed;
                previousMousePosition = { x: e.clientX, y: e.clientY };
            });
            document.addEventListener('mouseup', () => isDragging = false);
        }

        function animate() {
            requestAnimationFrame(animate);
            const direction = new THREE.Vector3();
            camera.getWorldDirection(direction);
            
            if (keys['w']) camera.position.addScaledVector(direction, moveSpeed);
            if (keys['s']) camera.position.addScaledVector(direction, -moveSpeed);
            if (keys['a']) sphere.rotation.y += rotationSpeed;
            if (keys['d']) sphere.rotation.y -= rotationSpeed;
            if (keys['arrowup']) camera.position.y += verticalSpeed;
            if (keys['arrowdown']) camera.position.y -= verticalSpeed;
            if (keys['+']) camera.fov = Math.max(30, camera.fov - zoomSpeed);
            if (keys['-']) camera.fov = Math.min(100, camera.fov + zoomSpeed);
            
            camera.updateProjectionMatrix();
            renderer.render(scene, camera);
        }

        function startMoving(key) { keys[key] = true; }
        function stopMoving(key) { keys[key] = false; }
        
        init();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
