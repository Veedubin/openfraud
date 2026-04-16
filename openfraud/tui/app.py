"""
openfraud/tui/app.py
Example Textual app demonstrating OpenFraud graph TUI integration.

This can be integrated into OCR My Junk's existing TUI or run standalone.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from openfraud.tui.graph_screen import FraudGraphScreen


class OpenFraudTUI(App):
    """Main OpenFraud TUI application with graph analysis."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    .title {
        text-style: bold;
        text-align: center;
        color: $primary;
    }
    
    .sidebar {
        width: 25;
        height: 100%;
        background: $surface;
        border-right: solid $primary;
        padding: 1;
    }
    
    .sidebar-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $primary;
    }
    
    .tab-title {
        text-style: bold;
        color: $primary-lighten-2;
        margin-bottom: 1;
    }
    
    .subtitle {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    Button {
        margin: 1 0;
        width: 100%;
    }
    
    DataTable {
        height: 1fr;
        border: solid $primary-darken-2;
    }
    
    TabbedContent {
        width: 1fr;
        height: 100%;
    }
    """
    
    BINDINGS: ClassVar = [
        Binding("q", "quit", "Quit", show=True),
        Binding("g", "open_graph", "Graph Analysis", show=True),
        Binding("?", "show_help", "Help", show=True),
    ]
    
    def __init__(self, db_path: Path | None = None, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
    
    def compose(self) -> ComposeResult:
        """Compose the main app."""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            yield Static("OpenFraud - Graph Analysis TUI", classes="title")
            yield Static("Press [b]G[/b] to open Graph Analysis or [b]Q[/b] to quit", classes="subtitle")
            yield Static("""
Available Features:
• Real-time graph statistics
• Risk node analysis with PageRank
• ASCII network visualization
• Community fraud heatmaps
• Pattern detection (self-loops, spiderwebs, cliques)
• Interactive node explorer

Press 'G' to launch the graph analysis interface.
            "", id="help-text")
        
        yield Footer()
    
    def action_open_graph(self):
        """Open the fraud graph analysis screen."""
        self.push_screen(FraudGraphScreen())
    
    def action_show_help(self):
        """Show help information."""
        self.notify(
            "OpenFraud Graph TUI\n"
            "Press G: Graph Analysis\n"
            "Press Q: Quit\n"
            "In Graph Screen:\n"
            "  1-4: Switch tabs\n"
            "  R: Refresh all data\n"
            "  S: Detect self-loops\n"
            "  W: Detect spiderwebs\n"
            "  C: Detect cliques",
            severity="information",
            timeout=10
        )


def main():
    """Run the TUI application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenFraud Graph TUI")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to DuckDB database (optional)"
    )
    
    args = parser.parse_args()
    
    app = OpenFraudTUI(db_path=args.db_path)
    app.run()


if __name__ == "__main__":
    main()
