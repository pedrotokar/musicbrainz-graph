<script lang="ts">
	import type { SearchResult } from '$lib/types';

    import { performArtistSearch } from '$lib/fetcher/api-fetcher';

    interface Props { onArtistSelectFunction: (nodeId: string) => void; }
    let { onArtistSelectFunction }: Props = $props();

    // Variables controlling the search state
    let userInput = $state("");
    let searchResults: SearchResult[] = $state([]);
    let searchState = $state("IDLE");
    let selectedIndex = $state(-1);

    // Variables to help handling input debouncing
    // svelte-ignore non_reactive_update
    let debounceTimer: ReturnType<typeof setTimeout>;
    let requestController: AbortController = new AbortController();

    // Debug
    let requestsInterrompidos = $state(0)
    let typeEvents = $state(0)

    // ------------------ Search logic management functions ------------------
    function selectArtist(artist: SearchResult) {
        onArtistSelectFunction(artist.id);
        searchResults = [];
        selectedIndex = -1;
        searchState = "IDLE";
        userInput = "";
    }

    function performSearch(query: string){
        const cleanQuery = query.trim();
        if (cleanQuery.length < 3) {
            searchResults = [];
            searchState = "IDLE";
            selectedIndex = -1;
            return;
        }

        searchState = "SEARCHING";
        selectedIndex = -1;

        requestController.abort();
        requestController = new AbortController();
        console.log("Sending query to backend:", cleanQuery);

        performArtistSearch(cleanQuery, requestController)
	        .then((data) => {
				console.log(data);
				if (data.length > 0) {
					searchResults = data;
                    searchState = "SUCCESS"
				} else {
					searchResults = [];
                    searchState = "EMPTY"
				}
			})
			.catch((error) => {
                if (error.name === "AbortError") {
                    requestsInterrompidos += 1;
                    return
                }
				console.error("Unexpected error while searching for artists:", error);
				searchResults = [];
                searchState = "ERROR"
			});
    }

    // ------------------- User input processing functions -------------------
    // This function is used to implement the debouncing. It assures that the
    // input is used only when the debouncing ended
    function handleInput(){
        typeEvents += 1;
        searchState = "TYPING";
        selectedIndex = -1;

        requestController.abort(); //User started to type, so I cancel the request

        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            performSearch(userInput);
        }, 1000);
    }

    // This function handles the results navigation with the keyboard
    function handleKeydown(event: KeyboardEvent) {
        if (event.key === "ArrowDown") {
            if (searchResults.length > 0) {
                event.preventDefault();
                selectedIndex = (selectedIndex + 1) % searchResults.length;
            }
        } else if (event.key === "ArrowUp") {
            if (searchResults.length > 0) {
                event.preventDefault();
                selectedIndex = (selectedIndex - 1 + searchResults.length) % searchResults.length;
            }
        } else if (event.key === "Enter") {
            event.preventDefault();
            if (selectedIndex >= 0 && selectedIndex < searchResults.length) {
                selectArtist(searchResults[selectedIndex]);
            } else {
                clearTimeout(debounceTimer);
                performSearch(userInput);
            }
        } else if (event.key === "Escape") {
            searchResults = [];
            selectedIndex = -1;
            searchState = "IDLE";
            (event.currentTarget as HTMLElement)?.blur();
        }
    }
</script>

<input
    id="artistSearchInput"
    type="text"
    bind:value={userInput}
	oninput={handleInput}
    onkeydown={handleKeydown}
    required
    placeholder="Busque por um artista ou banda"
/>

<div id="artistSearchResults">
    <ul role="listbox">
        {#each searchResults as result, index (result.id)}
        <li 
            role="option"
            aria-selected={index === selectedIndex}
            class:selected={index === selectedIndex}
            onclick={() => selectArtist(result)}
            onmouseenter={() => { selectedIndex = index; }}
        >
            {result.name} ({result.id}) ({result.score})
        </li>
        {/each}
    </ul>
</div>

<h4> Debug </h4>
input do cara: {userInput} <br>
debounce timer: {debounceTimer} <br>
estado da pesquisa: {searchState} <br>
requests interrompidos: {requestsInterrompidos} <br>
eventos: {typeEvents} <br>
item selecionado: {selectedIndex}

<style>
    .selected {
        background-color: #e2e8f0;
    }
</style>
