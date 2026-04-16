# OpenFraud: Universal Investigation Workbench
## The Swiss Army Knife for Entity, Threat & Fraud Hunting

### Vision Statement

**Any data. Any investigation. One tool.**

A unified, open-source investigation platform that handles:
- **Millions of PDFs/TIFFs** (Epstein files, FOIA dumps)
- **Structured data** (227M row Parquet, CSVs, spreadsheets)
- **Mixed sources** (logs + emails + documents)
- **Any domain** (fraud, threats, leaks, audits)

### The Problem with Current Tools

| Investigation Type | Current Tools | Problems |
|-------------------|---------------|----------|
| Document leaks | Manual review + regex scripts | Slow, inconsistent, not scalable |
| Healthcare fraud | Excel + basic stats | Can't see networks, miss patterns |
| Cyber threat hunting | Splunk + manual correlation | Expensive, steep learning curve |
| Financial audit | Palantir ($$$$) + consultants | Prohibitively expensive |

**Solution:** One tool that adapts to any data type and investigation style.

---

## The Universal Investigation Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIVERSAL INVESTIGATION PIPELINE               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐  │
│  │  INGEST  │──▶│ EXTRACT  │──▶│ CONNECT  │──▶│   ANALYZE    │  │
│  └──────────┘   └──────────┘   └──────────┘   └──────────────┘  │
│       │              │              │              │             │
│       ▼              ▼              ▼              ▼             │
│  Drop files    Extract         Build          Run forensic      │
│  (any format)  entities        graph          rules + ML        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         VISUALIZE & REPORT                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │   Graph    │  │  Timeline  │  │Risk Ranking│  │  Evidence  │ │
│  │   View     │  │    View    │  │   Table    │  │   Export   │ │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Use Case Examples

### Use Case 1: Epstein Files (Document-Heavy)

**Data:** 1 million+ PDFs/TIFFs from FOIA requests

**Workflow:**
```
1. INGEST: Drag folder → Auto-detect PDFs/TIFFs → Progress bar

2. EXTRACT: VLM (Qwen2-VL) reads each page:
   - Names in FROM/TO fields
   - Flight numbers
   - Dates
   - Locations
   - Dollar amounts
   
3. CONNECT:
   - Same flight number → "flew together"
   - Same date + location → "attended same event"
   - Mentioned in same document → "associated"
   - Phone numbers match → "contact"
   
4. ANALYZE:
   - Benford's Law on flight frequencies
   - Network: Who flew together most? (PageRank)
   - Timeline: Pattern of island visits
   - Communities: Social circles
   
5. VISUALIZE:
   - Graph: People → Flights → Locations
   - Heatmap: Visit frequency by date
   - Risk table: Who has most connections?
   
6. REPORT:
   - Export flight logs with suspicious patterns
   - Generate social network map
   - Timeline of key events
```

**Key Finding Example:**
"Jeffrey Epstein flew with [Person A] 47 times between 2002-2008, 
always to the same island location on weekends."

---

### Use Case 2: Medicaid Fraud (Structured Data)

**Data:** 227M row Parquet file of healthcare claims

**Workflow:**
```
1. INGEST: Select Parquet → Preview columns → Confirm

2. EXTRACT: Column mapping wizard:
   - billing_npi → Provider ID
   - total_paid_amount → Transaction Amount
   - claim_date → Date
   - hcpcs_code → Procedure
   
3. CONNECT:
   - Same provider + same beneficiary → Service relationship
   - Same provider type → Peer group
   - Geographic proximity → Location cluster
   
4. ANALYZE:
   - Benford's Law on billing amounts
   - Velocity: Claims per beneficiary (impossible frequencies)
   - Peer Z-scores: Outliers within specialty
   - Graph: Provider → Beneficiary network
   
5. VISUALIZE:
   - Fraud heatmap by community
   - Risk-ranked provider list
   - Billing pattern timeline
   - Network: Billing mills as hubs
   
6. REPORT:
   - List of 3,289 high-risk providers
   - $896B exposure analysis
   - Investigative priorities
```

**Key Finding Example:**
"Provider ENT_00123 billed $6.83B with 1,000+ claims/beneficiary 
(mathematically impossible). Network shows 47 connected providers 
in same shell company."

---

### Use Case 3: Cyber Threat Hunting (Mixed Data)

**Data:** Firewall logs + email exports + suspicious documents

**Workflow:**
```
1. INGEST: Multiple file types simultaneously

2. EXTRACT:
   - Logs: IPs, domains, timestamps, user agents
   - Emails: Sender, recipient, attachments, links
   - Documents: Embedded URLs, metadata
   
3. CONNECT:
   - Same IP → Same attacker
   - Domain resolution → Infrastructure
   - Email thread → Communication chain
   - Attachment hash → Malware family
   
4. ANALYZE:
   - Beaconing detection (regular intervals)
   - Lateral movement paths (graph traversal)
   - Data exfiltration (volume + timing)
   - C2 communication patterns
   
5. VISUALIZE:
   - Attack graph: Entry → Pivot → Exfil
   - Timeline: Attack progression
   - Geo-map: Attacker infrastructure locations
   - Risk: Asset criticality × exposure
   
6. REPORT:
   - Incident timeline
   - IOC list for blocking
   - Affected systems
   - Recommended remediation
```

**Key Finding Example:**
"Attacker used 3 compromised accounts to access 47 systems over 
14 days. Beaconing detected every 300 seconds to 185.220.101.x."

---

## Technical Architecture

### Data Adapter Layer

```python
# Unified interface for any data source
class DataAdapter(ABC):
    @abstractmethod
    def ingest(self, source: Path) -> Iterator[RawRecord]:
        pass
    
    @abstractmethod  
    def get_schema(self) -> Schema:
        pass

class DocumentAdapter(DataAdapter):
    """PDFs, TIFFs, images → OCR + VLM"""
    def ingest(self, source):
        for page in extract_pages(source):
            text = ocr(page)
            image_features = vlm_encode(page)
            yield RawRecord(text=text, image=image_features)

class TableAdapter(DataAdapter):
    """CSV, Parquet, Excel → Rows"""
    def ingest(self, source):
        df = pandas.read_parquet(source)
        for row in df.iterrows():
            yield RawRecord(data=row)

class LogAdapter(DataAdapter):
    """Logs → Parsed events"""
    def ingest(self, source):
        for line in tail(source):
            parsed = parse_log_line(line)
            yield RawRecord(event=parsed)
```

### Entity Extractor Layer

```python
class EntityExtractor(ABC):
    @abstractmethod
    def extract(self, record: RawRecord) -> List[Entity]:
        pass

class VLMExtractor(EntityExtractor):
    """Vision Language Model for documents"""
    def extract(self, record):
        # Use OCR My Junk's VLM pipeline
        prompt = "Extract all people, dates, locations, amounts"
        result = vlm_client.classify(record.image, prompt)
        return parse_entities(result)

class TableExtractor(EntityExtractor):
    """Column mapping for structured data"""
    def __init__(self, column_map: Dict[str, str]):
        self.mapping = column_map
    
    def extract(self, record):
        entity = Entity(
            id=record.data[self.mapping['id_column']],
            type=self.mapping['entity_type'],
            properties={
                k: record.data[v] 
                for k, v in self.mapping['properties'].items()
            }
        )
        return [entity]

class PatternExtractor(EntityExtractor):
    """Regex patterns for logs/emails"""
    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'ip': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    }
    
    def extract(self, record):
        entities = []
        for entity_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, record.text):
                entities.append(Entity(
                    type=entity_type,
                    value=match.group()
                ))
        return entities
```

### Graph Builder Layer

```python
class GraphBuilder:
    def __init__(self, db: Memgraph):
        self.db = db
    
    def add_entity(self, entity: Entity):
        """Add node to graph"""
        query = """
        MERGE (n:Entity {id: $id})
        SET n.type = $type
        SET n += $properties
        """
        self.db.query(query, {
            'id': entity.id,
            'type': entity.type,
            'properties': entity.properties
        })
    
    def link_entities(self, rel: Relationship):
        """Add relationship to graph"""
        query = """
        MATCH (a:Entity {id: $from_id})
        MATCH (b:Entity {id: $to_id})
        MERGE (a)-[r:RELATES {type: $rel_type}]->(b)
        SET r += $properties
        """
        self.db.query(query, {
            'from_id': rel.from_id,
            'to_id': rel.to_id,
            'rel_type': rel.type,
            'properties': rel.properties
        })
    
    def infer_relationships(self, rule: LinkingRule):
        """Auto-create links based on rules"""
        if rule.type == 'same_attribute':
            query = """
            MATCH (a:Entity), (b:Entity)
            WHERE a[$attr] = b[$attr] AND a.id < b.id
            MERGE (a)-[:SAME {attribute: $attr}]-(b)
            """
            self.db.query(query, {'attr': rule.attribute})
```

---

## TUI Screen Design

### Screen 1: Data Import (The "Inbox")

```
┌────────────────────────────────────────────────────────────┐
│  OpenFraud Investigation Workbench                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  📁 DATA IMPORT                                            │
│                                                            │
│  [Drop files here]                    [Browse...]          │
│                                                            │
│  Import Queue:                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ ✓ flight_logs.pdf      1.2MB    PDF    47 pages     │ │
│  │ ✓ medicaid_data.parquet  890MB  Parquet  227M rows  │ │
│  │ ◐ emails_export.pst    4.5GB    PST    [████░░░░░]  │ │
│  │ ...                                                  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Detected Types: 3 PDFs, 1 Parquet, 1 PST                  │
│                                                            │
│  [Cancel]                              [Continue →]        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Features:**
- Drag & drop or file browser
- Progress bars for large files
- Auto-detect file types
- Preview sample data
- Estimated processing time

---

### Screen 2: Entity Configuration (The "Mapping")

```
┌────────────────────────────────────────────────────────────┐
│  Configure Entity Extraction                               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  📄 flight_logs.pdf (PDF Document)                         │
│                                                            │
│  What entities should we extract?                          │
│  [✓] People names      [✓] Dates      [✓] Locations       │
│  [✓] Flight numbers    [ ] Dollar amounts                  │
│                                                            │
│  Preview (first page):                                   │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ FROM: Jeffrey Epstein                                │ │
│  │ TO:   Ghislaine Maxwell                              │ │
│  │ FLIGHT: N908JE                                       │ │
│  │ DATE:  2005-03-15                                    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  📊 medicaid_data.parquet (Structured)                     │
│                                                            │
│  Map columns to entity properties:                         │
│  ┌─────────────────────┬────────────────────────────────┐ │
│  │ Entity Property     │ Source Column                  │ │
│  ├─────────────────────┼────────────────────────────────┤ │
│  │ Provider ID         │ ▼ billing_npi                  │ │
│  │ Transaction Amount  │ ▼ total_paid_amount            │ │
│  │ Date                │ ▼ claim_date                   │ │
│  │ Procedure           │ ▼ hcpcs_code                   │ │
│  └─────────────────────┴────────────────────────────────┘ │
│                                                            │
│  [Quick Start: Healthcare Fraud]  [Use Template...]        │
│                                                            │
│  [← Back]                              [Continue →]        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Features:**
- Visual column mapper for structured data
- Checkboxes for document entity types
- Live preview of extraction
- Investigation templates
- Sensible defaults per file type

---

### Screen 3: Graph Construction (The "Connect")

```
┌────────────────────────────────────────────────────────────┐
│  Build Relationship Graph                                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Entities Found: 45,230 nodes                              │
│                                                            │
│  Configure linking rules:                                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ [✓] Link if same phone number                        │ │
│  │ [✓] Link if same email address                       │ │
│  │ [✓] Link if same physical address                    │ │
│  │ [✓] Link if appear in same document                  │ │
│  │ [ ] Link if within 30 days and same location         │ │
│  │ [+] Add custom rule...                               │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Entity Normalization:                                     │
│  [✓] Normalize names (J. Smith → John Smith)             │
│  [✓] Standardize addresses                               │
│  [✓] Deduplicate similar entities                        │ │
│                                                            │
│  Building graph...  [████████████████████░░░░░] 67%      │ │
│  Nodes: 45,230  |  Edges: 128,456  |  Time: 00:03:42      │
│                                                            │
│  [← Back]                              [Continue →]        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Features:**
- Checkbox linking rules
- Entity normalization options
- Progress bar during construction
- Live node/edge counts
- Cancel and resume capability

---

### Screen 4: Analysis Dashboard (The "Investigate")

```
┌────────────────────────────────────────────────────────────┐
│  Investigation Dashboard                             [?]   │
├────────────────────────────────────────────────────────────┤
│  [1 Risk] [2 Network] [3 Timeline] [4 Patterns] [5 Export] │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 🔴 TOP RISK ENTITIES                                 │ │
│  │                                                      │ │
│  │ Rank │ Entity          │ Risk │ Connections │ Flags │ │
│  │──────┼─────────────────┼──────┼─────────────┼───────│ │
│  │  1   │ Jeffrey Epstein │ 98%  │ 1,247       │ 23    │ │
│  │  2   │ Ghislaine Max.. │ 94%  │ 892         │ 18    │ │
│  │  3   │ N908JE (Flight) │ 87%  │ 456         │ 12    │ │
│  │  4   │ Little St James │ 82%  │ 678         │ 9     │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────┐  ┌────────────────────────┐ │
│  │ 🕸️ NETWORK VISUALIZATION │  │ 🏘️ COMMUNITY HEATMAP  │ │
│  │                          │  │                        │ │
│  │       ┌─────────┐        │  │ Circle 42: ████████░   │ │
│  │       │ J. Epst │        │  │ 87% fraud (13/15)     │ │
│  │       └────┬────┘        │  │                        │ │
│  │    ┌───────┼───────┐    │  │ Circle 15: ████░░░░░   │ │
│  │    ▼       ▼       ▼    │  │ 45% fraud (9/20)      │ │
│  │ [G.Max] [N908JE] [St.J] │  │                        │ │
│  │                          │  │ Circle 8:  █░░░░░░░░   │ │
│  └──────────────────────────┘  │ 12% fraud (3/25)      │ │
│                                 └────────────────────────┘ │
│                                                            │
│  [🔄 Refresh]  [🔍 Search]  [⚡ Detect Patterns]  [📊 Export] │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Features:**
- Tabbed interface (already built!)
- Risk-ranked entity table
- ASCII network visualization
- Community fraud heatmap
- Pattern detection buttons
- Search functionality

---

### Screen 5: Evidence Export (The "Report")

```
┌────────────────────────────────────────────────────────────┐
│  Export Findings                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Select findings to include:                               │
│                                                            │
│  [✓] Top 100 high-risk entities                          │
│  [✓] Suspicious network clusters (3 found)                 │
│  [✓] Timeline of key events                                │
│  [✓] Supporting documents (47 files)                       │
│  [ ] Full graph data (large)                               │
│  [ ] Raw extraction data                                   │
│                                                            │
│  Export Format:                                            │
│  (•) PDF Investigation Report                              │
│  ( ) Excel Workbook                                        │
│  ( ) JSON Data Package                                     │
│  ( ) GraphML for Gephi/Neo4j                               │
│                                                            │
│  Report Options:                                           │
│  [✓] Include visualizations                                │
│  [✓] Include evidence citations                            │
│  [✓] Redact PII (except subjects)                          │
│  [ ] Password protect                                      │
│                                                            │
│  Estimated size: 45 MB  |  Generation time: ~2 minutes     │
│                                                            │
│  [← Back]                              [Generate Report]   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Features:**
- Checkbox selection of findings
- Multiple export formats
- Redaction options
- Password protection
- Progress tracking

---

## Investigation Templates

### Template: Healthcare Fraud

```yaml
template_name: "Healthcare Fraud Investigation"
description: "Detect billing fraud, upcoding, and provider collusion"

data_adapters:
  - type: table
    formats: [parquet, csv, excel]

entity_extraction:
  entity_type: provider
  id_column: billing_npi
  properties:
    - amount: total_paid_amount
    - date: claim_date
    - procedure: hcpcs_code
    - beneficiary_count: total_beneficiary_count

linking_rules:
  - type: same_beneficiary
    description: "Same patient seen by multiple providers"
  - type: peer_group
    attribute: specialty_code
    description: "Providers in same specialty"

analysis_rules:
  - type: benford_law
    field: amount
    threshold: 0.1
  - type: velocity
    field: claims_per_beneficiary
    max: 31
  - type: peer_outlier
    field: amount
    z_threshold: 3.0

risk_weights:
  benford_violation: 0.25
  velocity_violation: 0.30
  peer_outlier: 0.20
  network_centrality: 0.25
```

### Template: Document Leak Investigation

```yaml
template_name: "Document Leak Analysis"
description: "Analyze FOIA dumps, email leaks, document collections"

data_adapters:
  - type: document
    formats: [pdf, tiff, png, jpg]

entity_extraction:
  use_vlm: true
  extract:
    - person_names
    - organizations
    - locations
    - dates
    - amounts
    - phone_numbers
    - email_addresses

linking_rules:
  - type: same_document
    description: "Entities appearing together"
  - type: temporal_proximity
    days: 7
    description: "Events within 7 days"
  - type: shared_contact
    field: email_address

analysis_rules:
  - type: network_centrality
    algorithm: pagerank
  - type: community_detection
    algorithm: louvain
  - type: temporal_clustering
    window: 30_days

visualization:
  primary: network_graph
  secondary: timeline
  tertiary: geographic_map
```

---

## Implementation Roadmap

### Phase 1: Foundation (P0 - Core)
**Timeline: 2-3 weeks**

- [ ] Data adapters (CSV, Parquet, JSON)
- [ ] Table entity extractor with column mapper
- [ ] Graph builder with linking rules
- [ ] Basic TUI screens (Import, Config, Dashboard)
- [ ] Integration with existing FraudGraphScreen

**Deliverable:** Working platform for structured data investigations

### Phase 2: Documents (P1 - Extension)
**Timeline: 3-4 weeks**

- [ ] Document adapter (PDF, TIFF)
- [ ] VLM integration (OCR My Junk bridge)
- [ ] Document entity extractor
- [ ] Content-addressed storage
- [ ] Full 5-screen TUI workflow

**Deliverable:** Support for document-heavy investigations

### Phase 3: Intelligence (P2 - Advanced)
**Timeline: 2-3 weeks**

- [ ] Investigation templates system
- [ ] Timeline view widget
- [ ] Geographic visualization
- [ ] Advanced pattern detection
- [ ] Report generation

**Deliverable:** Production-ready platform with templates

### Phase 4: Polish (P3 - Hardening)
**Timeline: 2 weeks**

- [ ] Performance optimization (1M+ document support)
- [ ] Error handling & recovery
- [ ] User onboarding tutorials
- [ ] Documentation
- [ ] Example investigations

**Deliverable:** Release-ready open-source project

---

## Key Differentiators

### vs Palantir
| Feature | Palantir | OpenFraud |
|---------|----------|-----------|
| Cost | $$$$ (prohibitively expensive) | Free (open source) |
| Setup | Weeks of consulting | `docker-compose up` |
| Customization | Limited | Full source code |
| TUI | Web-based | Terminal-native |

### vs Splunk
| Feature | Splunk | OpenFraud |
|---------|--------|-----------|
| Data type | Logs only | Any format |
| Analysis | Statistical | Graph + ML + Forensic |
| Visualization | Dashboards | Interactive graph |
| Cost | $$$ per GB | Free |

### vs Neo4j
| Feature | Neo4j | OpenFraud |
|---------|-------|-----------|
| Focus | Generic graph | Investigation-optimized |
| Data ingest | Manual ETL | Automated pipelines |
| Analysis | Queries | Built-in algorithms |
| TUI | Browser | Terminal |

---

## Resume Value

**For Data Science / ML Engineer:**
- "Architected universal investigation platform processing millions of documents and structured records"
- "Built multi-modal data pipeline supporting PDFs, Parquet, CSV, and logs"
- "Implemented entity extraction with VLM (Vision Language Models) and graph neural networks"

**For Security Engineer:**
- "Developed threat hunting platform with graph-based attack chain analysis"
- "Created fraud detection system identifying 16x more anomalies than traditional tools"
- "Built real-time network analysis for insider threat detection"

**For Data Engineer:**
- "Engineered scalable ETL pipeline processing 227M+ records with DuckDB and Memgraph"
- "Designed pluggable data adapter architecture supporting 10+ file formats"
- "Built reactive TUI with Textual for real-time investigation workflows"

---

## Next Steps

1. **Start with Phase 1:** Build structured data pipeline first
2. **Leverage existing code:** Reuse OpenFraud core + TUI widgets
3. **Add OCR My Junk bridge:** Document extraction using VLM
4. **Create templates:** Healthcare, Document, Threat Hunt
5. **Document everything:** README, tutorials, examples

**Call to Action:**
This becomes THE open-source alternative to expensive investigative platforms. A true "Swiss Army Knife" that any analyst can use for any investigation.

Ready to build the foundation?