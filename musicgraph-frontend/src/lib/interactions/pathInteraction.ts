import type { GraphEdge, GraphNode, GenericAPIResponse, NodeContext, EdgeContext } from "$lib/types";
import { GraphInteraction } from './abstractInteraction';
import { getArtistShortestPath } from '$lib/fetcher/api-fetcher';

export class PathInteraction extends GraphInteraction {

    static #instances: Map<string, WeakRef<PathInteraction>> = new Map();
    static #registry = new FinalizationRegistry((key: string) => {
        PathInteraction.#instances.delete(key);
        console.log(`GC destructed an interaction. Key '${key}' removed from ExpandInteraction singleton registry`);
    });

    private sourceNodeName: string;
    private targetNodeName: string;
    
    // Path linked list head
    // TODO: think if this is the best solution. I think the ideal would be
    // offsetting this logic to the backend somehow and getting everything 
    // treated nicely here but maybe that will be hard, idk
    private sourceNode: any;


    private constructor(
        interactionAPIResponse: GenericAPIResponse, 
        private sourceNodeId: string,
        private targetNodeId: string
    ){
        super(crypto.randomUUID(), interactionAPIResponse);
        const sourceArtistNode = interactionAPIResponse["nodes"].find((node) => node.id === sourceNodeId);
        const targetArtistNode = interactionAPIResponse["nodes"].find((node) => node.id === targetNodeId);
        if (sourceArtistNode && targetArtistNode){
            this.sourceNodeName = sourceArtistNode.display_name;
            this.targetNodeName = targetArtistNode.display_name;
            
            // Constructing the linked list
            // TODO: Review this entire logic
            this.sourceNode = sourceArtistNode;
            let currentNode;
            let nextNode;
            let nextRelationship = interactionAPIResponse["edges"].find((edge) => edge.target === sourceArtistNode.id || edge.source === sourceArtistNode.id) //Supposed to be only one
            if (nextRelationship?.target === this.sourceNode.id) {
                currentNode = interactionAPIResponse["nodes"].find((node) => node.id === nextRelationship?.source);
            } else {
                currentNode = interactionAPIResponse["nodes"].find((node) => node.id === nextRelationship?.target);
            }
            this.sourceNode.nextRelationship = nextRelationship;
            this.sourceNode.nextNode = currentNode;
            currentNode.previousRelationship = nextRelationship;
            currentNode.previousNode = this.sourceNode;


            while(currentNode?.id != targetArtistNode.id){
                let nextRelationship = interactionAPIResponse["edges"].find((edge) => (edge.target === currentNode.id && edge.source !== currentNode.previousNode.id) || (edge.source === currentNode.id && edge.target !== currentNode.previousNode.id)) //Supposed to be only one
                if (nextRelationship?.target === currentNode.id) {
                    nextNode = interactionAPIResponse["nodes"].find((node) => node.id === nextRelationship?.source);
                } else {
                    nextNode = interactionAPIResponse["nodes"].find((node) => node.id === nextRelationship?.target);
                }
                currentNode.nextRelationship = nextRelationship;
                currentNode.nextNode = nextNode;
                nextNode.previousRelationship = nextRelationship;
                nextNode.previousNode = currentNode;
                currentNode = nextNode;

            }

        } else {
            throw new Error("Path interaction API response did not include the source or target node.")
        }
    }

    static async create(sourceNodeId: string, targetNodeId: string){
        let key;
        if(sourceNodeId < targetNodeId){
            key = sourceNodeId + "<>" + targetNodeId;
        } else {
            key = targetNodeId + "<>" + sourceNodeId;
        }
        //Singleton logic
        if (this.#instances.has(key)) {
            const ref = this.#instances.get(key);
            if(ref !== undefined){
                const previousInstance = ref.deref(); // Tries to get the object from the weak ref. If it still exists then its returned
                if (previousInstance !== undefined) {
                    console.log(`Factory: returning existing instance for PathInteraction with source artist id '${sourceNodeId}' and target artist id '${targetNodeId}'`);
                    return previousInstance;
                }
            }
        }

        const graphData = await getArtistShortestPath(sourceNodeId, targetNodeId);
        const newInstance = new PathInteraction(graphData, sourceNodeId, targetNodeId);
        
        this.#instances.set(key, new WeakRef(newInstance));
        this.#registry.register(newInstance, key); //This is used to notify the instance has been deleted and thus delete the key
        return newInstance
    }

    getShowText(): string {
        return this.sourceNodeName + " -> " + this.targetNodeName;
    }

    getFocusNodeId(): string | undefined {
        return this.targetNodeId;
    }

    //TODO: evaluate if these solutions based on the linked list are the best options
    getNodeContext(node: GraphNode): NodeContext{
        if (node.id === this.sourceNodeId) {
            return { 
                isOrigin: true, 
                isRelated: false,
                edges: []
            };
        }
        
        let currentNode = this.sourceNode;
        while(currentNode.id != node.id){
            currentNode = currentNode.nextNode;
            if(!currentNode){
                return {
                    isOrigin: false,
                    isRelated: false,
                    edges: []
                }
            }
        }

        return { 
            isOrigin: false, 
            isRelated: true,
            edges: [currentNode.previousRelationship]
        };
    }

    getEdgeContext(edge: GraphEdge): EdgeContext{
        return "forward"
    }

    shouldAlwaysShowNode(node: GraphNode): boolean {
        return this.interactionAPIResponse["nodes"].some((pathNode) => pathNode.id == node.id);
    }

    //TODO: fix this so it actually dont hide the path edge
    shouldAlwaysShowEdge(edge: GraphEdge): boolean {
//        return this.interactionAPIResponse["edges"].some((pathEdge) => pathEdge.id == edge.id);
        return false
    }

}
