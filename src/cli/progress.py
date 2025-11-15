"""
Rich progress tracking system for SpecQL CLI

Provides beautiful, informative progress output using the rich library,
with graceful fallback to basic click output when rich is unavailable.
"""

import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Callable

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.tree import Tree
    from rich.panel import Panel
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Define dummy classes for type hints when rich is not available
    Console = None
    Progress = None
    SpinnerColumn = None
    BarColumn = None
    TextColumn = None
    TimeElapsedColumn = None
    Table = None
    Tree = None
    Panel = None
    Text = None


class SpecQLProgress:
    """Rich progress tracker for SpecQL generation"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.start_time = time.time()
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

    def scan_phase(self, entity_files: List[str]) -> Dict[str, int]:
        """Show entity scanning phase and return schema breakdown"""
        if not RICH_AVAILABLE or not self.console:
            print("🔍 Scanning entity files...")
            print(f"   Found {len(entity_files)} entity files")
            return {}

        self.console.print("🔍 [bold blue]Scanning entity files...[/bold blue]")
        self.console.print(f"   Found [bold]{len(entity_files)}[/bold] entity files")

        # Group by schema
        schema_stats = defaultdict(int)
        for file_path in entity_files:
            try:
                # Parse schema from file path or content
                # For now, use a simple heuristic based on directory structure
                path = Path(file_path)
                if "entities" in path.parts:
                    # Extract schema from path like entities/common/user.yaml -> common
                    entities_idx = path.parts.index("entities")
                    if entities_idx + 1 < len(path.parts):
                        schema = path.parts[entities_idx + 1]
                        if not schema.endswith('.yaml'):
                            schema_stats[schema] += 1
                        else:
                            schema_stats["default"] += 1
                    else:
                        schema_stats["default"] += 1
                else:
                    schema_stats["default"] += 1
            except Exception:
                schema_stats["default"] += 1

        # Show schema breakdown
        if len(schema_stats) > 1:
            table = Table(title="📊 Entity Breakdown", show_header=True)
            table.add_column("Schema", style="cyan")
            table.add_column("Entities", justify="right", style="green")

            for schema, count in sorted(schema_stats.items()):
                table.add_row(schema, str(count))

            self.console.print(table)

        return dict(schema_stats)

    def generation_progress(self, entities: List[Any]) -> Iterator[tuple[Any, Callable[[], None]]]:
        """Show progress bar during generation and yield entities with progress updater"""
        if not RICH_AVAILABLE:
            print("⚙️  Generating database schema...")
            for entity in entities:
                yield entity, lambda: None
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "⚙️  Generating database schema...",
                total=len(entities)
            )

            for entity in entities:
                # Yield control to caller for actual generation
                yield entity, lambda: progress.update(task, advance=1)

    def summary(
        self,
        stats: Dict[str, Any],
        output_dir: str,
        generated_files: Optional[List[str]] = None
    ) -> None:
        """Show final summary with statistics"""
        elapsed = time.time() - self.start_time

        if not RICH_AVAILABLE:
            print(f"\n✅ Generation complete! ({elapsed:.1f} seconds)")
            print(f"📁 Output: {output_dir}")
            print("📈 Statistics:")
            print(f"   Total files: {stats.get('total_files', 0)} SQL files")
            print(f"   Total SQL: ~{stats.get('total_lines', 0):,} lines")
            print(f"   Tables: {stats.get('tables', 0)}")
            print(f"   CRUD actions: {stats.get('crud_actions', 0)}")
            print(f"   Business actions: {stats.get('business_actions', 0)}")
            print("\n🎯 Next Steps:")
            print(f"   1. Review: tree {output_dir}")
            print(f"   2. Apply: psql -f {output_dir}/000_app_foundation.sql")
            print("   3. Migrate: Apply entity files in subdirectories")
            print("📚 Learn more: specql generate --help")
            return

        self.console.print(f"\n✅ [bold green]Generation complete![/bold green] ({elapsed:.1f} seconds)\n")

        # Output location with tree structure
        self.console.print(f"📁 [bold]Output:[/bold] {output_dir}")

        # Show directory structure if we have generated files
        if generated_files and len(generated_files) <= 20:  # Only show tree for reasonable number of files
            try:
                tree = Tree(f"[bold]{output_dir}[/bold]")
                file_tree = self._build_file_tree(generated_files, output_dir)
                if file_tree:
                    tree.add(file_tree)
                    self.console.print(tree)
            except Exception:
                # If tree building fails, just show the path
                pass

        # Statistics
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="dim")
        stats_table.add_column("Value", style="bold")

        stats_table.add_row("Total files:", f"{stats.get('total_files', 0)} SQL files")
        stats_table.add_row("Total SQL:", f"~{stats.get('total_lines', 0):,} lines")
        stats_table.add_row("Tables (tb_*):", str(stats.get('tables', 0)))
        stats_table.add_row("Table views (tv_*):", str(stats.get('table_views', 0)))
        stats_table.add_row("CRUD actions:", str(stats.get('crud_actions', 0)))
        stats_table.add_row("Business actions:", str(stats.get('business_actions', 0)))

        self.console.print(Panel(stats_table, title="📈 Statistics", border_style="blue"))

        # Next steps
        self.console.print("\n🎯 [bold]Next Steps:[/bold]")
        self.console.print(f"   1. Review:    tree {output_dir}")
        self.console.print(f"   2. Apply:     psql -f {output_dir}/000_app_foundation.sql")
        self.console.print("   3. Migrate:   Apply entity files in subdirectories")
        self.console.print("\n📚 Learn more: [dim]specql generate --help[/dim]")

    def _build_file_tree(self, files: List[str], base_dir: str) -> Optional[Tree]:
        """Build a rich tree structure from generated files"""
        if not files:
            return None

        base_path = Path(base_dir)
        tree = Tree("")

        # Group files by directory
        dir_groups = defaultdict(list)
        for file_path in files:
            try:
                path = Path(file_path)
                if path.is_absolute():
                    # Make relative to base_dir if possible
                    try:
                        path = path.relative_to(base_path)
                    except ValueError:
                        pass

                parent = str(path.parent) if path.parent != Path(".") else ""
                dir_groups[parent].append(path.name)
            except Exception:
                continue

        # Build tree structure
        def add_to_tree(parent_tree: Tree, current_path: str, groups: Dict[str, List[str]]):
            if current_path in groups:
                for file in sorted(groups[current_path]):
                    parent_tree.add(f"[green]{file}[/green]")

            # Add subdirectories
            subdirs = {}
            for dir_path in groups.keys():
                if dir_path.startswith(current_path) and dir_path != current_path:
                    remaining = dir_path[len(current_path):].lstrip("/")
                    if "/" in remaining:
                        subdir = remaining.split("/")[0]
                    else:
                        subdir = remaining
                    if subdir:
                        subdirs[subdir] = dir_path

            for subdir, full_path in sorted(subdirs.items()):
                subtree = parent_tree.add(f"[blue]{subdir}/[/blue]")
                add_to_tree(subtree, full_path, groups)

        add_to_tree(tree, "", dir_groups)
        return tree if tree.children else None

    def show_error(self, message: str) -> None:
        """Show error message"""
        if RICH_AVAILABLE:
            self.console.print(f"❌ [bold red]{message}[/bold red]")
        else:
            print(f"❌ {message}")

    def show_warning(self, message: str) -> None:
        """Show warning message"""
        if RICH_AVAILABLE:
            self.console.print(f"⚠️  [bold yellow]{message}[/bold yellow]")
        else:
            print(f"⚠️  {message}")

    def show_info(self, message: str) -> None:
        """Show info message"""
        if RICH_AVAILABLE:
            self.console.print(f"ℹ️  [bold blue]{message}[/bold blue]")
        else:
            print(f"ℹ️  {message}")

    def show_success(self, message: str) -> None:
        """Show success message"""
        if RICH_AVAILABLE:
            self.console.print(f"✅ [bold green]{message}[/bold green]")
        else:
            print(f"✅ {message}")