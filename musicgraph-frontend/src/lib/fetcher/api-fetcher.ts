import type { GenericAPIResponse } from '$lib/types';
export const URL_API = "http://127.0.0.1:8000";

export async function getArtistAdjacentNodes(artistId: string) {
    const response = await fetch(`${URL_API}/artist/${artistId}/adjacent`);
    const rawGraphData = await response.json() as GenericAPIResponse;
    return rawGraphData;
}
//    return normalizeGraph(rawGraphData);

// function normalizeGraph(rawGraphData: any) {
//     const nodeMap = new Map(rawGraphData["nodes"].map(n => [n.id, n]));

//     for(const node of rawGraphData["nodes"]){
//         nodeMap.set(node["id"], node);
//     }

//     for(const edge of rawGraphData["edges"]){
//         const sourceNode = nodeMap.get(edge["source"]);
//         const targetNode = nodeMap.get(edge["target"]);
//         if (!sourceNode || !targetNode){
//             console.warn(`API returned edge from ${edge["source"]} to ${edge["target"]} but one of them weren't in returned nodes (${sourceNode} | ${targetNode})`);
//             continue;
//         }
//         edge["source"] = nodeMap.get(edge["source"]);
//         edge["target"] = nodeMap.get(edge["target"]);
//     }

//     return rawGraphData;
// }
