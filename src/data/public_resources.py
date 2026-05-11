"""Registry of publicly downloadable resources.

Only items that:
    (a) have an explicit public URL, AND
    (b) can be redistributed for non-commercial research,
should live here. Clinical corpora (DementiaBank, ADReSS, TAUKADIAL, SpeechDx)
require institutional agreements and are documented in docs/DATA_ACCESS.md
instead.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PublicResource:
    name: str
    url: str
    description: str
    filename: str
    license_note: str


PUBLIC_RESOURCES: list[PublicResource] = [
    PublicResource(
        name="Alzheimer's Association — La comunicación (ES)",
        url="https://www.alz.org/getmedia/4a80e11b-f1df-4972-9323-b97c4359a89d/alzheimers-dementia-communication-spanish-ts.pdf",
        description="Guía breve sobre cómo comunicarse con una persona con Alzheimer.",
        filename="alz_association_comunicacion_ES.pdf",
        license_note="© Alzheimer's Association — redistribución informativa.",
    ),
    PublicResource(
        name="CEAFA — Cómo comunicarse con una persona con Alzheimer",
        url="https://www.ceafa.es/files/2020/01/como-comunicarse-con-una-persona-con-alzheimer.pdf",
        description="Guía publicada por la Confederación Española de Alzheimer.",
        filename="ceafa_como_comunicarse.pdf",
        license_note="© CEAFA — material divulgativo público.",
    ),
    PublicResource(
        name="MultiConAD paper (arXiv 2502.19208)",
        url="https://arxiv.org/pdf/2502.19208v1",
        description="Paper que describe un corpus multilingüe para detección de AD.",
        filename="multiconad_2025.pdf",
        license_note="arXiv preprint — distribución académica.",
    ),
]
