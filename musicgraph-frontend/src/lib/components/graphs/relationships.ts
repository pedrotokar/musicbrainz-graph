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
            const subtypes = edge.parameters.subtypes || [];
            return `<strong>${sourceName}</strong> e <strong>${targetName}</strong> possuem a seguinte conexão pessoal: ${subtypes.join(", ")}<br/>`;
        }
    },
    "HAS_MUSICAL_CONNECTION_TO": {
        "bidirectional": true,
        "displayName": "Tem relações musicais com o artista selecionado",
        "color": colorScheme[3],
        "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
            const subtypes = edge.parameters.subtypes || [];
            return `<strong>${sourceName}</strong> e <strong>${targetName}</strong> possuem a seguinte conexão musical: ${subtypes.join(", ")}<br/>`;
        }
    },
    "COLLABORATED_WITH": {
        "bidirectional": true,
        "displayName": "Fez lançamentos em colaboração com o artista selecionado",
        "color": colorScheme[5],
        "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
            const recordings = edge.parameters.collaboration_recordings;
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
        "forward": {
            "displayName": "Teve uma música regravada pelo artista selecionado",
            "color": colorScheme[6],
            "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
                if (edge.parameters.is_tribute_band) {
                    return `<strong>${targetName}</strong> é uma banda tributo de <strong>${sourceName}</strong>.<br/>`;
                }
                return `<strong>${targetName}</strong> fez cover de músicas de <strong>${sourceName}</strong>.<br/>`;
            }
        },
        "backward": {
            "displayName": "Regravou uma música do artista selecionado",
            "color": colorScheme[7],
            "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
                if (edge.parameters.is_tribute_band) {
                    return `<strong>${sourceName}</strong> é uma banda tributo de <strong>${targetName}</strong>.<br/>`;
                }
                return `<strong>${sourceName}</strong> fez cover de músicas de <strong>${targetName}</strong>.<br/>`;
            }
        }
    },
    "PRODUCED": {
        "bidirectional": false,
        "forward": {
            "displayName": "Teve uma música produzida pelo artista selecionado",
            "color": colorScheme[8],
            "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
                const recordings = edge.parameters.produced_recordings;
                let html = `<strong>${targetName}</strong> produziu as seguintes obras de <strong>${sourceName}</strong>:`;
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
            }
        },
        "backward": {
            "displayName": "Produziu uma música do artista selecionado",
            "color": colorScheme[9],
            "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
                const recordings = edge.parameters.produced_recordings;
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
            }
        }
    },
    "SAMPLED": {
        "bidirectional": false,
        "forward": {
            "displayName": "Teve uma música sampleada pelo artista selecionado",
            "color": colorScheme[10],
            "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
                return `<strong>${targetName}</strong> fez um sample de uma música de <strong>${sourceName}</strong>.<br/>`;
            }
        },
        "backward": {
            "displayName": "Fez um sample uma música do artista selecionado",
            "color": colorScheme[11],
            "tooltipGenerator": (edge: GraphEdge, sourceName: string, targetName: string) => {
                return `<strong>${sourceName}</strong> fez um sample de uma música de <strong>${targetName}</strong>.<br/>`;
            }
        }
    },
    "DEFAULT": {
        "bidirectional": true,
        "color": "#000000",
        "displayName": "erro!"
    }
    // "Sample (fez/foi feito)": {},
}
