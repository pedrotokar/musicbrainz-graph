import type { GenericAPIResponse, InteractionOwnedElements, NodeContext } from "$lib/types";
import { getArtistAdjacentNodes } from '$lib/fetcher/api-fetcher';

export abstract class GraphInteraction {
    constructor(
        protected id: string,
        protected interactionAPIResponse: GenericAPIResponse
    ) { }

    getId(): string {
        return this.id;
    }

    abstract getShowText(): string;
    abstract getNodeContext(nodeId: string): NodeContext;

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
    private originNodeName: string;

    private constructor(
        interactionAPIResponse: GenericAPIResponse, 
        private originNodeId: string
    ){
        super(crypto.randomUUID(), interactionAPIResponse);
        const originArtistNode = interactionAPIResponse["nodes"].find((node) => node.id === originNodeId);
        if (originArtistNode){
            this.originNodeName = originArtistNode.display_name;
        } else {
            this.originNodeName = "erro! investigar"
            //TODO: DISCOVER A BETTER WAY TO HANDLE THAT
        }
    }

    static async create(originNodeId: string){
        const graphData = await getArtistAdjacentNodes(originNodeId);
        return new ExpandInteraction(graphData, originNodeId);
    }

    getShowText() {
        return this.originNodeName;
    }

    getNodeContext(nodeId: string): NodeContext {
        if (nodeId === this.originNodeId) {
            return { 
                isOrigin: true, 
                isRelated: false 
            };
        }
        
        //TODO: handle multi edge
        const edge = this.interactionAPIResponse["edges"].find(edge => 
            (edge.source === this.originNodeId && edge.target === nodeId) ||
            (edge.target === this.originNodeId && edge.source === nodeId)
        );

        if (edge) {
            return {
                isOrigin: false,
                isRelated: true,
                relationshipType: edge.type,
                relationshipDirection: edge.source === this.originNodeId ? "forward" : "backward",
                relationshipMetadata: edge.parameters
            };
        }

        return { 
            isOrigin: false, 
            isRelated: false 
        };
    }
}
