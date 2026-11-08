import type { GraphEdge, RelationshipRegistry } from "$lib/types"

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
];

export const RELATIONSHIP_PRIORITY_ORDER: string[] = [
    "HAS_MUSICAL_CONNECTION_TO",
    "COLLABORATED_WITH",
    "COVERED",
    "SAMPLED",
    "HAS_PERSONAL_CONNECTION_TO",
    "PRODUCED",
    "DEFAULT",
];

export const relationshipData: RelationshipRegistry = {
    "HAS_PERSONAL_CONNECTION_TO": {
        "bidirectional": true,
        "displayName": "Tem relações pessoais com o artista selecionado",
        "color": colorScheme[1],
        "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
            const rawSubtypes = (edge.parameters as Record<string, unknown>).subtypes;
            const subtypes = Array.isArray(rawSubtypes) ? rawSubtypes.join(", ") : (rawSubtypes || "");
            return `<strong>${sourceName}</strong> e <strong>${targetName}</strong> possuem a seguinte conexão pessoal: ${subtypes}<br/>`;
        }
    },
    "HAS_MUSICAL_CONNECTION_TO": {
        "bidirectional": true,
        "displayName": "Tem relações musicais com o artista selecionado",
        "color": colorScheme[3],
        "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
            const rawSubtypes = (edge.parameters as Record<string, unknown>).subtypes;
            const subtypes = Array.isArray(rawSubtypes) ? rawSubtypes.join(", ") : (rawSubtypes || "");
            return `<strong>${sourceName}</strong> e <strong>${targetName}</strong> possuem a seguinte conexão musical: ${subtypes}<br/>`;
        }
    },
    "COLLABORATED_WITH": {
        "bidirectional": true,
        "displayName": "Fez lançamentos em colaboração com o artista selecionado",
        "color": colorScheme[5],
        "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
            const recordings = (edge.parameters as Record<string, unknown>).collaboration_recordings as [string, string][] | undefined;
            let html = `<strong>${sourceName}</strong> colaborou com <strong>${targetName}</strong>`;
            if (recordings && recordings.length > 0) {
                html += ` nas seguintes gravações:<ul style="margin: 4px 0 8px 16px; padding: 0;">`;
                for (const [id, title] of recordings) {
                    html += `<li><a href="https://musicbrainz.org/recording/${id}" target="_blank">${title}</a></li>`;
                }
                html += `</ul>`;
            } else {
                html += `.<br/>`;
            }
            return html;
        }
    },
    "COVERED": {
        "bidirectional": false,
        "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
            if (edge.parameters.is_tribute_band) {
                return `<strong>${sourceName}</strong> é uma banda tributo de <strong>${targetName}</strong>.<br/>`;
            }
            return `<strong>${sourceName}</strong> fez cover de músicas de <strong>${targetName}</strong>.<br/>`;
        },
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
        "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
            const recordings = (edge.parameters as Record<string, unknown>).produced_recordings as [string, string, string[]][] | undefined;
            let html = `<strong>${sourceName}</strong> produziu as seguintes obras de <strong>${targetName}</strong>:`;
            if (recordings && recordings.length > 0) {
                html += `<ul style="margin: 4px 0 8px 16px; padding: 0;">`;
                for (const [id, title, labels] of recordings) {
                    const type = labels.includes("Release") ? "release" : "recording";
                    html += `<li><a href="https://musicbrainz.org/${type}/${id}" target="_blank">${title}</a></li>`;
                }
                html += `</ul>`;
            } else {
                html += `.<br/>`;
            }
            return html;
        },
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
        "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
            return `<strong>${sourceName}</strong> fez um sample de uma música de <strong>${targetName}</strong>.<br/>`;
        },
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
