"""
openfraud/tui/graph_screen.py
Main fraud graph analysis screen for Textual TUI.
"""

from __future__ import annotations

from typing import Any, ClassVar

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Static,
    TabbedContent,
    TabPane,
)

from openfraud.tui.widgets import (
    ASCIINetworkGraph,
    FraudCommunityHeatmap,
    GraphStatsWidget,
    NodeExplorerWidget,
    PatternDetectionWidget,
    RiskNodeTable,
)


class FraudGraphScreen(Screen):
    """Main screen for fraud network graph analysis."""
    
    TITLE = "🔍 Fraud Network Analysis"
    
    BINDINGS: ClassVar = [
        Binding("r", "refresh_all", "Refresh", show=True),
        Binding("1", "focus_stats", "Stats", show=True),
        Binding("2", "focus_nodes", "Risk Nodes", show=True),
        Binding("3", "focus_graph", "Network", show=True),
        Binding("4", "focus_explorer", "Explorer", show=True),
        Binding("q", "go_back", "Back", show=True),
        Binding("s", "detect_self_loops", "Self-Loops", show=False),
        Binding("w", "detect_spiderwebs", "Spiderwebs", show=False),
        Binding("c", "detect_cliques", "Cliques", show=False),
    ]
    
    def __init__(self, db: Any | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.db = db
    
    def compose(self):
        """Compose the screen layout."""
        yield Header()
        
        with Horizontal():
            # Left sidebar with controls and stats
            with Vertical(id="graph-sidebar", classes="sidebar"):
                yield Static("Graph Analysis", classes="sidebar-title")
                
                # Quick action buttons
                yield Button("🔄 Refresh All", id="refresh-all", variant="primary")
                yield Button("🔍 Find Self-Loops", id="btn-self-loops")
                yield Button("🕸️ Find Spiderwebs", id="btn-spiderwebs")
                yield Button("👥 Detect Cliques", id="btn-cliques")
                yield Button("📊 Calculate PageRank", id="btn-pagerank")
                yield Button("🏘️ Detect Communities", id="btn-communities")
                
                # Stats widget
                yield GraphStatsWidget(id="graph-stats", db=self.db)
            
            # Main content area with tabs
            with TabbedContent(id="graph-tabs"):
                # Tab 1: Risk Analysis
                with TabPane("Risk Nodes", id="tab-risk"):
                    with Vertical():
                        yield Static("High-Risk Nodes by PageRank × Fraud Score", classes="tab-title")
                        yield RiskNodeTable(id="risk-table", db=self.db)
                
                # Tab 2: Network Visualization
                with TabPane("Network View", id="tab-network"):
                    with Horizontal():
                        with Vertical():
                            yield Static("Network Structure", classes="tab-title")
                            yield ASCIINetworkGraph(id="ascii-graph", db=self.db)
                        with Vertical():
                            yield Static("Community Analysis", classes="tab-title")
                            yield FraudCommunityHeatmap(id="community-heatmap", db=self.db)
                
                # Tab 3: Pattern Detection
                with TabPane("Patterns", id="tab-patterns"):
                    with Horizontal():
                        yield PatternDetectionWidget(id="pattern-widget", db=self.db)
                        with Vertical():
                            yield Static("Pattern Legend", classes="tab-title")
                            yield Static("""
Self-Loops: Nodes connected to themselves
• Indicates: Wash trading, self-billing
• Severity: HIGH

Spiderwebs: Hub nodes with many leaves
• Indicates: Billing mills, coordinators
• Severity: MEDIUM-HIGH

Cliques: Fully connected subgraphs
• Indicates: Collusion rings
• Severity: HIGH

Communities: Dense subgraphs
• Fraud Rate >50%: Investigate all
• Fraud Rate 20-50%: Review leaders
• Fraud Rate <20%: Monitor
                            """, id="pattern-legend")
                
                # Tab 4: Node Explorer
                with TabPane("Node Explorer", id="tab-explorer"):
                    yield NodeExplorerWidget(id="node-explorer", db=self.db)
        
        yield Footer()
    
    def on_mount(self):
        """Initialize screen on mount."""
        self.update_styles()
    
    def update_styles(self):
        """Apply custom styles."""
        self.styles.layout = "vertical"
    
    # ─────────────────────────────────────────────────────────────────
    # Action Handlers
    # ─────────────────────────────────────────────────────────────────
    
    def action_refresh_all(self):
        """Refresh all widgets."""
        self.notify("Refreshing all graph data...", severity="information")
        
        # Refresh all widgets
        stats_widget = self.query_one("#graph-stats", GraphStatsWidget)
        stats_widget.refresh_stats()
        
        risk_table = self.query_one("#risk-table", RiskNodeTable)
        risk_table.refresh_data()
        
        heatmap = self.query_one("#community-heatmap", FraudCommunityHeatmap)
        heatmap.refresh_heatmap()
        
        ascii_graph = self.query_one("#ascii-graph", ASCIINetworkGraph)
        ascii_graph.render_graph()
        
        self.notify("Refresh complete!", severity="success")
    
    def action_go_back(self):
        """Navigate back."""
        self.app.pop_screen()
    
    def action_focus_stats(self):
        """Focus stats tab."""
        tabs = self.query_one("#graph-tabs", TabbedContent)
        tabs.active = "tab-risk"
    
    def action_focus_nodes(self):
        """Focus risk nodes tab."""
        tabs = self.query_one("#graph-tabs", TabbedContent)
        tabs.active = "tab-risk"
    
    def action_focus_graph(self):
        """Focus network view tab."""
        tabs = self.query_one("#graph-tabs", TabbedContent)
        tabs.active = "tab-network"
    
    def action_focus_explorer(self):
        """Focus explorer tab."""
        tabs = self.query_one("#graph-tabs", TabbedContent)
        tabs.active = "tab-explorer"
    
    # ─────────────────────────────────────────────────────────────────
    # Pattern Detection Actions
    # ─────────────────────────────────────────────────────────────────
    
    def action_detect_self_loops(self):
        """Detect self-loop patterns."""
        pattern_widget = self.query_one("#pattern-widget", PatternDetectionWidget)
        pattern_widget.detect_self_loops()
        
        # Switch to patterns tab
        tabs = self.query_one("#graph-tabs", TabbedContent)
        tabs.active = "tab-patterns"
    
    def action_detect_spiderwebs(self):
        """Detect spiderweb patterns."""
        pattern_widget = self.query_one("#pattern-widget", PatternDetectionWidget)
        pattern_widget.detect_spiderwebs()
        
        tabs = self.query_one("#graph-tabs", TabbedContent)
        tabs.active = "tab-patterns"
    
    def action_detect_cliques(self):
        """Detect clique patterns."""
        pattern_widget = self.query_one("#pattern-widget", PatternDetectionWidget)
        pattern_widget.detect_cliques()
        
        tabs = self.query_one("#graph-tabs", TabbedContent)
        tabs.active = "tab-patterns"
    
    # ─────────────────────────────────────────────────────────────────
    # Button Handlers
    # ─────────────────────────────────────────────────────────────────
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "refresh-all":
            self.action_refresh_all()
        
        elif button_id == "btn-self-loops":
            self.action_detect_self_loops()
        
        elif button_id == "btn-spiderwebs":
            self.action_detect_spiderwebs()
        
        elif button_id == "btn-cliques":
            self.action_detect_cliques()
        
        elif button_id == "btn-pagerank":
            self._calculate_pagerank()
        
        elif button_id == "btn-communities":
            self._detect_communities()
    
    def _calculate_pagerank(self):
        """Calculate PageRank for all nodes."""
        if self.db is None:
            try:
                from memgraph_toolbox.api.memgraph import Memgraph
                self.db = Memgraph()
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
                return
        
        try:
            self.notify("Calculating PageRank...", severity="information")
            
            # Run PageRank algorithm
            self.db.query("""
                CALL pagerank.get()
                YIELD node, rank
                SET node.pagerank = rank
            """)
            
            self.notify("PageRank calculation complete!", severity="success")
            
            # Refresh risk table
            risk_table = self.query_one("#risk-table", RiskNodeTable)
            risk_table.refresh_data()
        
        except Exception as e:
            self.notify(f"Error calculating PageRank: {e}", severity="error")
    
    def _detect_communities(self):
        """Detect communities using Louvain algorithm."""
        if self.db is None:
            try:
                from memgraph_toolbox.api.memgraph import Memgraph
                self.db = Memgraph()
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
                return
        
        try:
            self.notify("Detecting communities...", severity="information")
            
            # Run Louvain community detection
            self.db.query("""
                CALL community_detection.get()
                YIELD node, community_id
                SET node.community_id = community_id
            """)
            
            self.notify("Community detection complete!", severity="success")
            
            # Refresh heatmap
            heatmap = self.query_one("#community-heatmap", FraudCommunityHeatmap)
            heatmap.refresh_heatmap()
            
            # Refresh stats
            stats = self.query_one("#graph-stats", GraphStatsWidget)
            stats.refresh_stats()
        
        except Exception as e:
            self.notify(f"Error detecting communities: {e}", severity="error")


class GraphDetailScreen(Screen):
    """Detail screen for viewing specific node information."""
    
    TITLE = "Node Details"
    
    BINDINGS = [
        Binding("q", "go_back", "Back", show=True),
        Binding("n", "show_neighbors", "Neighbors", show=True),
        Binding("p", "show_path", "Shortest Path", show=True),
    ]
    
    def __init__(self, node_id: str, db: Any | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.node_id = node_id
        self.db = db
    
    def compose(self):
        """Compose the detail screen."""
        yield Header()
        
        with Vertical():
            yield Static(f"Node: {self.node_id}", classes="detail-title")
            
            with Horizontal():
                # Left: Node properties
                with Vertical():
                    yield Static("Properties", classes="section-title")
                    yield DataTable(id="node-properties")
                
                # Right: Connections
                with Vertical():
                    yield Static("Connections", classes="section-title")
                    yield DataTable(id="node-connections")
        
        yield Footer()
    
    def on_mount(self):
        """Load node details on mount."""
        self._load_node_details()
    
    def _load_node_details(self):
        """Load and display node details."""
        if self.db is None:
            try:
                from memgraph_toolbox.api.memgraph import Memgraph
                self.db = Memgraph()
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
                return
        
        try:
            # Load properties
            result = self.db.query("""
                MATCH (n {id: $id})
                RETURN n, labels(n) as labels
            """, {"id": self.node_id})
            
            props_table = self.query_one("#node-properties", DataTable)
            props_table.add_columns("Property", "Value")
            
            if result:
                node = result[0]['n']
                labels = result[0].get('labels', [])
                
                props_table.add_row("ID", self.node_id)
                props_table.add_row("Labels", ", ".join(labels))
                
                for key, value in sorted(node.items()):
                    if key != 'id':
                        if isinstance(value, float):
                            value_str = f"{value:.4f}"
                        else:
                            value_str = str(value)
                        props_table.add_row(key, value_str)
            
            # Load connections
            connections = self.db.query("""
                MATCH (n {id: $id})-[r]-(neighbor)
                RETURN neighbor.id as neighbor_id,
                       type(r) as rel_type,
                       neighbor.fraud_score as neighbor_risk,
                       neighbor.is_fraud as neighbor_is_fraud
                LIMIT 50
            """, {"id": self.node_id})
            
            conn_table = self.query_one("#node-connections", DataTable)
            conn_table.add_columns("Connected To", "Relationship", "Risk")
            
            for conn in connections:
                risk = conn.get('neighbor_risk', 0)
                is_fraud = conn.get('neighbor_is_fraud', False)
                
                if is_fraud:
                    risk_str = "[red]🔴 CONFIRMED FRAUD[/red]"
                elif risk and risk > 0.5:
                    risk_str = f"[orange1]🟠 HIGH ({risk:.2f})[/orange1]"
                elif risk and risk > 0.2:
                    risk_str = f"[yellow]🟡 MEDIUM ({risk:.2f})[/yellow]"
                else:
                    risk_str = "[green]🟢 LOW[/green]"
                
                conn_table.add_row(
                    conn['neighbor_id'],
                    conn['rel_type'],
                    risk_str
                )
        
        except Exception as e:
            self.notify(f"Error loading details: {e}", severity="error")
    
    def action_go_back(self):
        """Go back to main graph screen."""
        self.app.pop_screen()
    
    def action_show_neighbors(self):
        """Show neighbors in ASCII graph."""
        # This would navigate back to main screen with node selected
        self.app.pop_screen()
        # Could emit a message to select this node
    
    def action_show_path(self):
        """Show shortest path to another node (placeholder)."""
        self.notify("Shortest path feature: Enter target node ID", severity="information")
