from flask import Flask, render_template_string, request, send_file, make_response
import os
from glob import glob
import time

app = Flask(__name__)

# Base path for nnUNet results
BASE_PATH = "/work/SitselU/zhonghui-wen/nnUNet_data/nnUNet_results"

def find_folds_with_progress(base_path):
    """Find fold_X folders with progress.png."""
    search_pattern = os.path.join(base_path, "**", "fold_*", "progress.png")
    progress_files = glob(search_pattern, recursive=True)
    folds = {}
    for file in progress_files:
        fold_path = os.path.dirname(file)
        # Shorten path to just fold name
        short_name = fold_path.replace(base_path, "").lstrip("/")
        folds[short_name] = file
    return folds

def get_most_recent_progress(folds):
    """Get the most recently updated progress.png."""
    if not folds:
        return None, None
    latest_folder, latest_file = max(folds.items(), key=lambda x: os.path.getmtime(x[1]))
    return latest_folder, latest_file

@app.route("/")
def index():
    """Render the list of folds and display the selected or newest progress.png."""
    folds = find_folds_with_progress(BASE_PATH)
    selected_fold = request.args.get("fold")  # Selected fold from user
    print(f"DEBUG: Selected fold: {selected_fold}")  # Debug print for fold selection

    # Serve the selected progress file or the most recent one
    if selected_fold and selected_fold in folds:
        progress_file = folds[selected_fold]
        print(f"DEBUG: Serving progress.png from: {progress_file}")
    else:
        _, progress_file = get_most_recent_progress(folds)
        print(f"DEBUG: Serving most recent progress.png: {progress_file}")

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>nnUNet Progress Viewer</title>
        <style>
            body { display: flex; font-family: Arial, sans-serif; height: 100vh; margin: 0; }
            .sidebar { width: 30%; background-color: #f0f0f0; overflow-y: auto; padding: 10px; }
            .content { flex-grow: 1; display: flex; justify-content: center; align-items: center; background-color: #eaeaea; }
            .img-container img { max-width: 100%; max-height: 90vh; }
            h1, h2 { margin: 0; }
            button { margin: 5px; padding: 10px; background-color: #007bff; color: white; border: none; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            a { text-decoration: none; color: black; display: block; margin: 5px 0; }
            a:hover { font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2>Available Folds</h2>
            <button onclick="window.location.href='/?newest=true'">Newest Progress</button>
            <hr>
            {% for fold, path in folds.items() %}
                <a href="/?fold={{ fold }}">{{ fold }}</a>
            {% endfor %}
        </div>
        <div class="content">
            <div class="img-container">
                {% if progress_file %}
                    <img src="/view?path={{ progress_file }}&t={{ timestamp }}" alt="Progress.png">
                {% else %}
                    <h1>No progress.png available</h1>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    """, folds=folds, progress_file=progress_file, timestamp=int(time.time()))

@app.route("/view")
def view_progress():
    """Serve the selected progress.png with no caching."""
    progress_file = request.args.get("path")
    if not progress_file or not os.path.isfile(progress_file):
        print(f"DEBUG: Invalid or missing file path: {progress_file}")  # Debug invalid file
        return "progress.png not found.", 404
    
    print(f"DEBUG: Serving file: {progress_file}")  # Debug: Serving file path

    # Disable caching in the response
    response = make_response(send_file(progress_file, mimetype="image/png"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
