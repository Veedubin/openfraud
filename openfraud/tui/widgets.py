"""
openfraud/tui/widgets.py
Textual widgets for fraud graph visualization.
"""

from __future__ import annotations

from typing import Any, ClassVar

from rich.console import Group
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text
from textual.reactive import reactive
from textual.widgets import DataTable, Static, Tree, Input, Button
from textual.containers import Horizontal, Vertical


class GraphStatsWidget(Static):
    """Display key graph statistics."""

    DEFAULT_CSS = """
    GraphStatsWidget {
        height: auto;
        padding: 1;
        border: solid $primary;
    }
    """

    # Reactive state
    node_count: reactive[int] = reactive(0)
    edge_count: reactive[int] = reactive(0)
    fraud_count: reactive[int] = reactive(0)
    community_count: reactive[int] = reactive(0)

    def __init__(self, db: Any | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.db = db

    def watch_node_count(self, value: int):
        self.update_display()

    def watch_edge_count(self, value: int):
        self.update_display()

    def watch_fraud_count(self, value: int):
        self.update_display()

    def update_display(self):
        """Update the display with current stats."""
        fraud_rate = (self.fraud_count / self.node_count * 100) if self.node_count > 0 else 0

        table = RichTable(show_header=False, box=None)
        table.add_column("Metric", style="cyan", justify="right")
        table.add_column("Value", style="white")

        table.add_row("Total Nodes", f"{self.node_count:,}")
        table.add_row("Relationships", f"{self.edge_count:,}")
        table.add_row("Fraud Nodes", f"{self.fraud_count:,}")
        table.add_row("Fraud Rate", f"{fraud_rate:.2f}%")
        table.add_row("Communities", f"{self.community_count:,}")

        if self.node_count > 0 and self.edge_count > 0:
            density = self.edge_count / (self.node_count * (self.node_count - 1))
            table.add_row("Density", f"{density:.6f}")

        self.update(Panel(table, title="Graph Statistics", border_style="blue"))

    def refresh_stats(self):
        """Query database and update stats."""
        if self.db is None:
            try:
                from memgraph_toolbox.api.memgraph import Memgraph

                self.db = Memgraph()
            except Exception:
                self.update("[red]Error: Could not connect to Memgraph[/red]")
                return

        try:
            # Get node count
            result = self.db.query("MATCH (n) RETURN count(n) as count")
            self.node_count = result[0]["count"] if result else 0

            # Get edge count
            result = self.db.query("MATCH ()-[r]->() RETURN count(r) as count")
            self.edge_count = result[0]["count"] if result else 0

            # Get fraud count
            result = self.db.query("""
                MATCH (n) 
                WHERE n.is_fraud = true 
                RETURN count(n) as count
            """)
            self.fraud_count = result[0]["count"] if result else 0

            # Get community count
            result = self.db.query("""
                MATCH (n) 
                WHERE n.community_id IS NOT NULL 
                RETURN count(DISTINCT n.community_id) as count
            """)
            self.community_count = result[0]["count"] if result else 0

        except Exception as e:
            self.update(f"[red]Error querying graph: {e}[/red]")

    def on_mount(self):
        self.refresh_stats()


class RiskNodeTable(DataTable):
    """Table displaying high-risk nodes with PageRank."""

    DEFAULT_CSS = """
    RiskNodeTable {
        height: 1fr;
        border: solid $primary;
    }
    """

    def __init__(self, db: Any | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.db = db
        self.cursor_type = "row"

    def on_mount(self):
        self.add_columns("Node ID", "PageRank", "Fraud Score", "Community", "Risk Level")
        self.refresh_data()

    def refresh_data(self):
        """Load high-risk nodes from database."""
        if self.db is None:
            try:
                from memgraph_toolbox.api.memgraph import Memgraph

                self.db = Memgraph()
            except Exception:
                return

        try:
            # Get nodes with PageRank and fraud scores
            result = self.db.query("""
                MATCH (n)
                WHERE n.pagerank IS NOT NULL OR n.fraud_score IS NOT NULL
                RETURN n.id as id, 
                       n.pagerank as pagerank,
                       n.fraud_score as fraud_score,
                       n.community_id as community,
                       n.is_fraud as is_fraud
                ORDER BY COALESCE(n.fraud_score, 0) * COALESCE(n.pagerank, 0) DESC
                LIMIT 50
            """)

            self.clear()
            for row in result:
                # Calculate composite risk
                pagerank = row.get("pagerank", 0) or 0
                fraud_score = row.get("fraud_score", 0) or 0
                is_fraud = row.get("is_fraud", False)

                composite_risk = fraud_score * (1 + pagerank)

                if composite_risk > 0.7 or is_fraud:
                    risk_level = "[red]CRITICAL[/red]"
                elif composite_risk > 0.4:
                    risk_level = "[yellow]HIGH[/yellow]"
                elif composite_risk > 0.2:
                    risk_level = "[orange1]MEDIUM[/orange1]"
                else:
                    risk_level = "[green]LOW[/green]"

                self.add_row(
                    str(row.get("id", "N/A")),
                    f"{pagerank:.4f}",
                    f"{fraud_score:.2f}",
                    str(row.get("community", "N/A")),
                    risk_level,
                )

        except Exception as e:
            self.add_row("Error", str(e), "", "", "[red]ERROR[/red]")


class ASCIINetworkGraph(Static):
    """ASCII visualization of network connections."""

    DEFAULT_CSS = """
    ASCIINetworkGraph {
        height: auto;
        min-height: 15;
        padding: 1;
        border: solid $primary;
    }
    """

    center_node: reactive[str | None] = reactive(None)

    def __init__(self, db: Any | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.db = db

    def watch_center_node(self, node_id: str | None):
        self.render_graph()

    def render_graph(self):
        """Render ASCII network graph."""
        if self.center_node is None:
            # Show default overview
            self.update(self._render_overview())
            return

        if self.db is None:
            try:
                from memgraph_toolbox.api.memgraph import Memgraph

                self.db = Memgraph()
            except Exception as e:
                self.update(f"[red]Database error: {e}[/red]")
                return

        try:
            # Get neighbors
            neighbors = self.db.query(
                """
                MATCH (center {id: $id})-[r]-(neighbor)
                RETURN neighbor.id as id, 
                       type(r) as rel_type,
                       neighbor.fraud_score as fraud_score,
                       neighbor.is_fraud as is_fraud
                LIMIT 12
            """,
                {"id": self.center_node},
            )

            self.update(self._render_node_with_neighbors(self.center_node, neighbors))

        except Exception as e:
            self.update(f"[red]Error rendering graph: {e}[/red]")

    def _render_overview(self) -> str:
        """Render network overview when no center node selected."""
        lines = [
            "Network Overview",
            "─" * 40,
            "",
            "    [center] Select a node to view connections",
            "",
            "Layout: Hub-and-spoke visualization",
            "",
            "Legend:",
            "  [●] High fraud risk (>0.7)",
            "  [○] Medium fraud risk (0.3-0.7)",
            "  [◌] Low fraud risk (<0.3)",
            "",
            "Click on a node in the Risk Table to explore.",
        ]
        return "\n".join(lines)

    def _render_node_with_neighbors(self, center: str, neighbors: list) -> str:
        """Render ASCII graph with center node and neighbors."""
        if not neighbors:
            return f"[yellow]No connections found for {center}[/yellow]"

        lines = []
        lines.append(f"Network: {center}")
        lines.append("─" * 50)
        lines.append("")

        # Center node display
        lines.append("           ┌─────────────┐")
        lines.append(f"           │  {center[:13]:^13}│")
        lines.append("           └──────┬──────┘")
        lines.append("                  │")

        # Split neighbors into left and right columns
        left_neighbors = neighbors[::2][:5]  # Even indices
        right_neighbors = neighbors[1::2][:5]  # Odd indices

        max_rows = max(len(left_neighbors), len(right_neighbors))

        for i in range(max_rows):
            line_parts = []

            # Left side
            if i < len(left_neighbors):
                n = left_neighbors[i]
                symbol = self._get_fraud_symbol(n.get("fraud_score"), n.get("is_fraud"))
                line_parts.append(f"  {symbol}─── {n['id'][:15]:<15}")
            else:
                line_parts.append(" " * 24)

            # Center connector
            if i == 0:
                line_parts.append("────┤")
            elif i == len(neighbors) - 1 or i == max_rows - 1:
                line_parts.append("    │")
            else:
                line_parts.append("────┼")

            # Right side
            if i < len(right_neighbors):
                n = right_neighbors[i]
                symbol = self._get_fraud_symbol(n.get("fraud_score"), n.get("is_fraud"))
                line_parts.append(f" {n['id'][:15]:>15} ───{symbol}")

            lines.append("".join(line_parts))

        lines.append("")
        lines.append(f"Total connections: {len(neighbors)}")

        return "\n".join(lines)

    def _get_fraud_symbol(self, fraud_score: float | None, is_fraud: bool | None) -> str:
        """Get symbol based on fraud risk."""
        if is_fraud:
            return "[red]●[/red]"
        if fraud_score is None:
            return "○"
        if fraud_score > 0.7:
            return "[red]●[/red]"
        elif fraud_score > 0.3:
            return "[yellow]○[/yellow]"
        else:
            return "[green]◌[/green]"

    def on_mount(self):
        self.render_graph()


class FraudCommunityHeatmap(Static):
    """ASCII heatmap showing fraud rates by community."""

    DEFAULT_CSS = """
    FraudCommunityHeatmap {
        height: auto;
        min-height: 12;
        padding: 1;
        border: solid $primary;
    }
    """

    def __init__(self, db: Any | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.db = db

    def on_mount(self):
        self.refresh_heatmap()

    def refresh_heatmap(self):
        """Generate community fraud heatmap."""
        if self.db is None:
            try:
                from memgraph_toolbox.api.memgraph import Memgraph

                self.db = Memgraph()
            except Exception as e:
                self.update(f"[red]Error: {e}[/red]")
                return

        try:
            communities = self.db.query("""
                MATCH (n)
                WHERE n.community_id IS NOT NULL
                WITH n.community_id as comm,
                     count(n) as total,
                     sum(CASE WHEN n.is_fraud = true THEN 1 ELSE 0 END) as frauds
                RETURN comm, total, frauds
                ORDER BY frauds DESC, total DESC
                LIMIT 10
            """)

            if not communities:
                self.update("[yellow]No community data available[/yellow]")
                return

            lines = []
            lines.append("Community Fraud Heatmap")
            lines.append("─" * 50)
            lines.append("")

            for c in communities:
                comm_id = c["comm"]
                total = c["total"]
                frauds = c["frauds"]
                fraud_rate = frauds / total if total > 0 else 0

                # Create bar
                bar_length = int(fraud_rate * 25)
                bar = "█" * bar_length + "░" * (25 - bar_length)

                # Color based on fraud rate
                if fraud_rate > 0.5:
                    color = "red"
                    emoji = "🔴"
                elif fraud_rate > 0.2:
                    color = "yellow"
                    emoji = "🟡"
                elif fraud_rate > 0.05:
                    color = "orange1"
                    emoji = "🟠"
                else:
                    color = "green"
                    emoji = "🟢"

                line = f"[{color}]{emoji} Comm {comm_id:>3}: |{bar}| {fraud_rate * 100:5.1f}% ({frauds}/{total})[/{color}]"
                lines.append(line)

            lines.append("")
            lines.append("Legend: 🔴 High Risk  🟡 Medium  🟠 Low  🟢 Safe")

            self.update("\n".join(lines))

        except Exception as e:
            self.update(f"[red]Error generating heatmap: {e}[/red]")


class NodeExplorerWidget(Vertical):
    """Interactive widget for exploring graph nodes."""

    DEFAULT_CSS = """
    NodeExplorerWidget {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    NodeExplorerWidget #search-row {
        height: auto;
    }
    
    NodeExplorerWidget #node-search {
        width: 1fr;
    }
    
    NodeExplorerWidget Tree {
        height: 1fr;
        border: solid $primary-darken-2;
    }
    """

    def __init__(self, db: Any | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.db = db

    def compose(self):
        with Horizontal(id="search-row"):
            yield Input(placeholder="Search node ID...", id="node-search")
            yield Button("Search", id="search-btn", variant="primary")
            yield Button("Neighbors", id="neighbors-btn")

        yield Tree("Graph Structure", id="node-tree")

        yield Static("Node Properties", classes="subtitle")
        yield DataTable(id="node-props")

    def on_mount(self):
        # Setup tree
        tree = self.query_one("#node-tree", Tree)
        tree.root.expand()

        # Setup properties table
        props_table = self.query_one("#node-props", DataTable)
        props_table.add_columns("Property", "Value")

        # Load initial data
        self._load_sample_nodes()

    def _load_sample_nodes(self):
        """Load sample nodes into tree."""
        if self.db is None:
            try:
                from memgraph_toolbox.api.memgraph import Memgraph

                self.db = Memgraph()
            except Exception:
                return

        try:
            tree = self.query_one("#node-tree", Tree)

            # Get high-risk nodes
            high_risk = self.db.query("""
                MATCH (n)
                WHERE n.is_fraud = true OR (n.fraud_score IS NOT NULL AND n.fraud_score > 0.5)
                RETURN n.id as id, n.fraud_score as score
                LIMIT 20
            """)

            fraud_node = tree.root.add("🔴 High Risk Nodes", expand=True)
            for node in high_risk:
                node_id = node["id"]
                score = node.get("score", "N/A")
                fraud_node.add_leaf(f"{node_id} (score: {score})")

            # Get hub nodes (high pagerank)
            hubs = self.db.query("""
                MATCH (n)
                WHERE n.pagerank IS NOT NULL
                RETURN n.id as id, n.pagerank as rank
                ORDER BY n.pagerank DESC
                LIMIT 10
            """)

            hub_node = tree.root.add("⭐ Hub Nodes", expand=True)
            for node in hubs:
                node_id = node["id"]
                rank = node.get("rank", 0)
                hub_node.add_leaf(f"{node_id} (PR: {rank:.3f})")

        except Exception as e:
            tree.root.add(f"Error loading nodes: {e}")

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        button_id = event.button.id
        search_input = self.query_one("#node-search", Input)
        node_id = search_input.value.strip()

        if not node_id:
            return

        if button_id == "search-btn":
            self._search_node(node_id)
        elif button_id == "neighbors-btn":
            self._show_neighbors(node_id)

    def _search_node(self, node_id: str):
        """Search for a specific node and display properties."""
        if self.db is None:
            return

        try:
            result = self.db.query(
                """
                MATCH (n {id: $id})
                RETURN n, labels(n) as labels
            """,
                {"id": node_id},
            )

            props_table = self.query_one("#node-props", DataTable)
            props_table.clear()

            if not result:
                props_table.add_row("Status", "[red]Node not found[/red]")
                return

            node_data = result[0]["n"]
            labels = result[0].get("labels", [])

            props_table.add_row("ID", str(node_id))
            props_table.add_row("Labels", ", ".join(labels))

            for key, value in node_data.items():
                if key != "id" and value is not None:
                    # Format value
                    if isinstance(value, float):
                        value_str = f"{value:.4f}"
                    else:
                        value_str = str(value)
                    props_table.add_row(key, value_str)

        except Exception as e:
            props_table = self.query_one("#node-props", DataTable)
            props_table.clear()
            props_table.add_row("Error", str(e))

    def _show_neighbors(self, node_id: str):
        """Show neighbors of a node in the tree."""
        if self.db is None:
            return

        try:
            tree = self.query_one("#node-tree", Tree)

            # Add to tree
            neighbor_root = tree.root.add(f"🔗 Connections of {node_id}", expand=True)

            neighbors = self.db.query(
                """
                MATCH (n {id: $id})-[r]-(neighbor)
                RETURN neighbor.id as id, type(r) as rel_type, 
                       neighbor.fraud_score as risk
                LIMIT 20
            """,
                {"id": node_id},
            )

            if not neighbors:
                neighbor_root.add_leaf("No connections found")
            else:
                for n in neighbors:
                    risk = n.get("risk", 0)
                    symbol = "🔴" if risk and risk > 0.5 else "🟢"
                    neighbor_root.add_leaf(f"{symbol} {n['id']} ({n['rel_type']})")

        except Exception as e:
            tree = self.query_one("#node-tree", Tree)
            tree.root.add(f"Error: {e}")


class PatternDetectionWidget(Static):
    """Widget for detecting and displaying suspicious patterns."""

    DEFAULT_CSS = """
    PatternDetectionWidget {
        height: auto;
        min-height: 10;
        padding: 1;
        border: solid $primary;
    }
    """

    def __init__(self, db: Any | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.db = db

    def on_mount(self):
        self.update("Click 'Detect Patterns' to analyze network")

    def detect_self_loops(self):
        """Detect nodes with self-loops."""
        if self.db is None:
            try:
                from memgraph_toolbox.api.memgraph import Memgraph

                self.db = Memgraph()
            except Exception as e:
                self.update(f"[red]Error: {e}[/red]")
                return

        try:
            result = self.db.query("""
                MATCH (n)-[r]->(n)
                RETURN n.id as id, type(r) as rel_type, count(r) as count
                LIMIT 20
            """)

            if not result:
                self.update("[green]No self-loops detected[/green]")
                return

            lines = ["🔴 Self-Loop Patterns Detected", "─" * 40]
            for row in result:
                lines.append(f"  {row['id']}: {row['rel_type']} ({row['count']}x)")

            self.update("\n".join(lines))

        except Exception as e:
            self.update(f"[red]Error: {e}[/red]")

    def detect_spiderwebs(self):
        """Detect spiderweb patterns (hub nodes)."""
        if self.db is None:
            return

        try:
            result = self.db.query("""
                MATCH (n)--(neighbor)
                WITH n, count(DISTINCT neighbor) as degree
                WHERE degree >= 10
                RETURN n.id as id, degree
                ORDER BY degree DESC
                LIMIT 15
            """)

            if not result:
                self.update("[green]No suspicious hub patterns[/green]")
                return

            lines = ["🕸️ Spiderweb Patterns (Hub Nodes)", "─" * 40]
            for row in result:
                lines.append(f"  {row['id']}: {row['degree']} connections")

            self.update("\n".join(lines))

        except Exception as e:
            self.update(f"[red]Error: {e}[/red]")

    def detect_cliques(self):
        """Detect cliques (fully connected groups)."""
        if self.db is None:
            return

        try:
            # Simple triangle detection
            result = self.db.query("""
                MATCH (a)--(b)--(c)--(a)
                WHERE a.id < b.id AND b.id < c.id
                RETURN a.id as a, b.id as b, c.id as c
                LIMIT 10
            """)

            if not result:
                self.update("[green]No clique patterns detected[/green]")
                return

            lines = ["👥 Clique Patterns (Triangular)", "─" * 40]
            for row in result:
                lines.append(f"  {row['a']} ↔ {row['b']} ↔ {row['c']}")

            self.update("\n".join(lines))

        except Exception as e:
            self.update(f"[red]Error: {e}[/red]")
