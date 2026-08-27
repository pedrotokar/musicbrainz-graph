import type { GraphEdge, GraphNode, GenericAPIResponse, NodeContext, EdgeContext } from "$lib/types";
import { GraphInteraction } from './abstractInteraction';
import { getArtistAdjacentNodes } from '$lib/fetcher/api-fetcher';

export class ExpandInteraction extends GraphInteraction {
    //Singleton logic
    static #instances: Map<string, WeakRef<ExpandInteraction>> = new Map();
    static #registry = new FinalizationRegistry((key: string) => {
        ExpandInteraction.#instances.delete(key);
        console.log(`GC destructed an interaction. Key '${key}' removed from ExpandInteraction singleton registry`);
    });

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
            throw new Error("Expand interaction API response did not include the source node.")
        }
    }

    static async create(originNodeId: string){
        //Singleton logic
        if (this.#instances.has(originNodeId)) {
            const ref = this.#instances.get(originNodeId);
            if(ref !== undefined){
                const previousInstance = ref.deref(); // Tries to get the object from the weak ref. If it still exists then its returned
                if (previousInstance !== undefined) {
                    console.log(`Factory: returning existing instance for ExpandInteraction with artist id '${originNodeId}'`);
                    return previousInstance;
                }
            }
        }

        const graphData = await getArtistAdjacentNodes(originNodeId);
        const newInstance = new ExpandInteraction(graphData, originNodeId);
        
        this.#instances.set(originNodeId, new WeakRef(newInstance));
        this.#registry.register(newInstance, originNodeId); //This is used to notify the instance has been deleted and thus delete the key
        return newInstance
    }

    getShowText() {
        return this.originNodeName;
    }

    getNodeContext(node: GraphNode): NodeContext {
        if (node.id === this.originNodeId) {
            return { 
                isOrigin: true, 
                isRelated: false 
            };
        }
        
        //TODO: handle multi edge
        const edge = this.interactionAPIResponse["edges"].find(edge => 
            (edge.source === this.originNodeId && edge.target === node.id) ||
            (edge.target === this.originNodeId && edge.source === node.id)
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

    getEdgeContext(edge: GraphEdge): EdgeContext {
        if (edge.source == this.originNodeId) {
            return "forward"
        } else if (edge.target == this.originNodeId) {
            return "backward"
        }
    }

    shouldAlwaysShowNode(node: GraphNode): boolean {
        return node.id == this.originNodeId
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    shouldAlwaysShowEdge(edge: GraphEdge): boolean {
        return false;
    }

}
