# OpenFraud TUI Integration Guide

This guide shows how to integrate OpenFraud's graph visualization TUI into OCR My Junk's existing Textual TUI.

## 📁 Files Overview

```
openfraud/tui/
├── __init__.py          # Exports all components
├── app.py               # Standalone demo app
├── graph_screen.py      # Main fraud graph screen
└── widgets.py           # Individual TUI widgets
```

## 🚀 Quick Start (Standalone)

Run the OpenFraud TUI independently:

```bash
cd ~/Projects/python/openfraud

# Install dependencies
uv sync

# Start infrastructure
docker-compose up -d

# Launch TUI
openfraud
# Or: python -m openfraud.tui.app

# In the TUI:
# Press 'G' to open Graph Analysis
```

## 🔌 Integration with OCR My Junk

### Method 1: Add Screen to Existing App (Recommended)

Add the `FraudGraphScreen` to OCR My Junk's existing `ControlCenterApp`:

```python
# In ocr-my-junk/src/ocrmj_labeler/tui/app.py

from openfraud.tui.graph_screen import FraudGraphScreen

class ControlCenterApp(App[None]):
    # ... existing code ...
    
    BINDINGS = [
        # ... existing bindings ...
        Binding("6", "switch_screen('fraud_graph')", "Fraud Graph", show=True),
    ]
    
    def get_screen_classes(self):
        return {
            "dashboard": DashboardScreen,
            "runs": RunsScreen,
            "assets": AssetsScreen,
            "stats": StatsScreen,
            "settings": SettingsScreen,
            "fraud_graph": FraudGraphScreen,  # Add this!
        }
```

### Method 2: Import Individual Widgets

Use OpenFraud widgets in custom screens:

```python
from openfraud.tui.widgets import (
    GraphStatsWidget,
    RiskNodeTable,
    FraudCommunityHeatmap,
)

class MyCustomScreen(Screen):
    def compose(self):
        yield GraphStatsWidget()
        yield RiskNodeTable()
```

### Method 3: Side-by-Side Integration

Create a bridge screen that shows both OCR and fraud data:

```python
from ocrmj_labeler.tui.widgets import AssetTable
from openfraud.tui.widgets import RiskNodeTable

class UnifiedScreen(Screen):
    def compose(self):
        with Horizontal():
            with Vertical():
                yield Static("OCR Assets")
                yield AssetTable()  # From OCR My Junk
            
            with Vertical():
                yield Static("Fraud Analysis")
                yield RiskNodeTable()  # From OpenFraud
```

## 🎨 Customization

### Customizing Widgets

All widgets accept an optional `db` parameter:

```python
from memgraph_toolbox.api.memgraph import Memgraph

# Use custom database connection
db = Memgraph(url="bolt://custom-host:7687")

widget = GraphStatsWidget(db=db)
```

### Custom Styling

Add custom CSS to your app:

```python
class MyApp(App):
    CSS = """
    GraphStatsWidget {
        border: solid $primary;
        background: $surface-darken-1;
    }
    
    RiskNodeTable {
        height: 2fr;
    }
    """
```

## 🖥️ Widget Reference

### GraphStatsWidget

Displays key graph statistics.

```python
from openfraud.tui.widgets import GraphStatsWidget

# Usage
widget = GraphStatsWidget()

# Methods
widget.refresh_stats()  # Manually refresh from database
```

**Displays:**
- Total nodes
- Relationships
- Fraud count and rate
- Communities
- Network density

### RiskNodeTable

Table of high-risk nodes sorted by composite risk score.

```python
from openfraud.tui.widgets import RiskNodeTable

widget = RiskNodeTable()
```

**Columns:**
- Node ID
- PageRank
- Fraud Score
- Community
- Risk Level (color-coded)

### ASCIINetworkGraph

ASCII visualization of node connections.

```python
from openfraud.tui.widgets import ASCIINetworkGraph

widget = ASCIINetworkGraph()

# Set center node to visualize
widget.center_node = "ENT_00123"
```

### FraudCommunityHeatmap

ASCII heatmap of fraud rates by community.

```python
from openfraud.tui.widgets import FraudCommunityHeatmap

widget = FraudCommunityHeatmap()

# Refresh
widget.refresh_heatmap()
```

### NodeExplorerWidget

Interactive tree-based node explorer.

```python
from openfraud.tui.widgets import NodeExplorerWidget

widget = NodeExplorerWidget()
```

**Features:**
- Search by node ID
- Browse high-risk nodes
- View hub nodes (high PageRank)
- Explore connections

### PatternDetectionWidget

Detects and displays suspicious patterns.

```python
from openfraud.tui.widgets import PatternDetectionWidget

widget = PatternDetectionWidget()

# Detection methods
widget.detect_self_loops()
widget.detect_spiderwebs()
widget.detect_cliques()
```

## 🎮 Keyboard Shortcuts

### Main Graph Screen

| Key | Action |
|-----|--------|
| `1` | Focus Risk Nodes tab |
| `2` | Focus Network View tab |
| `3` | Focus Patterns tab |
| `4` | Focus Node Explorer tab |
| `r` | Refresh all data |
| `s` | Detect self-loops |
| `w` | Detect spiderwebs |
| `c` | Detect cliques |
| `q` | Go back |
| `?` | Show help |

## 📊 Example: Full Integration

```python
# ocr_fraud_bridge.py

from textual.app import App
from ocrmj_labeler.tui.app import ControlCenterApp as OCRApp
from openfraud.tui.graph_screen import FraudGraphScreen

class UnifiedFraudApp(OCRApp):
    """OCR My Junk + OpenFraud combined."""
    
    TITLE = "OCR + Fraud Analysis"
    
    BINDINGS = [
        *OCRApp.BINDINGS,
        ("f", "open_fraud", "Fraud Analysis"),
    ]
    
    def action_open_fraud(self):
        """Open fraud graph screen."""
        self.push_screen(FraudGraphScreen())

if __name__ == "__main__":
    app = UnifiedFraudApp()
    app.run()
```

## 🧪 Testing

Run the standalone TUI:

```bash
# From openfraud directory
python -m openfraud.tui.app

# Or after installation
openfraud
```

Test individual widgets:

```python
# test_widgets.py
from textual.app import App
from openfraud.tui.widgets import GraphStatsWidget

class TestApp(App):
    def compose(self):
        yield GraphStatsWidget()

if __name__ == "__main__":
    TestApp().run()
```

## 🐛 Troubleshooting

### Widget not displaying data

Check Memgraph connection:

```python
from memgraph_toolbox.api.memgraph import Memgraph

db = Memgraph()
try:
    result = db.query("RETURN 1 as test")
    print(f"Connected! {result}")
except Exception as e:
    print(f"Error: {e}")
```

### Styling issues

Ensure CSS is loaded:

```python
class MyApp(App):
    CSS = open("custom.css").read()  # Load custom styles
```

### Database errors

Widgets handle connection errors gracefully - they'll show an error message instead of crashing.

## 📚 Next Steps

1. **Try standalone**: `cd ~/Projects/python/openfraud && python -m openfraud.tui.app`
2. **Integrate widgets**: Add `GraphStatsWidget` to your existing screen
3. **Add full screen**: Integrate `FraudGraphScreen` into OCR My Junk
4. **Customize**: Modify styles and behavior for your use case

## 💡 Tips

- Widgets are **reactive** - they update automatically when data changes
- Use **reactive variables** for dynamic updates
- All widgets handle **database connection errors** gracefully
- The ASCII graph is **fully navigable** - click nodes to explore
- **Color coding**: Red=Critical, Yellow=High, Orange=Medium, Green=Low
