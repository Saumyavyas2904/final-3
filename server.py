from flask import Flask, request, jsonify, render_template_string, send_from_directory
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
            return render_template_string(HTML_TEMPLATE, image_url=f"/static/uploads/{unique_filename}")

    return render_template_string(HTML_TEMPLATE, image_url="")

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
            "viewer_url": f"{request.host_url}viewer/{unique_filename}",
            "direct_url": f"{request.host_url}static/uploads/{unique_filename}"
        }), 200

    return jsonify({"error": "Invalid file type"}), 400

@app.route('/viewer/<filename>')
def viewer_page(filename):
    image_url = f"/static/uploads/{filename}"
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

    return {"message": "Image processed successfully", "url": f"/static/uploads/{output_filename}"}

HTML_TEMPLATE = """
<!DOCTYPE html> 
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, shrink-to-fit=no">
    <title>360° Scrollable Panorama</title>
    <style>
        * {
            touch-action: none;
            box-sizing: border-box;
        }
        body { 
            margin: 0; 
            overflow: hidden; 
            width: 100vw;
            height: 100vh;
        }
        canvas { 
            width: 100% !important;
            height: 100% !important;
        }
        .upload-form { 
            position: absolute; 
            z-index: 10; 
            padding: 10px; 
            background: rgba(0,0,0,0.5); 
            width: 100%;
            max-width: 400px;
            left: 50%;
            transform: translateX(-50%);
            text-align: center;
        }
        .upload-form input[type="file"] {
            width: 100%;
            margin-bottom: 10px;
        }
        .upload-form button {
            width: 100%;
            padding: 12px;
            background: #2c3e50;
            color: white;
            border: none;
            border-radius: 5px;
        }
        .controls {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 20;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 5px;
            max-width: 95%;
        }
        .controls button {
            background: linear-gradient(145deg, #2c3e50, #34495e);
            color: white;
            border: none;
            padding: 12px;
            margin: 0;
            font-size: 16px;
            cursor: pointer;
            border-radius: 8px;
            box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3);
            flex: 1 1 auto;
            min-width: 60px;
        }
        @media (min-width: 768px) {
            .controls button {
                padding: 15px;
                font-size: 18px;
                min-width: 80px;
            }
        }
        @media (max-width: 480px) {
            .controls {
                bottom: 10px;
                gap: 3px;
            }
            .controls button {
                padding: 10px;
                font-size: 14px;
                min-width: 50px;
            }
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    {% if not image_url %}
    <form action="/" method="post" enctype="multipart/form-data" class="upload-form">
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
        let moveSpeed = 0.5;
        let zoomSpeed = 1.0;
        let rotationSpeed = 0.005;
        let verticalSpeed = 0.5;
        let keys = {};
        let isDragging = false;
        let previousMousePosition = { x: 0, y: 0 };
        let previousTouchPosition = { x: 0, y: 0 };

        function init() {
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0xFFFFFF);

            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 0, 0);

            renderer = new THREE.WebGLRenderer({ 
                antialias: true,
                powerPreference: "high-performance"
            });
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);

            const textureLoader = new THREE.TextureLoader();
            textureLoader.load("{{ image_url }}", function(texture) {
                texture.wrapS = THREE.RepeatWrapping;
                texture.repeat.x = -1;

                const geometry = new THREE.SphereGeometry(500, 60, 40);
                const material = new THREE.MeshBasicMaterial({ 
                    map: texture, 
                    side: THREE.BackSide 
                });
                sphere = new THREE.Mesh(geometry, material);
                scene.add(sphere);

                animate();
            });

            window.addEventListener('resize', onWindowResize, false);
            
            document.addEventListener('keydown', (event) => { 
                keys[event.key.toLowerCase()] = true; 
            });
            document.addEventListener('keyup', (event) => { 
                keys[event.key.toLowerCase()] = false; 
            });

            document.addEventListener('mousedown', (event) => {
                isDragging = true;
                previousMousePosition = { 
                    x: event.clientX, 
                    y: event.clientY 
                };
            });

            document.addEventListener('mousemove', (event) => {
                if (isDragging) {
                    handleMovement(event.clientX, event.clientY);
                }
            });

            document.addEventListener('mouseup', () => { 
                isDragging = false; 
            });

            document.addEventListener('touchstart', (event) => {
                if (event.touches.length === 1) {
                    previousTouchPosition = {
                        x: event.touches[0].clientX,
                        y: event.touches[0].clientY
                    };
                }
            }, { passive: false });

            document.addEventListener('touchmove', (event) => {
                if (event.touches.length === 1) {
                    handleMovement(
                        event.touches[0].clientX,
                        event.touches[0].clientY
                    );
                    previousTouchPosition = {
                        x: event.touches[0].clientX,
                        y: event.touches[0].clientY
                    };
                }
                event.preventDefault();
            }, { passive: false });

            document.querySelector(".controls").style.display = "flex";
        }

        function handleMovement(x, y) {
            let deltaX = x - previousMousePosition.x;
            let deltaY = y - previousMousePosition.y;

            sphere.rotation.y += deltaX * rotationSpeed;
            sphere.rotation.x += deltaY * rotationSpeed;
            previousMousePosition = { x, y };
        }

        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }

        function startMoving(key) { keys[key] = true; }
        function stopMoving(key) { keys[key] = false; }

        function updateMovement() {
            let direction = new THREE.Vector3();
            camera.getWorldDirection(direction);

            if (keys['w']) camera.position.addScaledVector(direction, moveSpeed);
            if (keys['s']) camera.position.addScaledVector(direction, -moveSpeed);

            if (keys['a'] || keys['arrowleft']) sphere.rotation.y += rotationSpeed;
            if (keys['d'] || keys['arrowright']) sphere.rotation.y -= rotationSpeed;

            if (keys['arrowup']) camera.position.y += verticalSpeed;
            if (keys['arrowdown']) camera.position.y -= verticalSpeed;

            if (keys['+']) camera.fov = Math.max(30, camera.fov - zoomSpeed);
            if (keys['-']) camera.fov = Math.min(100, camera.fov + zoomSpeed);

            camera.updateProjectionMatrix();
        }

        function animate() {
            requestAnimationFrame(animate);
            updateMovement();
            renderer.render(scene, camera);
        }

        init();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)