import React from "react";
import {cancelSearch, SearchResult, searchResults, SearchResultTrack, searchTracks} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import SearchResultList from "./SearchResultList";
import SearchInputField from "./SearchInputField";
import * as Collections from "typescript-collections";
import * as _ from "lodash";

interface SearchState {
    searchCompleted: boolean,
    searchRunning: boolean,
    hasErrors: boolean,
    runningBatches: Collections.Set<number>,
    maxBatchIndex: number,
}

interface State {
    searchString: string,
    searchResults: Collections.DefaultDictionary<string, Collections.Dictionary<number, SearchResultTrack>>,
    searchStates: Collections.DefaultDictionary<string, SearchState>,
}

const styles = (theme: Theme) => createStyles({
    root: {
        display: 'flex',
        flexFlow: 'column',
        height: '100%',
    },
});

interface Props extends WithStyles<typeof styles> {
}

class SearchControl extends React.Component<Props, State> {

    constructor(props: Props) {
        super(props);
        this.state = SearchControl.getInitialState();
    }

    static getInitialState(): State {
        const searchStates = new Collections.DefaultDictionary<string, SearchState>(
            () => {
                return {
                    searchCompleted: false,
                    searchRunning: false,
                    hasErrors: false,
                    runningBatches: new Collections.Set(),
                    maxBatchIndex: 0,
                }
            });
        return {
            searchString: '',
            searchResults: new Collections.DefaultDictionary(() => new Collections.Dictionary()),
            searchStates: searchStates,
        };
    }

    componentDidMount() {
        searchResults(this.setSearchResults);
    }

    setSearchResults = (searchResult: SearchResult) =>{
        const indexDict = this.state.searchResults.getValue(searchResult.search_string);
        searchResult.results.forEach(trackSearchResult => indexDict.setValue(trackSearchResult.index, trackSearchResult));

        const previousSearchState = this.getSearchState(searchResult.search_string);
        const searchCompleted = searchResult.search_completed || previousSearchState.searchCompleted;
        if (searchResult.batch_completed) {
            previousSearchState.runningBatches.remove(searchResult.batch_index);
        }
        this.state.searchStates.setValue(searchResult.search_string, {
            searchCompleted: searchCompleted,
            searchRunning: !previousSearchState.runningBatches.isEmpty(),
            hasErrors: searchResult.has_error || previousSearchState.hasErrors,
            runningBatches: previousSearchState.runningBatches,
            maxBatchIndex: previousSearchState.maxBatchIndex,
        });

        this.setState({
            searchString: this.state.searchString,
            searchStates: this.state.searchStates,
            searchResults: this.state.searchResults,
        });

    };

    onValueChange = (searchString: string) => {

        if (searchString === '') {
            cancelSearch();
        } else {
            const searchState = this.getSearchState(searchString);
            if (!searchState.searchRunning && !searchState.searchCompleted) {
                this.runSearch(searchString)
            }
        }
        this.setState({
            searchString: searchString,
            searchStates: this.state.searchStates,
            searchResults: this.state.searchResults,
        });
    };

    runSearch = (searchString: string) => {
        const searchState = this.getSearchState(searchString);
        searchState.runningBatches.add(searchState.maxBatchIndex);
        this.setSearchState(searchString, {
            searchCompleted: searchState.searchCompleted,
            searchRunning: true,
            hasErrors: searchState.hasErrors,
            runningBatches: searchState.runningBatches,
            maxBatchIndex: searchState.maxBatchIndex + 1,
        });

        const maxSearchResultIndex = this.getMaxSearchResultKey(searchString) + 1;
        const requestedSearchIndices = _.range(maxSearchResultIndex)
            .filter(index => !this.hasSearchResultKey(searchString, index))
            .concat(_.range(maxSearchResultIndex, maxSearchResultIndex + 10));

        searchTracks(searchString, searchState.maxBatchIndex, requestedSearchIndices);
    };

    getCurrentSearchResults = () => {
        return this.getSearchResultValues(this.state.searchString);
    };

    getSearchResults = (searchString: string) => {
        return this.state.searchResults.getValue(searchString);
    };

    getSearchResultValues = (searchString: string) => {
        return this.getSearchResults(searchString).values();
    };

    getMaxSearchResultKey = (searchString: string) => {
        return _.max(this.getSearchResults(searchString).keys()) || -1;
    };

    hasSearchResultKey = (searchString: string, index: number) => {
        return this.getSearchResults(searchString).containsKey(index);
    };

    getCurrentSearchResultTracksSorted = () => {
        return this.getCurrentSearchResults()
            .sort((a, b) => a.index - b.index);
    };

    getCurrentSearchState = () => {
        return this.getSearchState(this.state.searchString);
    };

    getSearchState = (searchString: string) => {
        return this.state.searchStates.getValue(searchString);
    };

    setSearchState = (searchString: string, searchState: SearchState) => {
        return this.state.searchStates.setValue(searchString, searchState);
    };

    render() {

        const {classes} = this.props;

        return (
            <div className={classes.root} >
                <SearchInputField
                    onValueChange={this.onValueChange}
                    indicateError={this.getCurrentSearchState().hasErrors}
                    indicateSearchRunning={this.getCurrentSearchState().searchRunning} />
                <SearchResultList
                    sortedSearchResultTracks={this.getCurrentSearchResultTracksSorted()} />
            </div>
        );
    }
}

export default withStyles(styles)(SearchControl);
