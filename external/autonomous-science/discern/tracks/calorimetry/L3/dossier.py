"""
Calorimetry L3 model-visible evidence builder.

The model-visible layer is deliberately condition-blind:
- identical public filenames in every world;
- identical table schema;
- no real/counterfactual flag;
- no benchmark-construction provenance;
- no exact intervention-law disclosure.

Construction provenance remains hidden in manifest/freeze/audits.

No model/API calls.
"""

from __future__ import annotations

from pathlib import Path

import json
import shutil

import l3_common as C


HERE = Path(__file__).resolve().parent

RUN = (
    HERE
    / "results"
    / "l3_run"
)

DATA = (
    RUN
    / "data"
)

PUBLIC_ROOT = (
    DATA
    / "public_inputs"
)

MANIFEST = (
    RUN
    / "manifest.json"
)


WORLDS = (
    "real",
    "cf_nano_cu",
    "cf_nano_cu_50nm",
)


SPECIMEN = {
    "real": {
        "material":
            "Cu",

        "crystal_structure":
            "fcc",

        "microstructure":
            "ordinary coarse-grained/polycrystalline Cu",
    },

    "cf_nano_cu": {
        "material":
            "Cu",

        "crystal_structure":
            "fcc",

        "mean_crystallite_size_nm":
            8.0,

        "microstructure":
            "approximately 8-nm nanocrystalline Cu",
    },

    "cf_nano_cu_50nm": {
        "material":
            "Cu",

        "crystal_structure":
            "fcc",

        "mean_crystallite_size_nm":
            50.0,

        "microstructure":
            "approximately 50-nm nanocrystalline Cu",
    },
}


TASK_NOTE = (
    "A follow-up copper specimen is compared with an ordinary bulk-Cu "
    "heat-capacity reference and with the same six phase-resolved "
    "Cu-heptane equilibrium scenarios. Determine whether the supplied "
    "evidence supports quantitative reuse of the bulk heat-capacity "
    "reference or a reproducible specimen-level departure. If a departure "
    "is supported, propose one bounded, falsifiable physical explanation "
    "and one discriminating confirmatory experiment."
)


ANALYSIS_GUIDANCE = (
    "Start from the supplied specimen-versus-bulk heat-capacity evidence. "
    "Quantify the magnitude and temperature coherence of any difference "
    "relative to the stated uncertainty. Then test whether the same signed "
    "thermal change coherently explains all six phase-resolved equilibrium "
    "outcomes. Distinguish a specimen-level heat-capacity result from proof "
    "of a unique microscopic mechanism. Plausible explanations and checks "
    "may involve calibration or normalization, composition or oxide/impurity "
    "state, unrecognized phase behavior, microstructure/grain-boundary "
    "structure, density/free volume, and thermal-expansion effects. A strong "
    "next experiment should discriminate among live alternatives rather than "
    "merely repeat the same inference."
)


HEAT_CAPACITY_COLUMNS = {
    "measurement_id":
        "row identifier for the supplied specimen evidence series",

    "temperature_k":
        "temperature",

    "bulk_reference_cp_j_mol_k":
        "carried-forward ordinary bulk-Cu molar heat-capacity reference",

    "specimen_cp_j_mol_k":
        "follow-up specimen molar heat-capacity evidence",

    "cp_uncertainty_j_mol_k":
        "uncertainty associated with the supplied specimen-versus-reference comparison",

    "bulk_reference_source_id":
        "source identifier for the carried-forward bulk heat-capacity reference",
}


EQUILIBRIUM_COLUMN_NOTES = {
    "scenario_id":
        "scenario identifier",

    "regime":
        "phase-resolved equilibrium regime",

    "bulk_reference_temperature_k":
        "equilibrium temperature predicted using the bulk-Cu reference",

    "specimen_temperature_k":
        "equilibrium temperature using the follow-up specimen heat capacity",

    "bulk_reference_liquid_fraction":
        "heptane liquid fraction under the bulk-Cu reference",

    "specimen_liquid_fraction":
        "heptane liquid fraction under the follow-up specimen heat capacity",

    "partial_melt_note":
        (
            "in partial-melt scenarios the equilibrium temperature remains "
            "at the heptane transition temperature and the liquid fraction "
            "carries the response"
        ),
}


def build():

    manifest = json.loads(
        MANIFEST.read_text()
    )

    if [
        row[
            "world"
        ]
        for row in manifest
    ] != list(
        WORLDS
    ):

        raise RuntimeError(
            "unexpected active world roster"
        )


    if DATA.exists():

        shutil.rmtree(
            DATA
        )

    PUBLIC_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )


    for row in manifest:

        world = row[
            "world"
        ]

        world_dir = (
            PUBLIC_ROOT
            / world
        )

        world_dir.mkdir(
            parents=True,
            exist_ok=True,
        )


        csv_path = (
            world_dir
            / "evidence.csv"
        )

        dossier_path = (
            world_dir
            / "dossier.json"
        )


        cp = C.cp_comparison_panel(
            world
        )

        eq = C.equilibrium_panel(
            world
        )


        cp.to_csv(
            csv_path,
            index=False,
        )


        dossier = {
            "task_note":
                TASK_NOTE,

            "specimen":
                SPECIMEN[
                    world
                ],

            "source": {
                "bulk_reference":
                    "carried-forward final Calorimetry L2 Cu Cp(T) reference",

                "followup_heat_capacity_file":
                    "evidence.csv",

                "downstream_analysis":
                    (
                        "same phase-resolved adiabatic Cu-heptane "
                        "equilibrium computation used for the carried-forward reference"
                    ),

                "heptane_thermodynamics":
                    "unchanged from the carried-forward reference analysis",
            },

            "heat_capacity_columns":
                HEAT_CAPACITY_COLUMNS,

            "downstream_equilibrium_panel":
                eq.to_dict(
                    orient="records"
                ),

            "equilibrium_column_notes":
                EQUILIBRIUM_COLUMN_NOTES,

            "analysis_guidance":
                ANALYSIS_GUIDANCE,
        }


        dossier_path.write_text(
            json.dumps(
                dossier,
                indent=2,
            )
            + "\n"
        )


        # Manifest remains hidden from the benchmarked agent.
        # Only the model-visible file locations change.
        row[
            "twas_csv"
        ] = str(
            csv_path.resolve()
        )

        row[
            "dossier"
        ] = str(
            dossier_path.resolve()
        )


    MANIFEST.write_text(
        json.dumps(
            manifest,
            indent=2,
        )
        + "\n"
    )


    print(
        "[dossier] built condition-blind public evidence "
        "for real / 8-nm / 50-nm worlds"
    )


if __name__ == "__main__":

    build()
