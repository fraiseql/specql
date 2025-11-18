import click
from datetime import datetime
from .cache_manager import CacheManager


@click.group()
def cache():
    """Manage reverse engineering cache"""
    pass


@cache.command("stats")
def cache_stats():
    """Show cache statistics"""
    cache_manager = CacheManager()
    cache_files = list(cache_manager.cache_dir.glob("*.json"))

    if not cache_files:
        click.echo("Cache is empty")
        return

    total_size = sum(f.stat().st_size for f in cache_files)
    oldest = min(f.stat().st_mtime for f in cache_files)
    newest = max(f.stat().st_mtime for f in cache_files)

    click.echo("📊 Cache Statistics")
    click.echo(f"  Entries: {len(cache_files)}")
    click.echo(f"  Total size: {total_size / 1024:.1f} KB")
    click.echo(f"  Oldest entry: {datetime.fromtimestamp(oldest)}")
    click.echo(f"  Newest entry: {datetime.fromtimestamp(newest)}")


@cache.command("clear")
@click.option("--older-than", type=int, help="Clear entries older than N days")
def cache_clear(older_than):
    """Clear cache"""
    cache_manager = CacheManager()
    cache_manager.clear_cache(older_than_days=older_than)
    click.echo("✓ Cache cleared")
