from typing import Optional
from pathlib import Path
import json

from src.generators.diagrams.relationship_extractor import RelationshipExtractor

class HTMLViewerGenerator:
    """
    Generate interactive HTML viewer for schema diagrams

    Features:
    - SVG embedding with pan/zoom
    - Entity list sidebar
    - Search/filter entities
    - Clickable entities (show details)
    - Relationship highlighting
    - Export options
    """

    HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Schema Diagram</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}

        .sidebar {{
            width: 300px;
            background: #f5f5f5;
            border-right: 1px solid #ddd;
            display: flex;
            flex-direction: column;
        }}

        .sidebar-header {{
            padding: 20px;
            background: #4a90e2;
            color: white;
        }}

        .sidebar-header h1 {{
            font-size: 18px;
            margin-bottom: 5px;
        }}

        .sidebar-header p {{
            font-size: 12px;
            opacity: 0.9;
        }}

        .search-box {{
            padding: 15px;
            border-bottom: 1px solid #ddd;
        }}

        .search-box input {{
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}

        .entity-list {{
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }}

        .entity-item {{
            padding: 10px 12px;
            margin-bottom: 5px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .entity-item:hover {{
            background: #e3f2fd;
            border-color: #4a90e2;
        }}

        .entity-item.active {{
            background: #4a90e2;
            color: white;
            border-color: #4a90e2;
        }}

        .entity-name {{
            font-weight: 600;
            font-size: 14px;
        }}

        .entity-schema {{
            font-size: 11px;
            color: #666;
            margin-top: 2px;
        }}

        .entity-item.active .entity-schema {{
            color: rgba(255, 255, 255, 0.8);
        }}

        .diagram-container {{
            flex: 1;
            position: relative;
            overflow: hidden;
            background: white;
        }}

        .diagram-svg {{
            width: 100%;
            height: 100%;
        }}

        .controls {{
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }}

        .btn {{
            padding: 8px 16px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}

        .btn:hover {{
            background: #f5f5f5;
            border-color: #4a90e2;
        }}

        .stats-panel {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            font-size: 12px;
        }}

        .stats-panel h3 {{
            font-size: 14px;
            margin-bottom: 10px;
            color: #4a90e2;
        }}

        .stat-item {{
            margin: 5px 0;
            color: #666;
        }}

        .entity-detail {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            max-width: 400px;
            display: none;
        }}

        .entity-detail.active {{
            display: block;
        }}

        .entity-detail h3 {{
            font-size: 16px;
            margin-bottom: 10px;
            color: #4a90e2;
        }}

        .field-list {{
            margin-top: 10px;
        }}

        .field-item {{
            padding: 5px 0;
            font-size: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}

        .field-name {{
            font-weight: 600;
            color: #333;
        }}

        .field-type {{
            color: #666;
            margin-left: 8px;
        }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h1>{title}</h1>
            <p>{entity_count} entities, {relationship_count} relationships</p>
        </div>

        <div class="search-box">
            <input type="text" id="search" placeholder="Search entities...">
        </div>

        <div class="entity-list" id="entityList">
            {entity_list_html}
        </div>
    </div>

    <div class="diagram-container">
        <div id="diagram" class="diagram-svg"></div>

        <div class="controls">
            <button class="btn" onclick="zoomIn()">Zoom In</button>
            <button class="btn" onclick="zoomOut()">Zoom Out</button>
            <button class="btn" onclick="resetView()">Reset</button>
            <button class="btn" onclick="downloadSVG()">Download SVG</button>
        </div>

        <div class="stats-panel">
            <h3>Statistics</h3>
            <div class="stat-item">Entities: {entity_count}</div>
            <div class="stat-item">Relationships: {relationship_count}</div>
            <div class="stat-item">Schemas: {schema_count}</div>
        </div>

        <div class="entity-detail" id="entityDetail">
            <h3 id="detailName"></h3>
            <div class="field-list" id="detailFields"></div>
        </div>
    </div>

    <script>
        // Entity data
        const entities = {entities_json};

        // SVG content
        const svgContent = `{svg_content}`;

        // Initialize
        document.getElementById('diagram').innerHTML = svgContent;

        // Search functionality
        document.getElementById('search').addEventListener('input', function(e) {{
            const query = e.target.value.toLowerCase();
            const items = document.querySelectorAll('.entity-item');

            items.forEach(item => {{
                const name = item.querySelector('.entity-name').textContent.toLowerCase();
                if (name.includes(query)) {{
                    item.style.display = 'block';
                }} else {{
                    item.style.display = 'none';
                }}
            }});
        }});

        // Entity click handlers
        function showEntityDetail(entityName) {{
            const entity = entities[entityName];
            if (!entity) return;

            document.getElementById('detailName').textContent = entityName + ' (' + entity.schema + ')';

            const fieldsList = document.getElementById('detailFields');
            fieldsList.innerHTML = entity.fields.map(field => {{
                return `
                    <div class="field-item">
                        <span class="field-name">${{field.name}}</span>
                        <span class="field-type">${{field.type}}</span>
                    </div>
                `;
            }}).join('');

            document.getElementById('entityDetail').classList.add('active');

            // Highlight entity in list
            document.querySelectorAll('.entity-item').forEach(item => {{
                item.classList.remove('active');
            }});
            document.querySelector(`[data-entity="${{entityName}}"]`).classList.add('active');
        }}

        // Zoom controls
        let scale = 1;
        const svg = document.querySelector('svg');

        function zoomIn() {{
            scale = Math.min(scale + 0.2, 3);
            updateZoom();
        }}

        function zoomOut() {{
            scale = Math.max(scale - 0.2, 0.5);
            updateZoom();
        }}

        function resetView() {{
            scale = 1;
            updateZoom();
        }}

        function updateZoom() {{
            if (svg) {{
                svg.style.transform = `scale(${{scale}})`;
                svg.style.transformOrigin = 'center center';
            }}
        }}

        // Download SVG
        function downloadSVG() {{
            const blob = new Blob([svgContent], {{type: 'image/svg+xml'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'schema.svg';
            a.click();
        }}

        // Pan/drag functionality
        let isPanning = false;
        let startX, startY, scrollLeft, scrollTop;

        const container = document.querySelector('.diagram-container');

        container.addEventListener('mousedown', (e) => {{
            if (e.target === container || e.target.tagName === 'svg') {{
                isPanning = true;
                startX = e.pageX - container.offsetLeft;
                startY = e.pageY - container.offsetTop;
                scrollLeft = container.scrollLeft;
                scrollTop = container.scrollTop;
            }}
        }});

        container.addEventListener('mousemove', (e) => {{
            if (!isPanning) return;
            e.preventDefault();
            const x = e.pageX - container.offsetLeft;
            const y = e.pageY - container.offsetTop;
            container.scrollLeft = scrollLeft - (x - startX);
            container.scrollTop = scrollTop - (y - startY);
        }});

        container.addEventListener('mouseup', () => {{
            isPanning = false;
        }});

        container.addEventListener('mouseleave', () => {{
            isPanning = false;
        }});
    </script>
</body>
</html>
'''

    def __init__(self, extractor: RelationshipExtractor):
        self.extractor = extractor

    def generate(
        self,
        svg_content: str,
        output_path: Optional[str] = None,
        title: str = "Schema Diagram"
    ) -> str:
        """
        Generate interactive HTML viewer

        Args:
            svg_content: SVG diagram content
            output_path: Path to save HTML file (if None, returns HTML string)
            title: Page title

        Returns:
            HTML content as string

        Raises:
            RuntimeError: If HTML generation fails
        """
        if not self.extractor.entities:
            raise ValueError("No entities found in extractor. Run extract_from_entities() first.")

        if not svg_content or not svg_content.strip():
            raise ValueError("SVG content cannot be empty")

        try:
            # Build entity list HTML
            entity_list_html = []

            for entity_name, entity_node in sorted(self.extractor.entities.items()):
                entity_list_html.append(f'''
                    <div class="entity-item" data-entity="{entity_name}" onclick="showEntityDetail('{entity_name}')">
                        <div class="entity-name">{entity_name}</div>
                        <div class="entity-schema">{entity_node.schema} • {len(entity_node.fields)} fields</div>
                    </div>
                ''')

            # Build entities JSON
            entities_data = {}
            for entity_name, entity_node in self.extractor.entities.items():
                entities_data[entity_name] = {
                    'name': entity_name,
                    'schema': entity_node.schema,
                    'fields': entity_node.fields,
                }

            # Get statistics
            summary = self.extractor.get_relationship_summary()

            # Generate HTML
            html = self.HTML_TEMPLATE.format(
                title=title,
                entity_count=summary['total_entities'],
                relationship_count=summary['total_relationships'],
                schema_count=len(summary['schemas']),
                entity_list_html=''.join(entity_list_html),
                entities_json=json.dumps(entities_data),
                svg_content=svg_content.replace('`', '\\`'),  # Escape backticks
            )

            # Write file if path provided
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_text(html)

            return html

        except Exception as e:
            raise RuntimeError(f"Failed to generate HTML viewer: {e}") from e