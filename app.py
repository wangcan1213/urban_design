from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory, abort

app = Flask(__name__)

DATA_ROOT = Path("data")


def numeric_sort_key(path: Path):
    stem = path.stem
    first = stem.split("-")[0]
    return int(first) if first.isdigit() else 9999


@app.route("/")
def index():
    return render_template("preview.html")


@app.route("/api/projects")
def get_projects():
    projects = [
        p.name for p in DATA_ROOT.iterdir()
        if p.is_dir()
    ]
    return jsonify(projects)


@app.route("/api/<project>/routes")
def get_routes(project):
    project_dir = DATA_ROOT / project
    geojson_dir = project_dir / "geojsons"
    video_dir = project_dir / "videos"

    if not geojson_dir.exists() or not video_dir.exists():
        abort(404)

    geojsons = {p.stem: p for p in geojson_dir.glob("*.geojson")}
    videos = {p.stem: p for p in video_dir.glob("*.mp4")}

    names = sorted(
        set(geojsons.keys()) & set(videos.keys()),
        key=lambda x: numeric_sort_key(Path(x))
    )

    routes = []
    for name in names:
        routes.append({
            "name": name,
            "geojson": f"/media/{project}/geojsons/{name}.geojson",
            "video": f"/media/{project}/videos/{name}.mp4"
        })

    return jsonify(routes)


@app.route("/media/<project>/<folder>/<path:filename>")
def media(project, folder, filename):
    if folder not in ["geojsons", "videos"]:
        abort(404)

    directory = DATA_ROOT / project / folder

    return send_from_directory(
        directory,
        filename,
        conditional=True
    )


if __name__ == "__main__":
    app.run(debug=True)