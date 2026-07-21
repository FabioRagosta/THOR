# THOR

## Transient Hunter ORchestrator

THOR is an open-source Python framework for the contextual classification and ranking of astronomical transient alerts.

The framework combines the classifications produced by multiple community brokers, reconciles heterogeneous taxonomic schemes into a common representation, and computes a consensus classification that can be tailored to specific scientific objectives. THOR is designed to assist the selection and prioritisation of transient candidates rather than replace broker classifications.

---

## Why THOR?

Modern time-domain surveys such as the Zwicky Transient Facility (ZTF) and, in the near future, the Vera C. Rubin Observatory generate enormous numbers of transient alerts every night. Several community brokers independently analyse these alerts, each adopting different machine-learning models, taxonomies, confidence estimates and data products.

Although these brokers provide valuable and complementary information, comparing and combining their classifications remains challenging.

THOR addresses this problem by providing a unified framework that:

- retrieves classifications from multiple brokers;
- reconciles heterogeneous taxonomies;
- computes a consensus classification;
- ranks candidates according to configurable scientific priorities.

---

## Features

- Multi-broker architecture
- Taxonomy reconciliation
- Consensus classification
- Candidate ranking
- Modular and extensible design
- Python interface

---

## Installation

```bash
pip install git+https://github.com/FabioRagosta/THOR.git
```

---

## Quick example

```python
from thor.hunter import Hunter

hunter = Hunter()

results = hunter.search(
    target="SN"
)

ranking = hunter.rank(results)

print(ranking.head())
```

---

## Workflow

```
Community Brokers
(Fink, ALeRCE, Lasair)
          │
          ▼
Taxonomy reconciliation
          │
          ▼
Consensus classification
          │
          ▼
Candidate ranking
          │
          ▼
Prioritised candidate list
```

---

## Documentation

The complete documentation includes:

- Installation guide
- Quick start tutorial
- User guide
- Worked examples
- API reference

---

## Citation

If THOR contributes to your research, please cite both the software and the accompanying publication.

Citation information is available through GitHub using the **"Cite this repository"** option.

---

## Licence

THOR is distributed under the MIT License.
