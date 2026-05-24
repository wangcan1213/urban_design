from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory, abort
import json

app = Flask(__name__)

PROJECT_ROOT = Path("data")


def numeric_sort_key(name: str):
    first = name.split("-")[0]
    return int(first) if first.isdigit() else 9999


@app.route("/")
def home():
    projects = [
        p.name for p in PROJECT_ROOT.iterdir()
        if p.is_dir()
    ]
    return jsonify(projects)


@app.route("/<project>")
def project_page(project):
    project_dir = PROJECT_ROOT / project

    if not project_dir.exists():
        abort(404)

    return render_template("project.html", project=project)


@app.route("/api/<project>/data")
def project_data(project):
    project_dir = PROJECT_ROOT / project
    geojson_dir = project_dir / "geojsons"
    video_dir = project_dir / "videos"
    meta_path = project_dir / "meta.json"

    if not geojson_dir.exists() or not video_dir.exists():
        abort(404)

    meta = {}

    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    geojsons = {p.stem: p for p in geojson_dir.glob("*.geojson")}
    videos = {p.stem: p for p in video_dir.glob("*.mp4")}

    names = sorted(
        set(geojsons.keys()) & set(videos.keys()),
        key=numeric_sort_key
    )

    routes = []

    for name in names:
        routes.append({
            "name": name,
            "geojson": f"/media/{project}/geojsons/{name}.geojson",
            "video": f"/media/{project}/videos/{name}.mp4"
        })

    return jsonify({
        "meta": meta,
        "routes": routes
    })


@app.route("/media/<project>/<folder>/<path:filename>")
def media(project, folder, filename):
    if folder not in ["geojsons", "videos"]:
        abort(404)

    directory = PROJECT_ROOT / project / folder

    return send_from_directory(
        directory,
        filename,
        conditional=True,
        max_age=0
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)