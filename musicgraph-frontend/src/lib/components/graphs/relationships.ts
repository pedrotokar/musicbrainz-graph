import type { RelationshipRegistry } from "$lib/types"

//Legendas
//Cores
//Tooltips

export const relationshipData: RelationshipRegistry = {
    "HAS_PERSONAL_CONNECTION_TO": {
        "bidirectional": true,
        "displayName": "Tem relações pessoais com o artista selecionado",
        "color": "yellow"
    },
    "HAS_MUSICAL_CONNECTION_TO": {
        "bidirectional": true,
        "displayName": "Tem relações musicais com o artista selecionado",
        "color": "blue"
    },
    "COLLABORATED_WITH": {
        "bidirectional": true,
        "displayName": "Fez lançamentos em colaboração com o artista selecionado",
        "color": "red"
    },
    "COVERED": {
        "bidirectional": false,
        "forward": {
            "displayName": "Teve uma música regravada pelo artista selecionado",
            "color": "green"
        },
        "backward": {
            "displayName": "Regravou uma música do artista selecionado",
            "color": "lightgreen"
        }
    },
    "PRODUCED": {
        "bidirectional": false,
        "forward": {
            "displayName": "Teve uma música produzida pelo artista selecionado",
            "color": "red"
        },
        "backward": {
            "displayName": "produziu uma música do artista selecionado",
            "color": "red"
        }
    },
    "DEFAULT": {
        "bidirectional": true,
        "color": "#000000",
        "displayName": "erro!"
    }
    // "Sample (fez/foi feito)": {},
}
