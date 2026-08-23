//Type Imports
import type { GenericAPIResponse, InteractionOwnedElements } from "$lib/types"

//Module Imports
import { getArtistAdjacentNodes } from '$lib/fetcher/api-fetcher';

export abstract class GraphInteraction {
    constructor(
        protected id: string,
        protected interactionAPIResponse: GenericAPIResponse
    ) { }

    getId(): string {
        return this.id;
    }

    getOwnedElements(): GenericAPIResponse {
        return this.interactionAPIResponse
    };
    
    getOwnedElementIds(): InteractionOwnedElements {
        const owned: InteractionOwnedElements = {
            "nodes": [],
            "edges": [],
        }
        if(this.interactionAPIResponse){
            for(const node of this.interactionAPIResponse["nodes"]){
                owned["nodes"].push(node.id);
            }
            for(const edge of this.interactionAPIResponse["edges"]){
                owned["edges"].push(edge.source + "->" + edge.target + "|" + edge.type)
            }
        }
        return owned
    }
}

export class ExpandInteraction extends GraphInteraction {
    private constructor(
        interactionAPIResponse: GenericAPIResponse, 
        private originNodeId: string
    ){
        super(crypto.randomUUID(), interactionAPIResponse);
    }

    static async create(originNodeId: string){
        const graphData = await getArtistAdjacentNodes(originNodeId);
        return new ExpandInteraction(graphData, originNodeId);
    }
}
