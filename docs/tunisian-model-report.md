# Tunisian Dish Classifier — training report

Trained 2026-08-31: MobileNetV3-Small (ImageNet init) fine-tuned on 9280 training / 2381 validation samples built from three public CC-BY-4.0 Roboflow datasets (pfemrds/detection-tunisian-food-2025 v5, mariems/tunisian-food-seg v3, working-llaze/dataset-tn-annotated-exemples-2 v1). 0 cross-dataset duplicate images removed by hash.

## Validation results (best epoch)

| Metric | Value |
|---|---|
| Top-1 accuracy | **86.7%** |
| Top-3 accuracy | **96.0%** |
| Classes | 19 |

## Per-class (top-1 hits / val samples)

| Class | Top-1 |
|---|---|
| assida_zgougou | 68/72 |
| baklava | 174/207 |
| bambalouni | 96/109 |
| brik | 146/185 |
| chakchouka | 18/36 |
| chorba | 64/70 |
| couscous | 93/117 |
| fricasse | 171/179 |
| harissa | 8/30 |
| kafteji | 47/70 |
| kamounia | 52/64 |
| lablabi | 153/162 |
| makroudh | 226/253 |
| makrouna | 75/81 |
| merguez | 289/303 |
| mloukhiya | 133/139 |
| ojja | 59/80 |
| salade_mechouia | 105/118 |
| tajine_tunisien | 87/106 |

## Notes
- Samples are bbox crops (15% pad) plus each image labeled by its largest box;
  validation uses the datasets' own valid/test splits, deduplicated across datasets.
- Excluded classes: ingredient labels (fish/chicken/egg/lamb/thon/vegetables),
  'coktail hlou' (drink), 'Kskrout kafteji' (sandwich variant).
- Student-collected datasets: expect label noise; treat numbers as demo-grade.
