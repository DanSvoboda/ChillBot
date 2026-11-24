# ChillBot — AI chatbot o chilli papričkách

Celý projekt je v notebooku [`ChillBot.ipynb`](ChillBot.ipynb). Notebook se dá spustit
odshora dolů (*Run All*) a postupně projde všechny čtyři části:

| Část | Komponenta | Co dělá |
| --- | --- | --- |
| **A** | Model predikce výnosu | Z dat FAOSTAT předpovídá, zda výnos paprik v dané zemi **vzroste** oproti minulému roku. |
| **B** | Klasifikátor odrůd | Doladěný ResNet18, který z fotografie rozpozná **13 odrůd chilli**. |
| **C** | Nástroje pro LLM | Oba modely jako funkce `predict_yield_rise` a `classify_plant_type`, které LLM volá přes function calling. |
| **D** | Chatbot | LLM, který volá nástroje z části C a odpovídá s pomocí **RAG** nad PDF znalostní bází (ChromaDB). |

## Spuštění

Python 3.11+, z kořene repozitáře:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Pak otevřete `ChillBot.ipynb` a spusťte všechny buňky. Notebook čte soubory
relativně ke kořeni projektu, takže kernel musí běžet v kořeni repozitáře.

Pro část D vyplňte v buňce **👉 Vyzkoušejte sami** proměnnou `API_KEY` (endpoint
`litellm.vse.cz`, model `qwen3.6-35b`). Bez klíče se volání LLM přeskočí a zbytek
notebooku doběhne. Otázku vyberete přes `QUESTION = QUESTIONS["..."]`, nebo
`RUN_ALL = True` projede všechny testovací otázky.

## Obsah notebooku

### A — Predikce růstu výnosu

- **Data:** FAOSTAT 1961–2024 — čerstvé a sušené papriky, změna teploty a ceny výrobců.
- **Příprava:** vyřazení zaniklých států a duplicitní Číny, pivot `production` / `area_harvested` / `yield`, dopočet chybějícího výnosu, připojení klimatu, ceny a hodnot z předchozích let. Výstupem je `papriky-yield.csv` s cílem `yield_rise`; tím zůstává oddělený od staršího produkčního datasetu.
- **Trénování:** Dummy, logistická regrese, Random Forest a SVC přes `GridSearchCV`. Validace na pěti časově uspořádaných blocích, test tvoří roky 2020+. Model se vybírá podle CV ROC AUC.
- Nejlepší pipeline (předzpracování + model) se uloží do `models/yield_clf.pkl`.

### B — Klasifikace odrůd z fotografie

- **Data:** fotky 13 odrůd ve `data/training/varieties/{train,valid,test}/<odrůda>/`.
- **Model:** ResNet18 předtrénovaný na ImageNetu s novou hlavou pro 13 tříd, Adam `lr=1e-4`, 10 epoch.
- Trénování je vypnuté (`TRAIN = False`); notebook načte checkpoint `models/varieties/checkpoint.pt`, a pokud chybí, stáhne ho z Hugging Face (`DanSvobodaVSE/chillbot-varieties`). Vyhodnocuje se accuracy na testovací množině.

### C — Nástroje pro LLM

- `predict_yield_rise(...)`: vstupy popisuje pydantic třída `YieldInput`; všechna pole jsou nepovinná, chybějící hodnoty doplní imputer v pipeline.
- `classify_plant_type(image_path)`: vrátí 3 nejpravděpodobnější odrůdy s pravděpodobnostmi.

### D — Chatbot

- **RAG:** `data/knowledge/papriky.pdf` se rozdělí na chunky (1000 znaků, překryv 200) a uloží do ChromaDB v `data/vector_store/`. K dotazu se přidá 5 nejpodobnějších chunků.
- **Function calling:** LLM dostane popis nástrojů (`TOOLS`), aplikace požadovaná volání spustí lokálně a výsledek vrátí LLM (max. 5 kol).

## Důležité soubory

```text
ChillBot.ipynb                      celý projekt
data/
  training/production/              FAOSTAT CSV + papriky-yield.csv
  training/varieties/               fotografie odrůd (train / valid / test)
  knowledge/papriky.pdf             znalostní báze pro RAG
  vector_store/                     ChromaDB index (sestaví se sám, když je prázdný)
models/
  yield_clf.pkl                      model z části A
  varieties/checkpoint.pt           model z části B
pyproject.toml                      závislosti
```

Ostatní složky (`web/`, `tools/`, `scripts/`, `tests/`, Docker soubory) jsou
původní verze kódu jako Flask aplikace. Notebook z nich vychází (buňky jsou
označené `adapted from: ...`), ale ke spuštění je nepotřebuje.
