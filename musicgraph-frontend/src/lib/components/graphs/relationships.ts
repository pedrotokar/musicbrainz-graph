import type { RelationshipRegistry } from "$lib/types"

//Legendas
//Cores
//Tooltips

const colorScheme = [
    "#a6cee3",
    "#1f78b4",
    "#b2df8a",
    "#33a02c",
    "#fb9a99",
    "#e31a1c",
    "#fdbf6f",
    "#ff7f00",
    "#cab2d6",
    "#6a3d9a",
    "#ffff99",
    "#b15928",
]

export const relationshipData: RelationshipRegistry = {
    "HAS_PERSONAL_CONNECTION_TO": {
        "bidirectional": true,
        "displayName": "Tem relações pessoais com o artista selecionado",
        "color": colorScheme[1]
    },
    "HAS_MUSICAL_CONNECTION_TO": {
        "bidirectional": true,
        "displayName": "Tem relações musicais com o artista selecionado",
        "color": colorScheme[3]
    },
    "COLLABORATED_WITH": {
        "bidirectional": true,
        "displayName": "Fez lançamentos em colaboração com o artista selecionado",
        "color": colorScheme[5]
    },
    "COVERED": {
        "bidirectional": false,
        "forward": {
            "displayName": "Teve uma música regravada pelo artista selecionado",
            "color": colorScheme[6]
        },
        "backward": {
            "displayName": "Regravou uma música do artista selecionado",
            "color": colorScheme[7]
        }
    },
    "PRODUCED": {
        "bidirectional": false,
        "forward": {
            "displayName": "Teve uma música produzida pelo artista selecionado",
            "color": colorScheme[8]
        },
        "backward": {
            "displayName": "Produziu uma música do artista selecionado",
            "color": colorScheme[9]
        }
    },
    "SAMPLED": {
        "bidirectional": false,
        "forward": {
            "displayName": "Teve uma música sampleada pelo artista selecionado",
            "color": colorScheme[10]
        },
        "backward": {
            "displayName": "Fez um sample uma música do artista selecionado",
            "color": colorScheme[11]
        }
    },
    "DEFAULT": {
        "bidirectional": true,
        "color": "#000000",
        "displayName": "erro!"
    }
    // "Sample (fez/foi feito)": {},
}
