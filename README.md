# THOR

**THOR** is a Python framework for searching, classifying and ranking astronomical transient candidates by combining classifications from multiple community brokers.

THOR retrieves classifications from **Fink**, **ALeRCE**, and **Lasair**, reconciles their heterogeneous taxonomies into a common classification scheme, computes a consensus classification, and produces a ranked list of candidates.

The framework is designed to support the rapid identification of transient events such as supernovae (SN), superluminous supernovae (SLSNe), tidal disruption events (TDEs), and other astronomical transients.

---

## Features

- Multi-broker transient search
- Unified taxonomy across brokers
- Consensus classification
- Candidate ranking
- Cross-match information
- Modular architecture for future broker integration

---

## Workflow

```
          Alert

             │
             ▼

    ┌─────────────────┐
    │   Fink Broker   │
    ├─────────────────┤
    │  ALeRCE Broker  │
    ├─────────────────┤
    │  Lasair Broker  │
    └─────────────────┘

             │
             ▼

 Taxonomy Reconciliation

             │
             ▼

 Consensus Classification

             │
             ▼

   Candidate Ranking

             │
             ▼

 Ranked Candidate List
```
## Documentation

The complete documentation is available at

**https://fabioragosta.github.io/THOR/**

It includes:

- Installation guide
- Quick start tutorial
- User guide
- API reference
- Examples
---

# Installation

Clone the repository

```bash
git clone https://github.com/FabioRagosta/thor.git
cd thor
```

Install the required dependencies

```bash
pip install -e .
```

(Installation via `pip` will be available in a future release.)

---

# Quick Start

```python
from thor.hunter import Hunter

hunter = Hunter(...)

results = hunter.search(...)

ranking = hunter.rank(results)

for candidate in ranking:
    print(candidate.objectId, candidate.consensus)
```

---

# Supported Brokers

| Broker | Supported |
|---------|-----------|
| Fink | ✓ |
| ALeRCE | ✓ |
| Lasair | ✓ |

---

# Scientific Background

THOR was developed to address the problem of combining heterogeneous classifications produced by independent astronomical brokers.

Rather than relying on a single broker, THOR reconciles different broker taxonomies into a common classification system and computes a consensus classification that can be used to prioritise transient candidates for follow-up observations.

The complete methodology is described in the accompanying publication.

---

# Documentation

The complete documentation, tutorials and API reference will be available through GitHub Pages.

---

# Citation

If you use THOR in your research, please cite the accompanying publication.

(BibTeX will be added after publication.)

---

# License

License information will be added before the first public release.
