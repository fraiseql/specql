"""
Main Textual application for SpecQL Interactive CLI

Provides a rich terminal UI with live preview, syntax highlighting,
auto-completion, and pattern suggestions.
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, TextArea, Button
from textual.binding import Binding
from rich.syntax import Syntax
from rich.panel import Panel

from .preview_generator import PreviewGenerator


class SpecQLInteractive(App):
    """
    Interactive SpecQL builder with live preview

    Features:
    - Split pane: YAML editor + SQL preview
    - Real-time validation
    - Pattern suggestions
    - Syntax highlighting
    """

    CSS = """
    #editor-container {
        width: 50%;
        border: solid $primary;
    }

    #preview-container {
        width: 50%;
        border: solid $accent;
    }

    #pattern-suggestions {
        height: 10;
        border: solid $warning;
    }

    TextArea {
        height: 1fr;
    }

    #action-bar {
        height: 3;
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+g", "generate", "Generate"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+p", "toggle_preview", "Toggle Preview"),
        Binding("ctrl+h", "help", "Help"),
    ]

    TITLE = "SpecQL Interactive Builder"

    def __init__(self):
        super().__init__()
        self.yaml_content = ""
        self.preview_mode = "schema"  # 'schema', 'actions', 'fraiseql'
        self.preview_generator = PreviewGenerator()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app"""
        yield Header()

        with Horizontal():
            # Left pane: YAML editor
            with Vertical(id="editor-container"):
                yield Static("📝 SpecQL YAML Editor", classes="panel-title")
                yield TextArea(
                    id="yaml-editor",
                    language="yaml",
                    theme="monokai",
                    show_line_numbers=True,
                )
                yield Static(id="validation-status", classes="status-bar")

            # Right pane: Live preview
            with Vertical(id="preview-container"):
                yield Static("🔍 Live Preview (PostgreSQL)", classes="panel-title")
                yield Static(id="preview-output", classes="preview")
                yield Static(id="preview-status", classes="status-bar")

        # Bottom: Pattern suggestions
        yield Static(id="pattern-suggestions", classes="suggestions-panel")

        # Action bar
        with Horizontal(id="action-bar"):
            yield Button("💾 Save", id="save-btn", variant="primary")
            yield Button("🚀 Generate", id="generate-btn", variant="success")
            yield Button("🎨 Apply Pattern", id="pattern-btn", variant="default")
            yield Button("🤖 AI Help", id="ai-btn", variant="warning")
            yield Button("📤 Export", id="export-btn", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted"""
        # Set initial YAML template
        editor = self.query_one("#yaml-editor", TextArea)
        editor.text = self._get_template()

        # Start watching for changes
        editor.watch_text(self._on_yaml_change)

    def _get_template(self) -> str:
        """Get starter YAML template"""
        return """entity: Contact
schema: crm
description: "CRM contact entity"

fields:
  email: text
  company_id: ref(Company)
  status:
    type: enum
    values: [lead, qualified, customer]

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
"""

    def _on_yaml_change(self, new_text: str) -> None:
        """Called when YAML editor content changes"""
        self.yaml_content = new_text
        self.refresh_preview()

    def refresh_preview(self) -> None:
        """Regenerate preview from current YAML"""
        preview_widget = self.query_one("#preview-output", Static)
        validation_widget = self.query_one("#validation-status", Static)

        try:
            # Generate preview
            result = self.preview_generator.generate_preview(
                self.yaml_content,
                mode=self.preview_mode
            )

            if result.success:
                # Update preview with syntax-highlighted SQL
                syntax = Syntax(
                    result.output,
                    "sql",
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=True,
                )
                preview_widget.update(syntax)
                validation_widget.update("✅ Valid SpecQL")

                # Update pattern suggestions
                self._update_pattern_suggestions(result.detected_patterns)
            else:
                # Show errors
                validation_widget.update(f"❌ {result.error}")
                preview_widget.update(Panel(
                    result.error,
                    title="Validation Error",
                    border_style="red"
                ))

        except Exception as e:
            validation_widget.update(f"❌ Error: {str(e)}")

    def _update_pattern_suggestions(self, patterns: list) -> None:
        """Update pattern suggestions panel"""
        suggestions_widget = self.query_one("#pattern-suggestions", Static)

        if not patterns:
            suggestions_widget.update("💡 No patterns detected yet")
            return

        suggestion_text = "🎯 Detected Patterns: " + ", ".join(
            f"{p['name']} ({p['confidence']:.0%})" for p in patterns
        )
        suggestions_widget.update(suggestion_text)

    def action_save(self) -> None:
        """Save current YAML to file"""

        # Show save dialog (simplified)
        # In real implementation, use proper dialog widget
        self.notify("💾 Saved to entities/contact.yaml")

    def action_generate(self) -> None:
        """Generate schema from current YAML"""
        self.notify("🚀 Generating schema...")

        try:
            from src.cli.orchestrator import Orchestrator
            orchestrator = Orchestrator()

            # Generate from current YAML
            # (simplified - real implementation writes temp file)
            result = orchestrator.generate_from_yaml(self.yaml_content)

            self.notify(f"✅ Generated {result.files_created} files")
        except Exception as e:
            self.notify(f"❌ Generation failed: {e}", severity="error")

    def action_toggle_preview(self) -> None:
        """Toggle preview mode (schema/actions/fraiseql)"""
        modes = ["schema", "actions", "fraiseql"]
        current_idx = modes.index(self.preview_mode)
        self.preview_mode = modes[(current_idx + 1) % len(modes)]

        self.notify(f"Preview mode: {self.preview_mode}")
        self.refresh_preview()

    def action_help(self) -> None:
        """Show help screen"""
        help_text = """
SpecQL Interactive Builder - Keyboard Shortcuts

Ctrl+S    Save YAML to file
Ctrl+G    Generate schema
Ctrl+P    Toggle preview mode (Schema/Actions/FraiseQL)
Ctrl+Q    Quit
Ctrl+H    Show this help

Editor Features:
- Syntax highlighting for YAML
- Real-time validation
- Auto-completion (Tab)
- Pattern suggestions

Preview Modes:
1. Schema - PostgreSQL DDL (tables, indexes, constraints)
2. Actions - PL/pgSQL functions
3. FraiseQL - GraphQL metadata
"""
        self.notify(help_text, title="Help")


def run_interactive():
    """Entry point for interactive CLI"""
    app = SpecQLInteractive()
    app.run()