import json
import sys
import webbrowser
from pathlib import Path


def load_geojson(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_coords(geojson):
    geom = geojson["features"][0]["geometry"]

    if geom["type"] == "LineString":
        return geom["coordinates"]

    if geom["type"] == "MultiLineString":
        coords = []
        for line in geom["coordinates"]:
            coords.extend(line)
        return coords

    raise ValueError(f"暂不支持 geometry 类型: {geom['type']}")


def make_geojson(coords):
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                }
            }
        ]
    }


def make_html(coords, html_path):
    # Leaflet 用的是 [lat, lng]，GeoJSON 坐标是 [lng, lat]
    latlngs = [[c[1], c[0]] for c in coords]

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Check Route</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css">
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            height: 100%;
        }}
        #map {{
            width: 100%;
            height: 100%;
        }}
    </style>
</head>
<body>
<div id="map"></div>

<script>
    const latlngs = {json.dumps(latlngs)};

    const map = L.map('map');

    L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }}).addTo(map);

    const route = L.polyline(latlngs, {{
        color: 'blue',
        weight: 5
    }}).addTo(map);

    L.marker(latlngs[0]).addTo(map).bindPopup("起点").openPopup();
    L.marker(latlngs[latlngs.length - 1]).addTo(map).bindPopup("终点");

    map.fitBounds(route.getBounds());
</script>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    if len(sys.argv) < 3:
        print("用法：")
        print("python check_route.py 起点index 终点index [y/n]")
        print("例如：")
        print("python check_route.py 0 100")
        print("python check_route.py 100 200 y")
        return

    start_idx = int(sys.argv[1])
    end_idx = int(sys.argv[2])
    save_subroute = sys.argv[3].lower() if len(sys.argv) >= 4 else "n"

    input_path = Path("track_video01.geojson")
    output_geojson = Path(f"subroute_{start_idx}_{end_idx}.geojson")
    output_html = Path("check_route_preview.html")

    geojson = load_geojson(input_path)
    coords = extract_coords(geojson)

    if start_idx < 0 or end_idx >= len(coords):
        raise IndexError(f"索引超出范围。当前轨迹点数量为 {len(coords)}")

    if start_idx > end_idx:
        raise ValueError("起点 index 不能大于终点 index")

    selected_coords = coords[start_idx:end_idx + 1]

    print(f"原始轨迹点数：{len(coords)}")
    print(f"当前显示点数：{len(selected_coords)}")
    print(f"显示范围：{start_idx} 到 {end_idx}")

    if save_subroute == "y":
        sub_geojson = make_geojson(selected_coords)
        with open(output_geojson, "w", encoding="utf-8") as f:
            json.dump(sub_geojson, f, ensure_ascii=False, indent=2)
        print(f"已保存子路径：{output_geojson}")

    make_html(selected_coords, output_html)
    webbrowser.open(output_html.resolve().as_uri())


if __name__ == "__main__":
    main()